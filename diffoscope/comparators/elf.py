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

import os
import re
import logging
import subprocess
import collections

from diffoscope.exc import OutputParsingError
from diffoscope.tools import tool_required
from diffoscope.tempfiles import get_named_temporary_file
from diffoscope.difference import Difference

from .deb import DebFile, get_build_id_map
from .utils.file import File
from .utils.command import Command
from .utils.container import Container
from .utils.libarchive import list_libarchive

DEBUG_SECTION_GROUPS = (
    'rawline',
    'info',
    'abbrev',
    'pubnames',
    'aranges',
    'macro',
    'frames',
    'loc',
    'ranges',
    'pubtypes',
    'trace_info',
    'trace_abbrev',
    'trace_aranges',
    'gdb_index',
)

logger = logging.getLogger(__name__)


class Readelf(Command):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # we don't care about the name of the archive
        self._archive_re = re.compile(r'^File: %s\(' % re.escape(self.path))

    @tool_required('readelf')
    def cmdline(self):
        return ['readelf', '--wide'] + self.readelf_options() + [self.path]

    def readelf_options(self):
        return []  # noqa

    def filter(self, line):
        try:
            # we don't care about the name of the archive
            line = self._archive_re.sub('File: lib.a(', line.decode('utf-8'))
            # the full path can appear in the output, we need to remove it
            return line.replace(self.path, '<elf>').encode('utf-8')
        except UnicodeDecodeError:
            return line

    @staticmethod
    def should_skip_section(section_name, section_type):
        return False


class ReadelfFileHeader(Readelf):
    def readelf_options(self):
        return ['--file-header']


class ReadelfProgramHeader(Readelf):
    def readelf_options(self):
        return ['--program-header']


class ReadelfSections(Readelf):
    def readelf_options(self):
        return ['--sections']


class ReadelfSymbols(Readelf):
    def readelf_options(self):
        return ['--symbols']

    @staticmethod
    def should_skip_section(section_name, section_type):
        return section_type in {'DYNSYM', 'SYMTAB'}


class ReadelfRelocs(Readelf):
    def readelf_options(self):
        return ['--relocs']

    @staticmethod
    def should_skip_section(section_name, section_type):
        return section_type in {'REL', 'RELA'}


class ReadelfDynamic(Readelf):
    def readelf_options(self):
        return ['--dynamic']

    @staticmethod
    def should_skip_section(section_name, section_type):
        return section_type == 'DYNAMIC'


class ReadelfNotes(Readelf):
    def readelf_options(self):
        return ['--notes']

    @staticmethod
    def should_skip_section(section_name, section_type):
        return section_type == 'NOTE'


class RedaelfVersionInfo(Readelf):
    def readelf_options(self):
        return ['--version-info']

    @staticmethod
    def should_skip_section(section_name, section_type):
        return section_type in {'VERDEF', 'VERSYM', 'VERNEED'}


class ReadelfDebugDump(Readelf):
    def __new__(cls, *args, **kwargs):
        # Find the section group from the class name
        debug_section_group = cls.__name__[len('ReadelfDebugDump_'):]
        if debug_section_group:
            return ReadelfDebugDump(debug_section_group, *args, **kwargs)
        return super(Readelf, cls).__new__(cls)

    def __init__(self, debug_section_group, *args, **kwargs):
        self._debug_section_group = debug_section_group
        super().__init__(*args, **kwargs)

    def readelf_options(self):
        return ['--debug-dump=%s' % self._debug_section_group]


READELF_DEBUG_DUMP_COMMANDS = [
    type('ReadelfDebugDump_{}'.format(x), (ReadelfDebugDump,), {})
    for x in DEBUG_SECTION_GROUPS
]


class ReadElfSection(Readelf):
    @staticmethod
    def base_options():
        if not hasattr(ReadElfSection, '_base_options'):
            output = subprocess.check_output(
                ['readelf', '--help'],
                shell=False,
                stderr=subprocess.DEVNULL,
            ).decode('us-ascii', errors='replace')

            ReadElfSection._base_options = []
            for x in ('--decompress',):
                if x in output:
                    ReadElfSection._base_options.append(x)
        return ReadElfSection._base_options

    def __init__(self, path, section_name, *args, **kwargs):
        self._path = path
        self._section_name = section_name
        super().__init__(path, *args, **kwargs)

    @property
    def section_name(self):
        return self._section_name

    def readelf_options(self):
        return ReadElfSection.base_options() + ['--hex-dump={}'.format(self.section_name)]

class ReadelfStringSection(ReadElfSection):
    def readelf_options(self):
        return ReadElfSection.base_options() + ['--string-dump={}'.format(self.section_name)]

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
        return [
            'objdump',
        ] + self.objdump_options() + [
            '--section={}'.format(self._section_name),
            self.path,
        ]

    def filter(self, line):
        # Remove the filename from the output
        if line.startswith(self._path_bin + b':'):
            return b''
        if line.startswith(b'In archive'):
            return b''

        return line

class ObjdumpDisassembleSection(ObjdumpSection):
    RE_SYMBOL_COMMENT = re.compile(rb'^( +[0-9a-f]+:[^#]+)# [0-9a-f]+ <[^>]+>$')

    def objdump_options(self):
        # With '--line-numbers' we get the source filename and line within the
        # disassembled instructions.
        # objdump can get the debugging information from the elf or from the
        # stripped symbols file specified in the .gnu_debuglink section
        return ['--line-numbers', '--disassemble', '--demangle']

    def filter(self, line):
        line = super().filter(line)
        return ObjdumpDisassembleSection.RE_SYMBOL_COMMENT.sub(r'\1', line)


READELF_COMMANDS = (
    ReadelfFileHeader,
    ReadelfProgramHeader,
    ReadelfSections,
    ReadelfSymbols,
    ReadelfRelocs,
    ReadelfDynamic,
    ReadelfNotes,
    RedaelfVersionInfo,
)

def _compare_elf_data(path1, path2):
    return [
        Difference.from_command(x, path1, path2)
        for x in list(READELF_COMMANDS) + READELF_DEBUG_DUMP_COMMANDS
    ]


def _should_skip_section(name, type):
    for x in READELF_COMMANDS:
        if x.should_skip_section(name, type):
            logger.debug("Skipping section %s, covered by %s", name, x)
            return True
    if name.startswith('.debug') or name.startswith('.zdebug'):
        # section .debug_str looks much nicer with `readelf --string-dump`
        # the rest is handled by READELF_DEBUG_DUMP_COMMANDS
        return not name.endswith('_str')
    return False


class ElfSection(File):
    def __init__(self, elf_container, member_name):
        super().__init__(container=elf_container)
        self._name = member_name

    @property
    def name(self):
        return self._name

    @property
    def progress_name(self):
        return "{} [{}]".format(
            self.container.source.progress_name,
            super().progress_name,
        )

    @property
    def path(self):
        return self.container.source.path

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

    @property
    def fuzzy_hash(self):
        return None

    @staticmethod
    def recognizes(file):
        # No file should be recognized as an elf section
        return False

    def compare(self, other, source=None):
        return Difference.from_command(
            ReadElfSection,
            self.path,
            other.path,
            command_args=[self._name],
        )

class ElfCodeSection(ElfSection):
    def compare(self, other, source=None):
        return Difference.from_command(
            ObjdumpDisassembleSection,
            self.path,
            other.path,
            command_args=[self._name],
        )

class ElfStringSection(ElfSection):
    def compare(self, other, source=None):
        return Difference.from_command(
            ReadelfStringSection,
            self.path,
            other.path,
            command_args=[self._name],
        )


@tool_required('readelf')
def get_build_id(path):
    try:
        output = subprocess.check_output(
            ['readelf', '--notes', path],
            stderr=subprocess.DEVNULL,
        )
    except subprocess.CalledProcessError as e:
        logger.debug("Unable to get Build ID for %s: %s", path, e)
        return None

    m = re.search(r'^\s+Build ID: ([0-9a-f]+)$', output.decode('utf-8'), flags=re.MULTILINE)
    if not m:
        return None

    return m.group(1)


@tool_required('readelf')
def get_debug_link(path):
    try:
        output = subprocess.check_output(
            ['readelf', '--string-dump=.gnu_debuglink', path],
            stderr=subprocess.DEVNULL,
        )
    except subprocess.CalledProcessError as e:
        logger.debug("Unable to get Build Id for %s: %s", path, e)
        return None

    m = re.search(r'^\s+\[\s+0\]\s+(\S+)$', output.decode('utf-8', errors='replace'), flags=re.MULTILINE)
    if not m:
        return None

    return m.group(1)


class ElfContainer(Container):
    SECTION_FLAG_MAPPING = {
        'X': ElfCodeSection,
        'S': ElfStringSection,
        '_': ElfSection,
    }

    @tool_required('readelf')
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        logger.debug("Creating ElfContainer for %s", self.source.path)

        cmd = ['readelf', '--wide', '--section-headers', self.source.path]
        output = subprocess.check_output(cmd, shell=False, stderr=subprocess.DEVNULL)
        has_debug_symbols = False

        try:
            output = output.decode('utf-8').split('\n')
            if output[1].startswith('File:'):
                output = output[2:]
            output = output[5:]

            # Entries of readelf --section-headers have the following columns:
            # [Nr]  Name  Type  Address  Off  Size  ES  Flg  Lk  Inf  Al
            self._sections = collections.OrderedDict()
            for line in output:
                if line.startswith('Key to Flags'):
                    break

                # Strip number column because there may be spaces in the brakets
                line = line.split(']', 1)[1].split()
                name, type, flags = line[0], line[1], line[6] + '_'

                if name.startswith('.debug') or name.startswith('.zdebug'):
                    has_debug_symbols = True

                if _should_skip_section(name, type):
                    continue

                # Use first match, with last option being '_' as fallback
                elf_class = [
                    ElfContainer.SECTION_FLAG_MAPPING[x]
                    for x in flags if x in ElfContainer.SECTION_FLAG_MAPPING
                ][0]

                logger.debug("Adding section %s (%s) as %s", name, type, elf_class)
                self._sections[name] = elf_class(self, name)

        except Exception as e:
            command = ' '.join(cmd)
            logger.debug(
                "OutputParsingError in %s from `%s` output - %s:%s",
                self.__class__.__name__, command, e.__class__.__name__, e,
            )
            raise OutputParsingError(command, self)

        if not has_debug_symbols:
            self._install_debug_symbols()

    @tool_required('objcopy')
    def _install_debug_symbols(self):
        # Figure out if we are in a Debian package first
        try:
            deb = self.source.container.source.container.source.container.source
        except AttributeError:
            return

        # It needs to be a .deb and we need access a to a -dbgsym package in
        # the same .changes, directory or archive
        if not isinstance(deb, DebFile) or not deb.container:
            return

        # Retrieve the Build ID for the ELF file we are examining
        build_id = get_build_id(self.source.path)
        debuglink = get_debug_link(self.source.path)
        if not build_id or not debuglink:
            return

        logger.debug(
            "Looking for a dbgsym package for Build Id %s (debuglink: %s)",
            build_id,
            debuglink,
        )

        # Build a map of Build-Ids if it doesn't exist yet
        if not hasattr(deb.container, 'dbgsym_build_id_map'):
            deb.container.dbgsym_build_id_map = get_build_id_map(deb.container)

        if not build_id in deb.container.dbgsym_build_id_map:
            logger.debug('Unable to find a matching debug package for Build Id %s', build_id)
            return

        dbgsym_package = deb.container.dbgsym_build_id_map[build_id]
        debug_file_path = './usr/lib/debug/.build-id/{0}/{1}.debug'.format(
            build_id[:2],
            build_id[2:],
        )
        debug_file = dbgsym_package.as_container.data_tar.as_container.lookup_file(debug_file_path)
        if not debug_file:
            logger.debug('Unable to find the matching debug file %s in %s', debug_file_path, dbgsym_package)
            return

        # Create a .debug directory and link the debug symbols there with the
        # right name
        dest_path = os.path.join(
            os.path.dirname(self.source.path),
            '.debug',
            os.path.basename(debuglink),
        )
        os.makedirs(os.path.dirname(dest_path), exist_ok=True)

        def objcopy(*args):
            subprocess.check_call(
                ('objcopy',) + args,
                shell=False,
                stderr=subprocess.DEVNULL,
        )

        # If #812089 was fixed, we would just do os.link(debug_file.path,
        # dest_path) but for now, we need to do more complicated things…
        # 1. Use objcopy to create a file with only the original .gnu_debuglink
        # section as we will have to update it to get the CRC right.
        debuglink_path = get_named_temporary_file(
            prefix='{}.debuglink.'.format(self.source.path),
        ).name

        objcopy('--only-section=.gnu_debuglink', self.source.path, debuglink_path)

        # 2. Monkey-patch the ElfSection object created for the .gnu_debuglink
        # to change the path to point to this new file
        section = self._sections['.gnu_debuglink']
        class MonkeyPatchedElfSection(section.__class__):
            @property
            def path(self):
                return debuglink_path
        section.__class__ = MonkeyPatchedElfSection

        # 3. Create a file with the debug symbols in uncompressed form
        objcopy('--decompress-debug-sections', debug_file.path, dest_path)

        # 4. Update the .gnu_debuglink to this new file so we get the CRC right
        objcopy('--remove-section=.gnu_debuglink', self.source.path)
        objcopy('--add-gnu-debuglink={}'.format(dest_path), self.source.path)

        logger.debug('Installed debug symbols at %s', dest_path)

    def get_member_names(self):
        return self._sections.keys()

    def get_member(self, member_name):
        return self._sections[member_name]

class ElfFile(File):
    CONTAINER_CLASS = ElfContainer
    RE_FILE_TYPE = re.compile(r'^ELF ')

    def compare_details(self, other, source=None):
        return _compare_elf_data(self.path, other.path)

class StaticLibFile(File):
    CONTAINER_CLASS = ElfContainer
    RE_FILE_TYPE = re.compile(r'\bar archive\b')
    RE_FILE_EXTENSION = re.compile(r'\.a$')

    @staticmethod
    def recognizes(file):
        return StaticLibFile.RE_FILE_TYPE.search(file.magic_file_type) and \
            StaticLibFile.RE_FILE_EXTENSION.search(file.name)

    def compare_details(self, other, source=None):
        differences = [Difference.from_text_readers(
            list_libarchive(self.path),
            list_libarchive(other.path),
            self.path,
            other.path,
            source="file list",
        )]
        differences.extend(_compare_elf_data(self.path, other.path))
        return differences
