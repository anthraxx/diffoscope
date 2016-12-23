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
import struct
import platform
import subprocess

from diffoscope import tool_required, logger
from diffoscope.profiling import profile
from diffoscope.difference import Difference
from diffoscope.comparators.utils import Command
from diffoscope.comparators.binary import File


class ShowIface(Command):
    @tool_required('ghc')
    def cmdline(self):
        return ['ghc', '--show-iface', self.path]


HI_MAGIC_32 = struct.pack('!I', 0x1face)
HI_MAGIC_64 = struct.pack('!I', 0x1face64)
if platform.architecture()[0] == '32bit':
    HI_MAGIC = HI_MAGIC_32
else:
    HI_MAGIC = HI_MAGIC_64

class HiFile(File):
    RE_FILE_EXTENSION = re.compile(r'\.(p_|dyn_)?hi$')

    @staticmethod
    def recognizes(file):
        if not HiFile.RE_FILE_EXTENSION.search(file.name):
            return False
        if not hasattr(HiFile, 'hi_version'):
            try:
                with profile('command', 'ghc'):
                    output = subprocess.check_output(['ghc', '--numeric-version'], shell=False)
                major, minor, patch = map(int, output.decode('utf-8').strip().split('.'))
                HiFile.hi_version = "%d%02d%d" % (major, minor, patch)
                logger.debug('Found .hi version %s', HiFile.hi_version)
            except OSError:
                HiFile.hi_version = None
                logger.debug('Unable to read GHC version')
        if HiFile.hi_version is None:
            return False

        with open(file.path, 'rb') as fp:
            # read magic
            buf = fp.read(4)
            if buf != HI_MAGIC:
                logger.debug('Haskell interface magic mismatch. Found %r instead of %r or %r', buf, HI_MAGIC_32, HI_MAGIC_64)
                return False
            # skip some old descriptor thingy that has varying size
            if buf == HI_MAGIC_32:
                fp.read(4)
            elif buf == HI_MAGIC_64:
                fp.read(8)
            # skip way_descr
            fp.read(4)
            # now read version
            buf = fp.read(16)
            version_found = ''.join(map(chr, struct.unpack_from('=3IB', buf)))
            if version_found != HiFile.hi_version:
                logger.debug('Haskell version mismatch. Found %s instead of %s.',
                             version_found, HiFile.hi_version)
                return False
            return True

    def compare_details(self, other, source=None):
        return [Difference.from_command(ShowIface, self.path, other.path)]
