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

import os
import re
import io
import signal
import hashlib
import threading
import contextlib
import subprocess
import tempfile

from multiprocessing.dummy import Queue

from diffoscope import logger, tool_required
from diffoscope.exc import RequiredToolNotFound
from diffoscope.config import Config
from diffoscope.profiling import profile


class DiffParser(object):
    RANGE_RE = re.compile(r'^@@\s+-(?P<start1>\d+)(,(?P<len1>\d+))?\s+\+(?P<start2>\d+)(,(?P<len2>\d+))?\s+@@$')

    def __init__(self, output, end_nl_q1, end_nl_q2):
        self._output = output
        self._end_nl_q1 = end_nl_q1
        self._end_nl_q2 = end_nl_q2
        self._action = self.read_headers
        self._diff = io.StringIO()
        self._success = False
        self._remaining_hunk_lines = None
        self._block_len = None
        self._direction = None
        self._end_nl = None

    @property
    def diff(self):
        return self._diff.getvalue()

    @property
    def success(self):
        return self._success

    def parse(self):
        for line in self._output:
            self._action = self._action(line.decode('utf-8', errors='replace'))
        self._action('')
        self._success = True
        self._output.close()

    def read_headers(self, line):
        found = DiffParser.RANGE_RE.match(line)
        if not line:
            return None
        elif line.startswith('---'):
            return self.read_headers
        elif line.startswith('+++'):
            return self.read_headers
        elif not found:
            raise ValueError('Unable to parse diff headers: %s' % repr(line))
        self._diff.write(line)
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
        if not line:
            return None
        elif line[0] == ' ':
            self._remaining_hunk_lines -= 2
        elif line[0] == '+':
            self._remaining_hunk_lines -= 1
        elif line[0] == '-':
            self._remaining_hunk_lines -= 1
        elif line[0] == '\\':
            # When both files don't end with \n, do not show it as a difference
            if self._end_nl is None:
                end_nl1 = self._end_nl_q1.get()
                end_nl2 = self._end_nl_q2.get()
                self._end_nl = end_nl1 and end_nl2
            if not self._end_nl:
                return self.read_hunk
        elif self._remaining_hunk_lines == 0:
            return self.read_headers(line)
        else:
            raise ValueError('Unable to parse diff hunk: %s' % repr(line))
        self._diff.write(line)
        if line[0] in ('-', '+'):
            if line[0] == self._direction:
                self._block_len += 1
            else:
                self._block_len = 1
                self._direction = line[0]
            max_lines = Config().max_diff_block_lines_saved
            if self._block_len >= max_lines:
                return self.skip_block
        else:
            self._block_len = 1
            self._direction = line[0]
        return self.read_hunk

    def skip_block(self, line):
        if self._remaining_hunk_lines == 0 or line[0] != self._direction:
            removed = self._block_len - Config().max_diff_block_lines_saved
            if removed:
                self._diff.write('%s[ %d lines removed ]\n' % (self._direction, removed))
            return self.read_hunk(line)
        self._block_len += 1
        self._remaining_hunk_lines -= 1
        return self.skip_block




DIFF_CHUNK = 4096


@tool_required('diff')
def run_diff(fifo1, fifo2, end_nl_q1, end_nl_q2):
    cmd = ['diff', '-aU7', fifo1, fifo2]
    logger.debug('running %s', cmd)
    p = subprocess.Popen(cmd, shell=False, bufsize=1,
                         stdin=subprocess.PIPE,
                         stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT,
    )
    p.stdin.close()
    parser = DiffParser(p.stdout, end_nl_q1, end_nl_q2)
    t_read = threading.Thread(target=parser.parse)
    t_read.daemon = True
    t_read.start()
    t_read.join()
    p.wait()
    logger.debug('done with diff, returncode %d, parsed %s', p.returncode, parser.success)
    if not parser.success and p.returncode not in (0, 1):
        raise subprocess.CalledProcessError(p.returncode, cmd, output=diff)
    if p.returncode == 0:
        return None
    return parser.diff


# inspired by https://stackoverflow.com/a/6874161
class ExThread(threading.Thread):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.__status_queue = Queue()

    def run(self, *args, **kwargs):
        try:
            super().run(*args, **kwargs)
        except Exception as ex:
            #except_type, except_class, tb = sys.exc_info()
            self.__status_queue.put(ex)
        self.__status_queue.put(None)

    def wait_for_exc_info(self):
        return self.__status_queue.get()

    def join(self):
        ex = self.wait_for_exc_info()
        if ex is None:
            return
        else:
            raise ex


def feed(feeder, f, end_nl_q):
    # work-around unified diff limitation: if there's no newlines in both
    # don't make it a difference
    try:
        end_nl = feeder(f)
        end_nl_q.put(end_nl)
    finally:
        f.close()


@contextlib.contextmanager
def fd_from_feeder(feeder, end_nl_q, fifo):
    outf = open(fifo, 'wb')
    t = ExThread(target=feed, args=(feeder, outf, end_nl_q))
    t.daemon = True
    t.start()
    try:
        t.join()
    finally:
        outf.close()


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


def diff(feeder1, feeder2):
    end_nl_q1 = Queue()
    end_nl_q2 = Queue()
    with tempfile.TemporaryDirectory() as tmpdir:
        fifo1 = '{}/f1'.format(tmpdir)
        fifo2 = '{}/f2'.format(tmpdir)
        fd_from_feeder(feeder1, end_nl_q1, fifo1)
        fd_from_feeder(feeder2, end_nl_q2, fifo2)
        return run_diff(fifo1, fifo2, end_nl_q1, end_nl_q2)


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


def get_source(path1, path2):
    if os.path.basename(path1) == os.path.basename(path2):
        return os.path.basename(path1)
    return None


def reverse_unified_diff(diff):
    res = []
    for line in diff.splitlines(True): # keepends=True
        found = DiffParser.RANGE_RE.match(line)
        if found:
            before = found.group('start2')
            if found.group('len2') is not None:
                before += ',' + found.group('len2')
            after = found.group('start1')
            if found.group('len1') is not None:
                after += ',' + found.group('len1')
            res.append('@@ -%s +%s @@\n' % (before, after))
        elif line.startswith('-'):
            res.append('+')
            res.append(line[1:])
        elif line.startswith('+'):
            res.append('-')
            res.append(line[1:])
        else:
            res.append(line)
    return ''.join(res)

re_diff_change = re.compile(r'^([+-@]).*', re.MULTILINE)

def color_unified_diff(diff):
    RESET = '\033[0m'
    RED, GREEN, CYAN = '\033[31m', '\033[32m', '\033[0;36m'

    def repl(m):
        return '{}{}{}'.format({
            '-': RED,
            '@': CYAN,
            '+': GREEN,
        }[m.group(1)], m.group(0), RESET)

    return re_diff_change.sub(repl, diff)
