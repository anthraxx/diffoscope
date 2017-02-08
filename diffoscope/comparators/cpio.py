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
# along with diffoscope.  If not, see <https://www.gnu.org/licenses/>.

import re

from diffoscope.difference import Difference

from .utils.file import File
from .utils.libarchive import LibarchiveContainer, list_libarchive


class CpioFile(File):
    CONTAINER_CLASS = LibarchiveContainer
    RE_FILE_TYPE = re.compile(r'\bcpio archive\b')

    def compare_details(self, other, source=None):
        return [Difference.from_text_readers(
            list_libarchive(self.path),
            list_libarchive(other.path),
            self.path,
            other.path,
            source="file list",
        )]
