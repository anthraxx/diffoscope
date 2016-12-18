# -*- coding: utf-8 -*-
#
# diffoscope: in-depth comparison of files, archives, and directories
#
# Copyright © 2016 Chris Lamb <lamby@debian.org>
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
import os
import struct
import binascii

from diffoscope.difference import Difference
from diffoscope.comparators.binary import File


class GitIndexFile(File):
    RE_FILE_TYPE = re.compile(r'^Git index')

    @staticmethod
    def recognizes(file):
        return GitIndexFile.RE_FILE_TYPE.match(file.magic_file_type)

    def compare_details(self, other, source=None):
        return [Difference.from_text(
            describe_index(self.path),
            describe_index(other.path),
            self.path,
            other.path,
        )]

def parse_index(f):
    _, version = struct.unpack('>LL', f.read(4 * 2))

    return {
        'version': version,
        'entries': list(parse_entries(f)),
    }

def parse_entries(f):
    num_entries = struct.unpack('>L', f.read(4))[0]

    for _ in range(num_entries):
        x = {}

        pos = f.tell()

        x['ctime'], x['ctime_nano'], x['mtime'], x['mtime_nano'], \
                x['dev'], x['inode'], x['mode'], x['uid'], x['gid'], \
                x['size'], x['sha'], x['flags'] = \
            struct.unpack('>LLLLLLLLLL20sH', f.read((4 * 10) + 20 + 2))

        x['path'] = f.read(x['flags'] & 0x0fff)

        f.read((pos + ((f.tell() - pos + 8) & ~7)) - f.tell())

        yield x

def describe_index(filename):
    with open(filename, 'rb') as f:
        index = parse_index(f)

    return """
Version: {version}

Entries:
{entries_fmt}
""".format(
    entries_fmt=''.join(describe_entry(x) for x in index['entries']),
    **index
)

def describe_entry(x):
    return """
Path:      {x[path]}
SHA:       {hexsha}
Size:      {x[size]}
Flags:     {x[flags]:#b}
User ID:   {x[uid]}
Group ID:  {x[gid]}
Created:   {x[ctime]}.{x[ctime_nano]}
Modified:  {x[mtime]}.{x[mtime_nano]}
Inode:     {x[inode]}
Device ID: ({major}, {minor})
""".format(
    x=x,
    major=os.major(x['dev']),
    minor=os.minor(x['dev']),
    hexsha=binascii.b2a_hex(x['sha']).decode('utf-8'),
)
