# -*- coding: utf-8 -*-
#
# debbindiff: highlight differences between two builds of Debian packages
#
# Copyright © 2014-2015 Jérémy Bobbio <lunar@debian.org>
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

from abc import ABCMeta, abstractmethod
from contextlib import contextmanager
# The following would be shutil.which in Python 3.3
import hashlib
import re
import os
import shutil
import subprocess
import tempfile
from threading import Thread
from debbindiff.comparators.binary import \
    compare_binary_files, are_same_binaries
from debbindiff.difference import Difference
from debbindiff import logger, RequiredToolNotFound


# decorator that will create a fallback on binary diff if no differences
# are detected or if an external tool fails
def binary_fallback(original_function):
    def with_fallback(path1, path2, source=None):
        if are_same_binaries(path1, path2):
            return []
        try:
            inside_differences = original_function(path1, path2, source)
            # no differences detected inside? let's at least do a binary diff
            if len(inside_differences) == 0:
                difference = compare_binary_files(path1, path2, source=source)[0]
                difference.comment = (difference.comment or '') + \
                    "No differences found inside, yet data differs"
            else:
                difference = Difference(None, path1, path2, source=source)
                difference.add_details(inside_differences)
        except subprocess.CalledProcessError as e:
            difference = compare_binary_files(path1, path2, source=source)[0]
            output = re.sub(r'^', '    ', e.output, flags=re.MULTILINE)
            cmd = ' '.join(e.cmd)
            difference.comment = (difference.comment or '') + \
                "Command `%s` exited with %d. Output:\n%s" \
                % (cmd, e.returncode, output)
        except RequiredToolNotFound as e:
            difference = compare_binary_files(path1, path2, source=source)[0]
            difference.comment = (difference.comment or '') + \
                "'%s' not available in path. Falling back to binary comparison." % e.command
            package = e.get_package()
            if package:
                difference.comment += "\nInstall '%s' to get a better output." % package
        return [difference]
    return with_fallback


@contextmanager
def make_temp_directory():
    temp_dir = tempfile.mkdtemp(suffix='debbindiff')
    try:
        yield temp_dir
    finally:
        shutil.rmtree(temp_dir)


def get_ar_content(path):
    return subprocess.check_output(
        ['ar', 'tv', path], stderr=subprocess.STDOUT, shell=False).decode('utf-8')


class Command(object):
    __metaclass__ = ABCMeta

    def __init__(self, path):
        self._path = path
        self._process = subprocess.Popen(self.cmdline(),
                                         shell=False, close_fds=True,
                                         stdin=subprocess.PIPE,
                                         stdout=subprocess.PIPE,
                                         stderr=subprocess.PIPE)
        if hasattr(self, 'feed_stdin'):
            self._stdin_feeder = Thread(target=self.feed_stdin, args=(self._process.stdin,))
            self._stdin_feeder.daemon = True
            self._stdin_feeder.start()
        else:
            self._stdin_feeder = None
            self._process.stdin.close()
        self._stderr = ''
        self._stderr_line_count = 0
        self._stderr_reader = Thread(target=self._read_stderr)
        self._stderr_reader.daemon = True
        self._stderr_reader.start()

    @property
    def path(self):
        return self._path

    @abstractmethod
    def cmdline(self):
        raise NotImplemented

    # Define only if needed
    #def feed_stdin(self, f)

    def filter(self, line):
        # Assume command output is utf-8 by default
        return line

    def poll(self):
        return self._process.poll()

    def terminate(self):
        return self._process.terminate()

    def wait(self):
        if self._stdin_feeder:
            self._stdin_feeder.join()
        self._stderr_reader.join()
        self._process.wait()

    MAX_STDERR_LINES = 50

    def _read_stderr(self):
        for line in iter(self._process.stderr.readline, b''):
            self._stderr_line_count += 1
            if self._stderr_line_count <= Command.MAX_STDERR_LINES:
                self._stderr += line
        if self._stderr_line_count > Command.MAX_STDERR_LINES:
            self._stderr += '[ %d lines ignored ]\n' % (self._stderr_line_count - Command.MAX_STDERR_LINES)
        self._process.stderr.close()

    @property
    def stderr_content(self):
        return self._stderr

    @property
    def stdout(self):
        return self._process.stdout
