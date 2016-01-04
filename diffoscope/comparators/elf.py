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
import subprocess
from diffoscope import tool_required, OutputParsingError
from diffoscope import logger
from diffoscope.comparators.binary import File
from diffoscope.comparators.utils import get_ar_content, Command, Container
from diffoscope.difference import Difference


class Readelf(Command):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # we don't care about the name of the archive
        self._archive_re = re.compile(r'^File: %s\(' % re.escape(self.path))

    @tool_required('readelf')
    def cmdline(self):
        return ['readelf', '--wide'] + self.readelf_options() + [self.path]

    def readelf_options(self):
        return []

    def filter(self, line):
        try:
            # we don't care about the name of the archive
            line = self._archive_re.sub('File: lib.a(', line.decode('utf-8'))
            # the full path can appear in the output, we need to remove it
            return line.replace(self.path, '<elf>').encode('utf-8')
        except UnicodeDecodeError:
            return line

class ReadelfAll(Readelf):
    def readelf_options(self):
        return ['--all']

class ReadelfDebugDump(Readelf):
    def readelf_options(self):
        return ['--debug-dump']

class ReadElfSection(Readelf):
    def __init__(self, path, section_name, *args, **kwargs):
        self._path = path
        self._section_name = section_name
        super().__init__(path, *args, **kwargs)

    def readelf_options(self):
        return ['--hex-dump']

    @tool_required('readelf')
    def cmdline(self):
        return ['readelf', '--wide'] + self.readelf_options() + \
            [self._section_name, self.path]

class ReadelfStringSection(ReadElfSection):
    def readelf_options(self):
        return ['--string-dump']

class ObjdumpSection(Command):
    def __init__(self, path, section_name, *args, **kwargs):
        self._path = path
        self._path_bin = path.encode('utf-8')
        self._section_name = section_name
        super().__init__(path, *args, **kwargs)

    def objdump_options(self):
        return []

    @tool_required('objdump')
    def cmdline(self):
        return ['objdump'] + self.objdump_options() + \
            ['--section='+self._section_name, self.path]

    def filter(self, line):
        # Remove the filename from the output
        if line.startswith(self._path_bin + b':'):
            return b''
        if line.startswith(b'In archive'):
            return b''
        return line

class ObjdumpDisassembleSection(ObjdumpSection):
    def objdump_options(self):
        # With '--line-numbers' we get the source filename and line within the
        # disassembled instructions.
        # objdump can get the debugging information from the elf or from the
        # stripped symbols file specified in the .gnu_debuglink section
        return ['--line-numbers', '--disassemble']

def _compare_elf_data(path1, path2):
    return [Difference.from_command(ReadelfAll, path1, path2),
            Difference.from_command(ReadelfDebugDump, path1, path2)]

class ElfSection(File):
    def __init__(self, elf_container, member_name):
        self._elf_container = elf_container
        self._name = member_name

    @property
    def name(self):
        return self._name

    @property
    def path(self):
        raise NotImplementedError('elf sections cannot be extracted')
        #return self._elf_container.source.path

    def cleanup(self):
        pass

    def is_directory(self):
        return False

    def is_symlink(self):
        return False

    def is_device(self):
        return False

    def has_same_content_as(self, other):
        # Always force diff of the section
        return False

    @staticmethod
    def recognizes(file):
        # No file should be recognized as an elf section
        return False

    def compare(self, other, source=None):
        return Difference.from_command(ReadElfSection,
                self._elf_container.source.path,
                other._elf_container.source.path,
                command_args=[self._name])

class ElfCodeSection(ElfSection):
    def compare(self, other, source=None):
        return Difference.from_command(ObjdumpDisassembleSection,
                self._elf_container.source.path,
                other._elf_container.source.path,
                command_args=[self._name])

class ElfStringSection(ElfSection):
    def compare(self, other, source=None):
        return Difference.from_command(ReadelfStringSection,
                self._elf_container.source.path,
                other._elf_container.source.path,
                command_args=[self._name])


class ElfContainer(Container):
    SECTION_TYPES = {'X': ElfCodeSection, 'S': ElfStringSection, '_': ElfSection}

    @tool_required('readelf')
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        logger.debug('creating ElfContainer for file %s', self.source.path)
        cmd = ['readelf', '--wide', '--section-headers', self.source.path]
        output = subprocess.check_output(cmd, shell=False)

        try:
            output = output.decode('utf-8').split('\n')
            if output[1].startswith('File:'):
                output = output[2:]
            output = output[5:]

            self._sections = {}
            self._section_list = [] # using a list to store original order
            # Entires of readelf --section-headers have the following columns:
            # [Nr]  Name  Type  Address  Off  Size  ES  Flg  Lk  Inf  Al
            for line in output:
                if line.startswith('Key to Flags'):
                    break
                # Strip number column because there may be spaces in the brakets
                line = line.split(']', 1)[1].split()
                name, flag = line[0], line[6] + '_'
                # Use first match, with last option being '_' as fallback
                type = [ElfContainer.SECTION_TYPES[type] for type in flag if \
                        type in ElfContainer.SECTION_TYPES][0]
                self._sections[name] = type
                self._section_list.append(name)
                logger.debug('adding %s section as %s', name, type)
        except Exception as e:
            command = ' '.join(cmd)
            logger.debug('OutputParsingError in %s from `%s` output - %s:%s'
                    % (self.__class__.__name__, command, e.__class__.__name__, e))
            raise OutputParsingError(command, self)

    def get_member_names(self):
        return self._section_list

    def get_member(self, member_name):
        return self._sections[member_name](self, member_name)

class ElfFile(File):
    CONTAINER_CLASS = ElfContainer
    RE_FILE_TYE = re.compile(r'^ELF ')

    @staticmethod
    def recognizes(file):
        return ElfFile.RE_FILE_TYE.match(file.magic_file_type)

    def compare_details(self, other, source=None):
        return _compare_elf_data(self.path, other.path)

class StaticLibFile(File):
    CONTAINER_CLASS = ElfContainer
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
