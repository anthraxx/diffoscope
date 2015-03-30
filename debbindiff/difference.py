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

import os
import os.path
from functools import partial
from tempfile import NamedTemporaryFile
import re
import subprocess
from threading import Thread
from debbindiff import logger, tool_required, RequiredToolNotFound


MAX_DIFF_BLOCK_LINES = 50
MAX_DIFF_LINES = 10000


class DiffParser(object):
    RANGE_RE = re.compile(r'^@@\s+-(?P<start1>\d+)(,(?P<len1>\d+))?\s+\+(?P<start2>\d+)(,(?P<len2>\d+))?\s+@@$')

    def __init__(self, output):
        self._output = output
        self._action = self.read_headers
        self._diff = ''
        self._success = False
        self._line_count = 0
        self._remaining_hunk_lines = None
        self._block_len = None
        self._direction = None

    @property
    def diff(self):
        return self._diff

    @property
    def success(self):
        return self._success

    def parse(self):
        for line in iter(self._output.readline, b''):
            self._line_count += 1
            if self._line_count >= MAX_DIFF_LINES:
                self._diff += '\n[ Processing stopped after %d lines. ]' % self._line_count
                break
            self._action = self._action(line.decode('utf-8'))
        self._success = True
        self._output.close()

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




DIFF_CHUNK = 4096


def feed_content(f, content, add_ln):
    for offset in range(0, len(content), DIFF_CHUNK):
        f.write(content[offset:offset + DIFF_CHUNK].encode('utf-8'))
    if add_ln:
        f.write('\n')
    f.close()


@tool_required('diff')
def diff(content1, content2):
    pipe_r1, pipe_w1 = os.pipe()
    pipe_r2, pipe_w2 = os.pipe()
    # run diff
    logger.debug('running diff')
    cmd = ['diff', '-au7', '/dev/fd/%d' % pipe_r1, '/dev/fd/%d' % pipe_r2]
    def close_pipes():
        os.close(pipe_w1)
        os.close(pipe_w2)
    p = subprocess.Popen(cmd, shell=False, bufsize=1,
                         stdin=subprocess.PIPE,
                         stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT,
                         preexec_fn=close_pipes)
    os.close(pipe_r1)
    os.close(pipe_r2)
    p.stdin.close()
    output1 = os.fdopen(pipe_w1, 'w')
    output2 = os.fdopen(pipe_w2, 'w')
    parser = DiffParser(p.stdout)
    t_read = Thread(target=parser.parse)
    t_read.daemon = True
    t_read.start()
    # work-around unified diff limitation: if there's no newlines in both
    # don't make it a difference
    add_ln = content1[-1] != '\n' and content2[-1] != '\n'
    t_write1 = Thread(target=feed_content, args=(output1, content1, add_ln))
    t_write1.daemon = True
    t_write1.start()
    t_write2 = Thread(target=feed_content, args=(output2, content2, add_ln))
    t_write2.daemon = True
    t_write2.start()
    t_write1.join()
    t_write2.join()
    t_read.join()
    p.wait()
    if not parser.success and p.returncode not in (0, 1):
        raise subprocess.CalledProcessError(cmd, p.returncode, output=diff)
    if p.returncode == 0:
        return None
    return parser.diff


class Difference(object):
    def __init__(self, unified_diff, path1, path2, source=None, comment=None):
        self._comment = comment
        self._unified_diff = unified_diff
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

    @staticmethod
    def from_content(content1, content2, path1, path2, source=None,
                     comment=None):
        actual_comment = comment
        if content1 and type(content1) is not unicode:
            raise UnicodeError('content1 has not been decoded')
        if content2 and type(content2) is not unicode:
            raise UnicodeError('content2 has not been decoded')
        unified_diff = None
        try:
            unified_diff = diff(content1, content2)
        except RequiredToolNotFound:
            actual_comment = 'diff is not available!'
            if comment:
                actual_comment += '\n\n' + orig_comment
        if not unified_diff:
            return None
        return Difference(unified_diff, path1, path2, source, actual_comment)

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
