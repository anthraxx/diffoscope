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

import re
import struct
import subprocess
from debbindiff import tool_required
from debbindiff.comparators.binary import File, needs_content
from debbindiff.comparators.utils import Command
from debbindiff.difference import Difference
from debbindiff import logger


class ShowIface(Command):
    @tool_required('ghc')
    def cmdline(self):
        return ['ghc', '--show-iface', self.path]


HI_MAGIC = 33214052


class HiFile(File):
    RE_FILE_EXTENSION = re.compile(r'\.(p_|dyn_)?hi$')

    @staticmethod
    def recognizes(file):
        if not HiFile.RE_FILE_EXTENSION.search(file.name):
            return False
        if not hasattr(HiFile, 'ghc_version'):
            try:
                output = subprocess.check_output(['ghc', '--numeric-version'], shell=False)
                HiFile.ghc_version = output.decode('utf-8').strip().split('.')
                logger.debug('Found GHC version %s', HiFile.ghc_version)
            except OSError:
                HiFile.ghc_version = None
                logger.debug('Unable to read GHC version')
        if HiFile.ghc_version is None:
            return False

        with file.get_content():
            with open(file.path) as fp:
                buf = fp.read(32)
                magic = struct.unpack_from('!I', buf)[0]
                if magic != HI_MAGIC:
                    logger.debug('Haskell interface magic mismatch. Found %d instead of %d' % (magic, HI_MAGIC))
                    return False
                # XXX: what is second field for?
                version_found = map(unichr, struct.unpack_from('<I4xIB', buf, 16))
                if version_found != HiFile.ghc_version:
                    logger.debug('Haskell version mismatch. Found %s instead of %s.',
                                 version_found, HiFile.ghc_version)
                    return False
                return True

    @needs_content
    def compare_details(self, other, source=None):
        return [Difference.from_command(ShowIface, self.path, other.path)]
