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

import re
import io
import os
import errno
import fcntl
import hashlib
import logging
import threading
import subprocess

from multiprocessing.dummy import Queue

from diffoscope.tempfiles import get_temporary_directory

from .tools import tool_required
from .config import Config

DIFF_CHUNK = 4096

logger = logging.getLogger(__name__)
re_diff_change = re.compile(r'^([+-@]).*', re.MULTILINE)


class DiffParser(object):
    RANGE_RE = re.compile(
        r'^@@\s+-(?P<start1>\d+)(,(?P<len1>\d+))?\s+\+(?P<start2>\d+)(,(?P<len2>\d+))?\s+@@$',
    )

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
        self._max_lines = Config().max_diff_block_lines_saved

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
        if not line:
            return None

        if line.startswith('---'):
            return self.read_headers

        if line.startswith('+++'):
            return self.read_headers

        found = DiffParser.RANGE_RE.match(line)

        if not found:
            raise ValueError('Unable to parse diff headers: %r' % line)

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
            raise ValueError('Unable to parse diff hunk: %r' % line)

        self._diff.write(line)

        if line[0] in ('-', '+'):
            if line[0] == self._direction:
                self._block_len += 1
            else:
                self._block_len = 1
                self._direction = line[0]

            if self._block_len >= self._max_lines:
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

@tool_required('diff')
def run_diff(fifo1, fifo2, end_nl_q1, end_nl_q2):
    cmd = ['diff', '-aU7', fifo1, fifo2]

    logger.debug("Running %s", ' '.join(cmd))

    p = subprocess.Popen(
        cmd,
        shell=False,
        bufsize=1,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    p.stdin.close()

    parser = DiffParser(p.stdout, end_nl_q1, end_nl_q2)
    parser.parse()
    p.wait()

    logger.debug(
        "%s: returncode %d, parsed %s",
        ' '.join(cmd),
        p.returncode,
        parser.success,
    )

    if not parser.success and p.returncode not in (0, 1):
        raise subprocess.CalledProcessError(p.returncode, cmd, output=diff)

    if p.returncode == 0:
        return None

    return parser.diff

class FIFOFeeder(threading.Thread):
    def __init__(self, feeder, fifo_path, end_nl_q=None, *, daemon=True):
        os.mkfifo(fifo_path)
        super().__init__(daemon=daemon)
        self.feeder = feeder
        self.fifo_path = fifo_path
        self.end_nl_q = Queue() if end_nl_q is None else end_nl_q
        self._exception = None
        self._want_join = threading.Event()

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, exc_type, exc_value, exc_tb):
        self.join()

    def run(self):
        try:
            # Try to open the FIFO nonblocking, so we can periodically check
            # if the main thread wants us to wind down.  If it does, there's no
            # more need for the FIFO, so stop the thread.
            while True:
                try:
                    fifo_fd = os.open(self.fifo_path, os.O_WRONLY | os.O_NONBLOCK)
                except OSError as error:
                    if error.errno != errno.ENXIO:
                        raise
                    elif self._want_join.is_set():
                        return
                else:
                    break

            # Now clear the fd's nonblocking flag to let writes block normally.
            fcntl.fcntl(fifo_fd, fcntl.F_SETFL, 0)
            with open(fifo_fd, 'wb') as fifo:
                # The queue works around a unified diff limitation: if there's
                # no newlines in both don't make it a difference
                end_nl = self.feeder(fifo)
                self.end_nl_q.put(end_nl)
        except Exception as error:
            self._exception = error

    def join(self):
        self._want_join.set()
        super().join()
        if self._exception is not None:
            raise self._exception


def empty_file_feeder():
    def feeder(f):
        return False
    return feeder

def make_feeder_from_raw_reader(in_file, filter=lambda buf: buf):
    def feeder(out_file):
        h = None
        end_nl = False
        max_lines = Config().max_diff_input_lines
        line_count = 0

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
            out_file.write("[ Too much input for diff (SHA1: {}) ]\n".format(
                h.hexdigest(),
            ).encode('utf-8'))
            end_nl = True

        return end_nl
    return feeder

def diff(feeder1, feeder2):
    tmpdir = get_temporary_directory().name

    fifo1_path = os.path.join(tmpdir, 'fifo1')
    fifo2_path = os.path.join(tmpdir, 'fifo2')
    with FIFOFeeder(feeder1, fifo1_path) as fifo1, \
         FIFOFeeder(feeder2, fifo2_path) as fifo2:
        return run_diff(fifo1_path, fifo2_path, fifo1.end_nl_q, fifo2.end_nl_q)

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
