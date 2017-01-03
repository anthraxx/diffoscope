# -*- coding: utf-8 -*-
#
# diffoscope: in-depth comparison of files, archives, and directories
#
# Copyright © 2014-2015 Jérémy Bobbio <lunar@debian.org>
#
# diffoscope is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# diffoscope is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with diffoscope.  If not, see <https://www.gnu.org/licenses/>.

import signal
import hashlib
import logging
import subprocess

from .exc import RequiredToolNotFound
from .diff import diff, reverse_unified_diff
from .config import Config
from .profiling import profile

DIFF_CHUNK = 4096

logger = logging.getLogger(__name__)


class Difference(object):
    def __init__(self, unified_diff, path1, path2, source=None, comment=None, has_internal_linenos=False):
        self._comments = []
        if comment:
            if type(comment) is list:
                self._comments.extend(comment)
            else:
                self._comments.append(comment)
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
        # Ensure renderable types
        if not isinstance(self._source1, str):
            raise TypeError("path1/source[0] is not a string")
        if not isinstance(self._source2, str):
            raise TypeError("path2/source[1] is not a string")
        # Whether the unified_diff already contains line numbers inside itself
        self._has_internal_linenos = has_internal_linenos
        self._details = []

    def __repr__(self):
        return '<Difference %s -- %s %s>' % (self._source1, self._source2, self._details)

    @staticmethod
    def from_feeder(feeder1, feeder2, path1, path2, source=None, comment=None, **kwargs):
        try:
            unified_diff = diff(feeder1, feeder2)
            if not unified_diff:
                return None
            return Difference(unified_diff, path1, path2, source, comment, **kwargs)
        except RequiredToolNotFound:
            difference = Difference(None, path1, path2, source)
            difference.add_comment('diff is not available!')
            if comment:
                difference.add_comment(comment)
            return difference

    @staticmethod
    def from_text(content1, content2, *args, **kwargs):
        return Difference.from_feeder(make_feeder_from_text(content1),
                                      make_feeder_from_text(content2),
                                      *args, **kwargs)

    @staticmethod
    def from_raw_readers(file1, file2, *args, **kwargs):
        return Difference.from_feeder(make_feeder_from_raw_reader(file1),
                                      make_feeder_from_raw_reader(file2),
                                      *args, **kwargs)

    @staticmethod
    def from_text_readers(file1, file2, *args, **kwargs):
        return Difference.from_feeder(make_feeder_from_text_reader(file1),
                                      make_feeder_from_text_reader(file2),
                                      *args, **kwargs)

    @staticmethod
    def from_command(klass, path1, path2, *args, **kwargs):
        command_args = []
        if 'command_args' in kwargs:
            command_args = kwargs['command_args']
            del kwargs['command_args']
        command1 = None
        if path1 == '/dev/null':
            feeder1 = empty_file_feeder()
        else:
            command1 = klass(path1, *command_args)
            feeder1 = make_feeder_from_command(command1)
        command2 = None
        if path2 == '/dev/null':
            feeder2 = empty_file_feeder()
        else:
            command2 = klass(path2, *command_args)
            feeder2 = make_feeder_from_command(command2)
        if 'source' not in kwargs:
            source_cmd = command1 or command2
            kwargs['source'] = ' '.join(map(lambda x: '{}' if x == source_cmd.path else x, source_cmd.cmdline()))
        difference = Difference.from_feeder(feeder1, feeder2, path1, path2, *args, **kwargs)
        if not difference:
            return None
        if command1 and command1.stderr_content:
            difference.add_comment('stderr from `%s`:' % ' '.join(command1.cmdline()))
            difference.add_comment(command1.stderr_content)
        if command2 and command2.stderr_content:
            difference.add_comment('stderr from `%s`:' % ' '.join(command2.cmdline()))
            difference.add_comment(command2.stderr_content)
        return difference

    @property
    def comment(self):
        return '\n'.join(self._comments)

    @property
    def comments(self):
        return self._comments

    def add_comment(self, comment):
        for line in comment.splitlines():
            self._comments.append(line)

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
    def has_internal_linenos(self):
        return self._has_internal_linenos

    @property
    def details(self):
        return self._details

    def add_details(self, differences):
        if len([d for d in differences if type(d) is not Difference]) > 0:
            raise TypeError("'differences' must contains Difference objects'")
        self._details.extend(differences)

    def get_reverse(self):
        if self._unified_diff is None:
            unified_diff = None
        else:
            unified_diff = reverse_unified_diff(self._unified_diff)
        logger.debug('reverse orig %s %s', self._source1, self._source2)
        difference = Difference(unified_diff, None, None, source=[self._source2, self._source1], comment=self._comments)
        difference.add_details([d.get_reverse() for d in self._details])
        return difference

def make_feeder_from_text_reader(in_file, filter=lambda text_buf: text_buf):
    def encoding_filter(text_buf):
        return filter(text_buf).encode('utf-8')
    return make_feeder_from_raw_reader(in_file, encoding_filter)

def make_feeder_from_command(command):
    def feeder(out_file):
        with profile('command', command.cmdline()[0]):
            end_nl = make_feeder_from_raw_reader(command.stdout, command.filter)(out_file)
            if command.poll() is None:
                command.terminate()
            returncode = command.wait()
        if returncode not in (0, -signal.SIGTERM):
            raise subprocess.CalledProcessError(returncode, command.cmdline(), output=command.stderr.getvalue())
        return end_nl
    return feeder

def make_feeder_from_raw_reader(in_file, filter=lambda buf: buf):
    def feeder(out_file):
        max_lines = Config().max_diff_input_lines
        line_count = 0
        end_nl = False
        h = None
        if max_lines < float("inf"):
            h = hashlib.sha1()
        for buf in in_file:
            line_count += 1
            out = filter(buf)
            if h:
                h.update(out)
            if line_count < max_lines:
                out_file.write(out)
            end_nl = buf[-1] == '\n'
        if h and line_count >= max_lines:
            out_file.write('[ Too much input for diff (SHA1: {}) ]\n'.format(h.hexdigest()).encode('utf-8'))
            end_nl = True
        return end_nl
    return feeder

def make_feeder_from_text(content):
    def feeder(f):
        for offset in range(0, len(content), DIFF_CHUNK):
            f.write(content[offset:offset + DIFF_CHUNK].encode('utf-8'))
        return content and content[-1] == '\n'
    return feeder

def empty_file_feeder():
    def feeder(f):
        return False
    return feeder
