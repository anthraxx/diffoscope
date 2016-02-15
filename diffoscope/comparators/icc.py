# -*- coding: utf-8 -*-
#
# diffoscope: in-depth comparison of files, archives, and directories
#
# Copyright © 2016 Jérémy Bobbio <lunar@debian.org>
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
from diffoscope.comparators.binary import File
from diffoscope.comparators.utils import Command
from diffoscope.difference import Difference


class Iccdump(Command):
    @tool_required('cd-iccdump')
    def cmdline(self):
          return ['cd-iccdump', self.path]


class IccFile(File):
    RE_FILE_EXTENSION = re.compile(r'\bICC Profile$')

    @staticmethod
    def recognizes(file):
        return IccFile.RE_FILE_EXTENSION.search(file.magic_file_type)

    def compare_details(self, other, source=None):
        return [Difference.from_command(Iccdump, self.path, other.path)]
