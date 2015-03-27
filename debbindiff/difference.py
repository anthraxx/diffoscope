# -*- coding: utf-8 -*-
#
# debbindiff: highlight differences between two builds of Debian packages
#
# Copyright © 2014 Jérémy Bobbio <lunar@debian.org>
#
# debbindiff is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# debbindiff is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with debbindiff.  If not, see <http://www.gnu.org/licenses/>.

import os.path
from functools import partial
from tempfile import NamedTemporaryFile
import re
import subprocess
from debbindiff import logger, tool_required, RequiredToolNotFound


MAX_DIFF_BLOCK_LINES = 50


class DiffParser(object):
    RANGE_RE = re.compile(r'^@@\s+-(?P<start1>\d+)(,(?P<len1>\d+))?\s+\+(?P<start2>\d+)(,(?P<len2>\d+))?\s+@@$')

    def __init__(self, output):
        self._output = output
        self._action = self.read_headers
        self._diff = ''
        self._remaining_hunk_lines = None
        self._block_len = None
        self._direction = None

    def parse(self):
        while True:
            line = self._output.readline().decode('utf-8')
            if line == '': # EOF
                return self._diff
            self._action = self._action(line)

    def read_headers(self, line):
        found = DiffParser.RANGE_RE.match(line)
        if line.startswith('---'):
            return self.read_headers
        elif line.startswith('+++'):
            return self.read_headers
        elif not found:
            raise ValueError('Unable to parse diff headers: %s' % repr(line))
        self._diff += line
        if found.group('len1'):
            self._remaining_hunk_lines = int(found.group('len1'))
        else:
            self._remaining_hunk_lines = 1
        if found.group('len2'):
            self._remaining_hunk_lines += int(found.group('len2'))
        else:
            self._remaining_hunk_lines += 1
        self._direction = None
        return self.read_hunk

    def read_hunk(self, line):
        if line[0] == ' ':
            self._remaining_hunk_lines -= 2
        elif line[0] == '+':
            self._remaining_hunk_lines -= 1
        elif line[0] == '-':
            self._remaining_hunk_lines -= 1
        elif line[0] == '\\':
            pass
        elif self._remaining_hunk_lines == 0:
            return self.read_headers(line)
        else:
            raise ValueError('Unable to parse diff hunk: %s' % repr(line))
        self._diff += line
        if line[0] in ('-', '+') and line[0] == self._direction:
            self._block_len += 1
            if self._block_len >= MAX_DIFF_BLOCK_LINES:
                return self.skip_block
        else:
            self._block_len = 1
            self._direction = line[0]
        return self.read_hunk

    def skip_block(self, line):
        if not line.startswith(self._direction):
            self._diff += '%s[ %d lines removed ]\n' % (self._direction, self._block_len - MAX_DIFF_BLOCK_LINES)
            return self.read_hunk(line)
        self._block_len += 1
        self._remaining_hunk_lines -= 1
        if self._remaining_hunk_lines == 0:
            self._diff += '%s[ %d lines removed ]\n' % (self._direction, self._block_len - MAX_DIFF_BLOCK_LINES)
            return self.read_headers
        return self.skip_block


@tool_required('diff')
def diff(content1, content2):
    with NamedTemporaryFile('w') as tmp_file1:
        with NamedTemporaryFile('w') as tmp_file2:
            # fill temporary files
            tmp_file1.write(content1.encode('utf-8'))
            tmp_file2.write(content2.encode('utf-8'))
            # work-around unified diff limitation: if there's no newlines in both
            # don't make it a difference
            if content1[-1] != '\n' and content2[-1] != '\n':
                tmp_file1.write('\n')
                tmp_file2.write('\n')
            tmp_file1.flush()
            tmp_file2.flush()
            # run diff
            logger.debug('running diff')
            cmd = ['diff', '-au7', tmp_file1.name, tmp_file2.name]
            p = subprocess.Popen(cmd, shell=False,
                                 close_fds=True, stdin=None, stdout=subprocess.PIPE,
                                 stderr=subprocess.STDOUT)
            # parse ouptut
            logger.debug('parsing diff output')
            diff = DiffParser(p.stdout).parse()
            p.wait()
            if p.returncode not in (0, 1):
                raise subprocess.CalledProcessError(cmd, p.returncode, output=diff)
            return diff


class Difference(object):
    def __init__(self, content1, content2, path1, path2, source=None,
                 comment=None):
        self._comment = comment
        if content1 and type(content1) is not unicode:
            raise UnicodeError('content1 has not been decoded')
        if content2 and type(content2) is not unicode:
            raise UnicodeError('content2 has not been decoded')
        self._unified_diff = None
        if content1 is not None and content2 is not None:
            try:
                self._unified_diff = diff(content1, content2)
            except RequiredToolNotFound:
                self._comment = 'diff is not available!'
                if comment:
                    self._comment += '\n\n' + comment
        # allow to override declared file paths, useful when comparing
        # tempfiles
        if source:
            if type(source) is list:
                self._source1, self._source2 = source
            else:
                self._source1 = source
                self._source2 = source
        else:
            self._source1 = path1
            self._source2 = path2
        self._details = []

    @property
    def comment(self):
        return self._comment

    @comment.setter
    def comment(self, comment):
        self._comment = comment

    @property
    def source1(self):
        return self._source1

    @property
    def source2(self):
        return self._source2

    @property
    def unified_diff(self):
        return self._unified_diff

    @property
    def details(self):
        return self._details

    def add_details(self, differences):
        self._details.extend(differences)


def get_source(path1, path2):
    if os.path.basename(path1) == os.path.basename(path2):
        return os.path.basename(path1)
    return None
