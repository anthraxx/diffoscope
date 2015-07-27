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

import os.path
import re
import subprocess
from debbindiff import tool_required
from debbindiff.comparators.binary import File, needs_content
from debbindiff.comparators.utils import get_ar_content, Command
from debbindiff.difference import Difference


class Readelf(Command):
    @tool_required('readelf')
    def cmdline(self):
        return ['readelf'] + self.readelf_options() + [self.path]

    def readelf_options(self):
        return []

    def filter(self, line):
        # we don't care about the name of the archive
        line = re.sub('^File: %s\(' % re.escape(self.path), 'File: lib.a(', line)
        # the full path can appear in the output, we need to remove it
        return line.replace(self.path, os.path.basename(self.path))

class ReadelfAll(Readelf):
    def readelf_options(self):
        return ['-all']

class ReadelfDebugDump(Readelf):
    def readelf_options(self):
        return ['--debug-dump']

class ObjdumpDisassemble(Command):
    @tool_required('objdump')
    def cmdline(self):
        return ['objdump', '--disassemble', '--full-contents', self.path]

    def filter(self, line):
        # we don't care about the name of the archive
        line = re.sub('^In archive %s:' % re.escape(self.path), 'In archive:', line)
        # the full path can appear in the output, we need to remove it
        return line.replace(self.path, os.path.basename(self.path))

def _compare_elf_data(path1, path2):
    differences = []
    differences.append(Difference.from_command(ReadelfAll, path1, path2))
    differences.append(Difference.from_command(ReadelfDebugDump, path1, path2))
    differences.append(Difference.from_command(ObjdumpDisassemble, path1, path2))
    return differences

class ElfFile(File):
    RE_FILE_TYE = re.compile(r'^ELF ')

    @staticmethod
    def recognizes(file):
        return ElfFile.RE_FILE_TYE.match(file.magic_file_type)

    @needs_content
    def compare_details(self, other, source=None):
        return _compare_elf_data(self.path, other.path)

class StaticLibFile(File):
    RE_FILE_TYPE = re.compile(r'\bar archive\b')
    RE_FILE_EXTENSION = re.compile(r'\.a$')

    @staticmethod
    def recognizes(file):
        return StaticLibFile.RE_FILE_TYPE.search(file.magic_file_type) and StaticLibFile.RE_FILE_EXTENSION.search(file.name)

    @needs_content
    def compare_details(self, other, source=None):
        differences = []
        # look up differences in metadata
        content1 = get_ar_content(self.path)
        content2 = get_ar_content(other.path)
        differences.append(Difference.from_unicode(
                               content1, content2, self.path, other.path, source="metadata"))
        differences.extend(_compare_elf_data(self.path, other.path))
        return differences
