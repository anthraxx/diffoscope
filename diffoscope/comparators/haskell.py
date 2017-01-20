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
import logging
import platform
import subprocess

from diffoscope.tools import tool_required
from diffoscope.profiling import profile
from diffoscope.difference import Difference

from .utils.file import File
from .utils.command import Command

HI_MAGIC_32 = struct.pack('>I', 0x1face)
HI_MAGIC_64 = struct.pack('>I', 0x1face64)

if platform.architecture()[0] == '32bit':
    HI_MAGIC = HI_MAGIC_32
else:
    HI_MAGIC = HI_MAGIC_64

logger = logging.getLogger(__name__)


class ShowIface(Command):
    @tool_required('ghc')
    def cmdline(self):
        return ['ghc', '--show-iface', self.path]

class HiFile(File):
    """
    Here is how an example .hi file starts:

    % hexdump -C tests/data/test1.hi | head -n 1
    00000000  01 fa ce 64 00 00 00 00  00 00 00 00 04 00 00 00  |...d............|
              ~~~~~~~~~~~ ~~~~~~~~~~~~~~~~~~~~~~~~ ~~ ~~~~~~~~~~
                HI_MAGIC    zero padding (used to  ↑↑  int('7')
                             be a field here)      ||
                                                   ||
                           ·~~~~~~~~~~~~~~~~~~~~~~~||
                           | version string length ||
                           ·~~~~~~~~~~~~~~~~~~~~~~~~~

    00000010  37 00 00 00 31 00 00 00  30 00 00 00 33 00 00 00  |7...1...0...3...|
            ~~~~ ~~~~~~~~~~~ ~~~~~~~~~~~~ ~~~~~~~~~~~
                  int('1')     int('0')    int('3')


    So the version of this file has 4 characters, and it's 7103. Note how all
    this information is stored as big endian.
    """
    RE_FILE_EXTENSION = re.compile(r'\.(p_|dyn_)?hi$')

    @staticmethod
    def recognizes(file):
        if not HiFile.RE_FILE_EXTENSION.search(file.name):
            return False

        if not hasattr(HiFile, 'hi_version'):
            try:
                with profile('command', 'ghc'):
                    output = subprocess.check_output(
                        ['ghc', '--numeric-version'],
                    )
            except (OSError, subprocess.CalledProcessError):
                HiFile.hi_version = None
                logger.debug("Unable to read GHC version")
            else:
                major, minor, patch = [
                    int(x) for x in output.decode('utf-8').strip().split('.')
                ]
                HiFile.hi_version = '%d%02d%d' % (major, minor, patch)
                logger.debug("Found .hi version %s", HiFile.hi_version)

        if HiFile.hi_version is None:
            return False

        with open(file.path, 'rb') as fp:
            # Read magic
            buf = fp.read(4)
            if buf != HI_MAGIC:
                logger.debug(
                    "Haskell interface magic mismatch. "
                    "Found %r instead of %r or %r",
                    buf, HI_MAGIC_32, HI_MAGIC_64,
                )
                return False

            # Skip some old descriptor thingy that has varying size
            if buf == HI_MAGIC_32:
                fp.read(4)
            elif buf == HI_MAGIC_64:
                fp.read(8)

            # Read version, which is [Char]
            buf = fp.read(1)

            # Small list optimisation - anything less than 0xff has its length
            # in a single byte; everything else is 0xff followed by the 32-bit
            # length (big-endian).
            if buf[0] == 0xff:
                buf = fp.read(4)
                length = struct.unpack('>I', buf)[0]
            else:
                length = buf[0]

            # Now read characters; each is 32-bit big-endian.
            version_found = ''.join(
                chr(struct.unpack('>I', fp.read(4))[0]) for _ in range(length)
            )

            if version_found != HiFile.hi_version:
                logger.debug(
                    "Haskell version mismatch; found %s instead of %s.",
                    version_found,
                    HiFile.hi_version,
                )
                return False

            return True

    def compare_details(self, other, source=None):
        return [Difference.from_command(ShowIface, self.path, other.path)]
