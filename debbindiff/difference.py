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

from contextlib import contextmanager
import os
import os.path
from functools import partial
from tempfile import NamedTemporaryFile
import re
import subprocess
import sys
import traceback
from threading import Thread
from multiprocessing import Queue
from debbindiff import logger, tool_required, RequiredToolNotFound


MAX_DIFF_BLOCK_LINES = 50
MAX_DIFF_INPUT_LINES = 100000 # GNU diff cannot process arbitrary large files :(


class DiffParser(object):
    RANGE_RE = re.compile(r'^@@\s+-(?P<start1>\d+)(,(?P<len1>\d+))?\s+\+(?P<start2>\d+)(,(?P<len2>\d+))?\s+@@$')

    def __init__(self, output, end_nl_q1, end_nl_q2):
        self._output = output
        self._end_nl_q1 = end_nl_q1
        self._end_nl_q2 = end_nl_q2
        self._action = self.read_headers
        self._diff = ''
        self._success = False
        self._remaining_hunk_lines = None
        self._block_len = None
        self._direction = None
        self._end_nl = None

    @property
    def diff(self):
        return self._diff

    @property
    def success(self):
        return self._success

    def parse(self):
        for line in iter(self._output.readline, b''):
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
        if self._remaining_hunk_lines == 0 or line[0] != self._direction:
            self._diff += '%s[ %d lines removed ]\n' % (self._direction, self._block_len - MAX_DIFF_BLOCK_LINES)
            return self.read_hunk(line)
        self._block_len += 1
        self._remaining_hunk_lines -= 1
        return self.skip_block




DIFF_CHUNK = 4096


@tool_required('diff')
def run_diff(fd1, fd2, end_nl_q1, end_nl_q2):
    logger.debug('running diff')
    cmd = ['diff', '-au7', '/dev/fd/%d' % fd1, '/dev/fd/%d' % fd2]
    def close_fds():
        fds = [int(fd) for fd in os.listdir('/dev/fd')
                       if int(fd) not in (1, 2, fd1, fd2)]
        for fd in fds:
            try:
                os.close(fd)
            except OSError:
                pass
    p = subprocess.Popen(cmd, shell=False, bufsize=1,
                         stdin=subprocess.PIPE,
                         stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT,
                         preexec_fn=close_fds)
    p.stdin.close()
    os.close(fd1)
    os.close(fd2)
    parser = DiffParser(p.stdout, end_nl_q1, end_nl_q2)
    t_read = Thread(target=parser.parse)
    t_read.daemon = True
    t_read.start()
    t_read.join()
    p.wait()
    if not parser.success and p.returncode not in (0, 1):
        raise subprocess.CalledProcessError(cmd, p.returncode, output=diff)
    if p.returncode == 0:
        return None
    return parser.diff


# inspired by https://stackoverflow.com/a/6874161
class ExThread(Thread):
    def __init__(self, *args, **kwargs):
        super(ExThread, self).__init__(*args, **kwargs)
        self.__status_queue = Queue()

    def run(self, *args, **kwargs):
        try:
            super(ExThread, self).run(*args, **kwargs)
        except Exception:
            except_type, except_class, tb = sys.exc_info()
            self.__status_queue.put((except_type, except_class, traceback.extract_tb(tb)))
        self.__status_queue.put(None)

    def wait_for_exc_info(self):
        return self.__status_queue.get()

    def join(self):
        ex_info = self.wait_for_exc_info()
        if ex_info is None:
            return
        else:
            except_type, except_class, tb = ex_info
            logger.debug('Exception: %s' %
                         traceback.format_exception_only(except_type, except_class)[0].strip())
            logger.debug('Traceback:')
            for line in traceback.format_list(tb):
                logger.debug(line[:-1])
            raise except_type, except_class, None


def feed(feeder, f, end_nl_q):
    # work-around unified diff limitation: if there's no newlines in both
    # don't make it a difference
    try:
        end_nl = feeder(f)
        end_nl_q.put(end_nl)
    finally:
        f.close()


@contextmanager
def fd_from_feeder(feeder, end_nl_q):
    pipe_r, pipe_w = os.pipe()
    outf = os.fdopen(pipe_w, 'w')
    t = ExThread(target=feed, args=(feeder, outf, end_nl_q))
    t.daemon = True
    t.start()
    yield pipe_r
    try:
        t.join()
    finally:
        outf.close()


def make_feeder_from_unicode(content):
    def feeder(f):
        for offset in range(0, len(content), DIFF_CHUNK):
            f.write(content[offset:offset + DIFF_CHUNK].encode('utf-8'))
        return content and content[-1] == '\n'
    return feeder


def make_feeder_from_file(in_file, filter=lambda buf: buf.encode('utf-8')):
    def feeder(out_file):
        line_count = 0
        end_nl = False
        for buf in iter(in_file.readline, b''):
            line_count += 1
            out_file.write(filter(buf))
            if line_count >= MAX_DIFF_INPUT_LINES:
                out_file.write('[ Too much input for diff ]%s\n' % (' ' * out_file.fileno()))
                end_nl = True
                break
            end_nl = buf[-1] == '\n'
        return end_nl
    return feeder

def make_feeder_from_command(command):
    def feeder(out_file):
        end_nl = make_feeder_from_file(command.stdout, command.filter)(out_file)
        if command.poll() is None:
            command.terminate()
        command.wait()
        return end_nl
    return feeder


def diff(feeder1, feeder2):
    try:
        end_nl_q1 = Queue()
        end_nl_q2 = Queue()
    except OSError as e:
        if e.errno not in (13, 38):
            raise
        logger.critical('/dev/shm is not available or not on a tmpfs. Unable to create semaphore.')
        sys.exit(2)
    with fd_from_feeder(feeder1, end_nl_q1) as fd1:
        with fd_from_feeder(feeder2, end_nl_q2) as fd2:
            return run_diff(fd1, fd2, end_nl_q1, end_nl_q2)


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
    def from_feeder(feeder1, feeder2, path1, path2, source=None,
                    comment=None):
        actual_comment = comment
        unified_diff = None
        try:
            unified_diff = diff(feeder1, feeder2)
        except RequiredToolNotFound:
            actual_comment = 'diff is not available!'
            if comment:
                actual_comment += '\n\n' + orig_comment
        if not unified_diff:
            return None
        return Difference(unified_diff, path1, path2, source, actual_comment)

    @staticmethod
    def from_unicode(content1, content2, *args, **kwargs):
        return Difference.from_feeder(make_feeder_from_unicode(content1),
                                      make_feeder_from_unicode(content2),
                                      *args, **kwargs)

    @staticmethod
    def from_file(file1, file2, *args, **kwargs):
        return Difference.from_feeder(make_feeder_from_file(file1),
                                      make_feeder_from_file(file2),
                                      *args, **kwargs)

    @staticmethod
    def from_command(cls, path1, path2, *args, **kwargs):
        command_args = []
        if 'command_args' in kwargs:
            command_args = kwargs['command_args']
            del kwargs['command_args']
        command1 = cls(path1, *command_args)
        command2 = cls(path2, *command_args)
        if 'source' not in kwargs:
            kwargs['source'] = ' '.join(map(lambda x: '{}' if x == command1.path else x, command1.cmdline()))
        difference = Difference.from_feeder(make_feeder_from_command(command1),
                                            make_feeder_from_command(command2),
                                            path1, path2, *args, **kwargs)
        if not difference:
            return None
        if command1.stderr_content or command2.stderr_content:
            if difference.comment:
                difference.comment += '\n'
            else:
                difference.comment = ''
            if command1.stderr_content:
                difference.comment += 'stderr from `%s`:\n%s\n' % (' '.join(command1.cmdline()), command1.stderr_content)
            if command2.stderr_content:
                difference.comment += 'stderr from `%s`:\n%s\n' % (' '.join(command2.cmdline()), command2.stderr_content)
        return difference

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
