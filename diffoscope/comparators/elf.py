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
# along with diffoscope.  If not, see <http://www.gnu.org/licenses/>.

import os.path
import re
from diffoscope import tool_required
from diffoscope.comparators.binary import File
from diffoscope.comparators.utils import get_ar_content, Command
from diffoscope.difference import Difference


class Readelf(Command):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # we don't care about the name of the archive
        self._archive_re = re.compile(r'^File: %s\(' % re.escape(self.path))
        self._basename = os.path.basename(self.path)

    @tool_required('readelf')
    def cmdline(self):
        return ['readelf'] + self.readelf_options() + [self.path]

    def readelf_options(self):
        return []

    def filter(self, line):
        try:
            # we don't care about the name of the archive
            line = self._archive_re.sub('File: lib.a(', line.decode('utf-8'))
            # the full path can appear in the output, we need to remove it
            return line.replace(self.path, self._basename).encode('utf-8')
        except UnicodeDecodeError:
            return line

class ReadelfAll(Readelf):
    def readelf_options(self):
        return ['-all']

class ReadelfDebugDump(Readelf):
    def readelf_options(self):
        return ['--debug-dump']

class ObjdumpDisassemble(Command):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # we don't care about the name of the archive
        self._archive_re = re.compile(r'^In archive %s:' % re.escape(self.path))
        self._basename = os.path.basename(self.path)

    @tool_required('objdump')
    def cmdline(self):
        return ['objdump', '--disassemble', '--full-contents', self.path]

    def filter(self, line):
        try:
            # we don't care about the name of the archive
            line = self._archive_re.sub('In archive:', line.decode('utf-8'))
            # the full path can appear in the output, we need to remove it
            return line.replace(self.path, self._basename).encode('utf-8')
        except UnicodeDecodeError:
            return line

def _compare_elf_data(path1, path2):
    return [Difference.from_command(ReadelfAll, path1, path2),
            Difference.from_command(ReadelfDebugDump, path1, path2),
            Difference.from_command(ObjdumpDisassemble, path1, path2)]

class ElfFile(File):
    RE_FILE_TYE = re.compile(r'^ELF ')

    @staticmethod
    def recognizes(file):
        return ElfFile.RE_FILE_TYE.match(file.magic_file_type)

    def compare_details(self, other, source=None):
        return _compare_elf_data(self.path, other.path)

class StaticLibFile(File):
    RE_FILE_TYPE = re.compile(r'\bar archive\b')
    RE_FILE_EXTENSION = re.compile(r'\.a$')

    @staticmethod
    def recognizes(file):
        return StaticLibFile.RE_FILE_TYPE.search(file.magic_file_type) and StaticLibFile.RE_FILE_EXTENSION.search(file.name)

    def compare_details(self, other, source=None):
        differences = []
        # look up differences in metadata
        content1 = get_ar_content(self.path)
        content2 = get_ar_content(other.path)
        differences.append(Difference.from_text(
                               content1, content2, self.path, other.path, source="metadata"))
        differences.extend(_compare_elf_data(self.path, other.path))
        return differences
