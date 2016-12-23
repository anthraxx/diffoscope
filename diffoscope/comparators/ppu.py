# -*- coding: utf-8 -*-
#
# diffoscope: in-depth comparison of files, archives, and directories
#
# Copyright © 2015 Daniel Kahn Gillmor <dkg@fifthhorseman.net>
#             2015 Jérémy Bobbio <lunar@debian.org>
#             2015 Paul Gevers <elbrus@debian.org>
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
import subprocess

from diffoscope import tool_required, logger
from diffoscope.profiling import profile
from diffoscope.difference import Difference
from diffoscope.comparators.utils import Command
from diffoscope.comparators.binary import File


class Ppudump(Command):
    @tool_required('ppudump')
    def cmdline(self):
        return ['ppudump', self.path]

    def env(self):
        # ppudump will return times using the local timezone which is not ideal
        # to investigate files. TZ environment variable can be used to enforce UTC.
        # Currently there is no fpc release yet that includes the TC environment
        # variable, but it looks for timezone definitions in the directory
        # specified by TZDIR. So let's set it to a non-existent directory
        # so we get UTC output even when the system timezone is set otherwise.
        env = dict(os.environ)
        env['TZ'] = ':UTC'
        env['TZDIR'] = '/nonexistent'
        return env

    def filter(self, line):
        if re.match(r'^Analyzing %s \(v[0-9]+\)$' % re.escape(self.path), line.decode('utf-8', errors='ignore')):
            return b''
        return line


class PpuFile(File):
    RE_FILE_EXTENSION = re.compile(r'\.ppu$')

    @staticmethod
    def recognizes(file):
        if not PpuFile.RE_FILE_EXTENSION.search(file.name):
            return False
        with open(file.path, 'rb') as f:
            magic = f.read(3)
            if magic != b"PPU":
                return False
            ppu_version = f.read(3).decode('ascii', errors='ignore')
        if not hasattr(PpuFile, 'ppu_version'):
            try:
                with profile('command', 'ppudump'):
                    subprocess.check_output(['ppudump', '-vh', file.path], shell=False, stderr=subprocess.STDOUT)
                PpuFile.ppu_version = ppu_version
            except subprocess.CalledProcessError as e:
                error = e.output.decode('utf-8', errors='ignore')
                m = re.search('Expecting PPU version ([0-9]+)', error)
                try:
                    PpuFile.ppu_version = m.group(1)
                except AttributeError:
                    if m is None:
                        PpuFile.ppu_version = None
                        logger.debug('Unable to read PPU version')
                    else:
                        raise
            except OSError:
                PpuFile.ppu_version = None
                logger.debug('Unable to read PPU version')
        return PpuFile.ppu_version == ppu_version

    def compare_details(self, other, source=None):
        return [Difference.from_command(Ppudump, self.path, other.path)]
