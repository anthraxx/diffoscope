# -*- coding: utf-8 -*-
#
# diffoscope: in-depth comparison of files, archives, and directories
#
# Copyright © 2016 Chris Lamb <lamby@debian.org>
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

import io
import abc
import logging
import subprocess
import threading

logger = logging.getLogger(__name__)


class Command(object, metaclass=abc.ABCMeta):
    def __init__(self, path):
        self._path = path
        logger.debug("Executing %s", ' '.join(self.cmdline()))
        self._process = subprocess.Popen(self.cmdline(),
                                         shell=False, close_fds=True,
                                         env=self.env(),
                                         stdin=subprocess.PIPE,
                                         stdout=subprocess.PIPE,
                                         stderr=subprocess.PIPE)
        if hasattr(self, 'feed_stdin'):
            self._stdin_feeder = threading.Thread(target=self._feed_stdin, args=(self._process.stdin,))
            self._stdin_feeder.daemon = True
            self._stdin_feeder.start()
        else:
            self._stdin_feeder = None
            self._process.stdin.close()
        self._stderr = io.BytesIO()
        self._stderr_line_count = 0
        self._stderr_reader = threading.Thread(target=self._read_stderr)
        self._stderr_reader.daemon = True
        self._stderr_reader.start()

    @property
    def path(self):
        return self._path

    @abc.abstractmethod
    def cmdline(self):
        raise NotImplementedError()

    def env(self):
        return None # inherit parent environment by default

    # Define only if needed. We take care of closing stdin.
    #def feed_stdin(self, stdin)

    def _feed_stdin(self, stdin):
        try:
            self.feed_stdin(stdin)
        finally:
            stdin.close()

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
        returncode = self._process.wait()
        logger.debug(
            "%s returned (exit code: %d)",
            ' '.join(self.cmdline()),
            returncode,
        )
        return returncode

    MAX_STDERR_LINES = 50

    def _read_stderr(self):
        for line in iter(self._process.stderr.readline, b''):
            self._stderr_line_count += 1
            if self._stderr_line_count <= Command.MAX_STDERR_LINES:
                self._stderr.write(line)
        if self._stderr_line_count > Command.MAX_STDERR_LINES:
            self._stderr.write('[ {} lines ignored ]\n'.format(self._stderr_line_count - Command.MAX_STDERR_LINES).encode('utf-8'))
        self._process.stderr.close()

    @property
    def stderr_content(self):
        return self._stderr.getvalue().decode('utf-8', errors='replace')

    @property
    def stderr(self):
        return self._stderr

    @property
    def stdout(self):
        return self._process.stdout
