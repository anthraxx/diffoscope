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

from diffoscope.difference import Difference
from diffoscope.comparators.binary import File
from diffoscope.comparators.libarchive import LibarchiveContainer, \
    list_libarchive

class TarContainer(LibarchiveContainer):
    pass


class TarFile(File):
    CONTAINER_CLASS = TarContainer
    RE_FILE_TYPE = re.compile(r'\btar archive\b')

    @staticmethod
    def recognizes(file):
        return TarFile.RE_FILE_TYPE.search(file.magic_file_type)

    def compare_details(self, other, source=None):
        return [Difference.from_text_readers(list_libarchive(self.path),
                                        list_libarchive(other.path),
                                        self.path, other.path, source="file list")]
