# -*- coding: utf-8 -*-
#
# diffoscope: in-depth comparison of files, archives, and directories
#
# Copyright © 2014-2015 Jérémy Bobbio <lunar@debian.org>
# Copyright © 2015 Clemens Lang <cal@macports.org>
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
import subprocess

from diffoscope import tool_required
from diffoscope.difference import Difference
from diffoscope.comparators.utils import Command
from diffoscope.comparators.binary import File


class Otool(Command):
    def __init__(self, path, arch, *args, **kwargs):
        self._path = path
        self._arch = arch
        super().__init__(path, *args, **kwargs)

    @tool_required('otool')
    def cmdline(self):
        return ['otool'] + self.otool_options() + [self.path]

    def otool_options(self):
        return ['-arch', self._arch]

    def filter(self, line):
        try:
            # Strip the filename itself, it's in the first line on its own, terminated by a colon
            if line and line.decode('utf-8').strip() == self._path + ':':
                return b""
            return line
        except UnicodeDecodeError:
            return line


class OtoolHeaders(Otool):
    def otool_options(self):
        return super().otool_options() + ['-h']


class OtoolLibraries(Otool):
    def otool_options(self):
        return super().otool_options() + ['-L']


class OtoolDisassemble(Otool):
    def otool_options(self):
        return super().otool_options() + ['-tdvV']


class MachoFile(File):
    RE_FILE_TYPE = re.compile(r'^Mach-O ')
    RE_EXTRACT_ARCHS = re.compile(r'^(?:Architectures in the fat file: .* are|Non-fat file: .* is architecture): (.*)$')

    @staticmethod
    def recognizes(file):
        return MachoFile.RE_FILE_TYPE.match(file.magic_file_type)

    @staticmethod
    @tool_required('lipo')
    def get_arch_from_macho(path):
        lipo_output = subprocess.check_output(['lipo', '-info', path]).decode('utf-8')
        lipo_match = MachoFile.RE_EXTRACT_ARCHS.match(lipo_output)
        if lipo_match is None:
            raise ValueError('lipo -info on Mach-O file %s did not produce expected output. Output was: %s' % path, lipo_output)
        return lipo_match.group(1).split()

    def compare_details(self, other, source=None):
        differences = []
        # Check for fat binaries, trigger a difference if the architectures differ
        my_archs = MachoFile.get_arch_from_macho(self.path)
        other_archs = MachoFile.get_arch_from_macho(other.path)

        differences.append(Difference.from_text('\n'.join(my_archs),
                                                '\n'.join(other_archs),
                                                self.name, other.name, source='architectures'))

        # Compare common architectures for differences
        for common_arch in set(my_archs) & set(other_archs):
            differences.append(Difference.from_command(OtoolHeaders, self.path, other.path, command_args=[common_arch],
                                                       comment="Mach-O headers for architecture %s" % common_arch))
            differences.append(Difference.from_command(OtoolLibraries, self.path, other.path, command_args=[common_arch],
                                                       comment="Mach-O load commands for architecture %s" % common_arch))
            differences.append(Difference.from_command(OtoolDisassemble, self.path, other.path, command_args=[common_arch],
                                                       comment="Code for architecture %s" % common_arch))

        return differences
