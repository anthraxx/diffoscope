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
# along with diffoscope.  If not, see <http://www.gnu.org/licenses/>.

import re
from diffoscope import tool_required
from diffoscope.comparators.binary import File, needs_content
from diffoscope.comparators.utils import Command
from diffoscope.difference import Difference


class Ppudump(Command):
    @tool_required('ppudump')
    def cmdline(self):
        return ['ppudump', self.path]

    def filter(self, line):
        if re.match(r'^Analyzing %s \(v[0-9]+\)$' % re.escape(self.path), line.decode('utf-8')):
            return b''
        return line


class PpuFile(File):
    RE_FILE_EXTENSION = re.compile(r'\.ppu$')

    @staticmethod
    def recognizes(file):
        if not PpuFile.RE_FILE_EXTENSION.search(file.name):
            return False
        with file.get_content():
            with open(file.path, 'rb') as f:
                if re.match(rb'^PPU[0-9]+', f.read(32)):
                    return True
        return False

    @needs_content
    def compare_details(self, other, source=None):
        return [Difference.from_command(Ppudump, self.path, other.path)]
