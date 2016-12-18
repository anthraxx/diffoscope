# -*- coding: utf-8 -*-
#
# diffoscope: in-depth comparison of files, archives, and directories
#
# Copyright © 2014-2015 Jérémy Bobbio <lunar@debian.org>
# Copyright © 2016 Ximin Luo <infinity0@pwned.gg>
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

from diffoscope import logger, tool_required
from diffoscope.difference import Difference
from diffoscope.comparators.utils import Command
from diffoscope.comparators.binary import File
from diffoscope.comparators.libarchive import LibarchiveContainer, \
    list_libarchive


# TODO: this would also be useful for Go archives. Currently those are handled
# by StaticLibFile, but then readelf complains with "Error: Not an ELF file".
# ArFile gives slightly more reasonable output, e.g. a readable plain diff of
# the __.PKGDEF member which is just a text file containing the Go interface.

class ArContainer(LibarchiveContainer):
    def get_members(self):
        members = LibarchiveContainer.get_members(self)
        cls = members.__class__
        known_ignores = {
            "/" : "this is the symbol table, already accounted for in other output",
            "//" : "this is the table for GNU long names, already accounted for in the archive filelist",
        }
        filtered_out = cls([p for p in members.items() if p[0] in known_ignores])
        if filtered_out:
            for k, v in filtered_out.items():
                logger.debug("ignored ar member '%s' because %s", k, known_ignores[k])
        return cls([p for p in members.items() if p[0] not in known_ignores])

class ArSymbolTableDumper(Command):
    @tool_required('nm')
    def cmdline(self):
        return ['nm', '-s', self.path]

class ArFile(File):
    CONTAINER_CLASS = ArContainer
    RE_FILE_TYPE = re.compile(r'\bar archive\b')

    @staticmethod
    def recognizes(file):
        return ArFile.RE_FILE_TYPE.search(file.magic_file_type)

    def compare_details(self, other, source=None):
        return [Difference.from_command(ArSymbolTableDumper, self.path, other.path),
                Difference.from_text_readers(list_libarchive(self.path),
                                             list_libarchive(other.path),
                                             self.path, other.path, source="file list")]
