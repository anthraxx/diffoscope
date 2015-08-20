# -*- coding: utf-8 -*-
#
# diffoscope: in-depth comparison of files, archives, and directories
#
# Copyright © 2015 Reiner Herrmann <reiner@reiner-h.de>
#             2015 Jérémy Bobbio <lunar@debian.org>
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
from diffoscope.comparators.libarchive import LibarchiveContainer
from diffoscope.comparators.utils import Command
from diffoscope.difference import Difference


class CpioContent(Command):
    @tool_required('cpio')
    def cmdline(self):
        return ['cpio', '--quiet', '--numeric-uid-gid', '-tvF', self.path]


class CpioFile(File):
    RE_FILE_TYPE = re.compile(r'\bcpio archive\b')

    @staticmethod
    def recognizes(file):
        return CpioFile.RE_FILE_TYPE.search(file.magic_file_type)

    @needs_content
    def compare_details(self, other, source=None):
        differences = []
        differences.append(Difference.from_command(
            CpioContent, self.path, other.path, source="file list"))
        with LibarchiveContainer(self).open() as my_container, \
             LibarchiveContainer(other).open() as other_container:
            differences.extend(my_container.compare(other_container, source))
        return differences
