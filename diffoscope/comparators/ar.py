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
# along with diffoscope.  If not, see <http://www.gnu.org/licenses/>.

import os.path
import re
from diffoscope.difference import Difference
from diffoscope.comparators.binary import File
from diffoscope.comparators.libarchive import LibarchiveContainer, list_libarchive
from diffoscope import logger

# TODO: this would also be useful for Go archives. Currently those are handled
# by StaticLibFile, but then readelf complains with "Error: Not an ELF file".
# ArFile gives slightly more reasonable output, e.g. a readable plain diff of
# the __.PKGDEF member which is just a text file containing the Go interface.

class ArContainer(LibarchiveContainer):
    def get_members(self):
        members = LibarchiveContainer.get_members(self)
        cls = members.__class__
        # for some reason libarchive outputs ["/", "//"] as member names for
        # some archives. for now, let's just filter these out, otherwise they
        # cause exceptions later. eventually, we should investigate this in
        # more detail and handle it properly.
        filtered_out = cls([p for p in members.items() if not os.path.basename(p[0])])
        if filtered_out:
            logger.debug("ignored directory ar members %s in %s, don't yet know how to handle these",
                list(filtered_out.keys()), self.source.path)
        return cls([p for p in members.items() if os.path.basename(p[0])])


class ArFile(File):
    CONTAINER_CLASS = ArContainer
    RE_FILE_TYPE = re.compile(r'\bar archive\b')

    @staticmethod
    def recognizes(file):
        return ArFile.RE_FILE_TYPE.search(file.magic_file_type)

    def compare_details(self, other, source=None):
        return [Difference.from_text_readers(list_libarchive(self.path),
                                        list_libarchive(other.path),
                                        self.path, other.path, source="file list")]
