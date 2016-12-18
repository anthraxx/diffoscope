# -*- coding: utf-8 -*-
#
# diffoscope: in-depth comparison of files, archives, and directories
#
# Copyright © 2015 Jérémy Bobbio <lunar@debian.org>
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

import io
import os
import re
import struct
import subprocess

from diffoscope import logger, tool_required
from diffoscope.difference import Difference
from diffoscope.comparators.utils import Archive, Command
from diffoscope.comparators.binary import File


class CbfsListing(Command):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._header_re = re.compile(r'^.*: ([^,]+, bootblocksize [0-9]+, romsize [0-9]+, offset 0x[0-9A-Fa-f]+)$')

    @tool_required('cbfstool')
    def cmdline(self):
        return ['cbfstool', self.path, 'print']

    def filter(self, line):
        return self._header_re.sub('\\1', line.decode('utf-8')).encode('utf-8')


class CbfsContainer(Archive):
    @tool_required('cbfstool')
    def entries(self, path):
        cmd = ['cbfstool', path, 'print']
        output = subprocess.check_output(cmd, shell=False).decode('utf-8')
        header = True
        for line in output.rstrip('\n').split('\n'):
            if header:
                if line.startswith('Name'):
                    header = False
                continue
            name = line.split()[0]
            if name == '(empty)':
                continue
            yield name

    def open_archive(self):
        return self

    def close_archive(self):
        pass

    def get_member_names(self):
        return list(self.entries(self.source.path))

    @tool_required('cbfstool')
    def extract(self, member_name, dest_dir):
        dest_path = os.path.join(dest_dir, os.path.basename(member_name))
        cmd = ['cbfstool', self.source.path, 'extract', '-n', member_name, '-f', dest_path]
        logger.debug("cbfstool extract %s to %s", member_name, dest_path)
        subprocess.check_call(cmd, shell=False, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
        return dest_path


CBFS_HEADER_MAGIC = 0x4F524243
CBFS_HEADER_VERSION1 = 0x31313131
CBFS_HEADER_VERSION2 = 0x31313132
CBFS_HEADER_SIZE = 8 * 4 # 8 * uint32_t

# On 2015-12-15, the largest image produced by coreboot is 16 MiB
CBFS_MAXIMUM_FILE_SIZE = 24 * 2 ** 20 # 24 MiB

def is_header_valid(buf, size, offset=0):
    magic, version, romsize, bootblocksize, align, cbfs_offset, architecture, pad = struct.unpack_from('!IIIIIIII', buf, offset)
    return magic == CBFS_HEADER_MAGIC and \
           (version == CBFS_HEADER_VERSION1 or version == CBFS_HEADER_VERSION2) and \
           (romsize <= size) and \
           (cbfs_offset < romsize)


class CbfsFile(File):
    CONTAINER_CLASS = CbfsContainer

    @staticmethod
    def recognizes(file):
        size = os.stat(file.path).st_size
        if size < CBFS_HEADER_SIZE or size > CBFS_MAXIMUM_FILE_SIZE:
            return False
        with open(file.path, 'rb') as f:
            # pick at the latest byte as it should contain the relative offset of the header
            f.seek(-4, io.SEEK_END)
            # <pgeorgi> given the hardware we support so far, it looks like
            #           that field is now bound to be little endian
            #   -- #coreboot, 2015-10-14
            rel_offset = struct.unpack('<i', f.read(4))[0]
            if rel_offset < 0 and -rel_offset > CBFS_HEADER_SIZE and -rel_offset < size:
                f.seek(rel_offset, io.SEEK_END)
                logger.debug('looking for header at offset: %x', f.tell())
                if is_header_valid(f.read(CBFS_HEADER_SIZE), size):
                    return True
            elif not file.name.endswith('.rom'):
                return False
            else:
                logger.debug('CBFS relative offset seems wrong, scanning whole image')
            f.seek(0, io.SEEK_SET)
            offset = 0
            buf = f.read(CBFS_HEADER_SIZE)
            while len(buf) >= CBFS_HEADER_SIZE:
                if is_header_valid(buf, size, offset):
                    return True
                if len(buf) - offset <= CBFS_HEADER_SIZE:
                    buf = f.read(32768)
                    offset = 0
                else:
                    offset += 1
            return False

    def compare_details(self, other, source=None):
        return [Difference.from_command(CbfsListing, self.path, other.path)]
