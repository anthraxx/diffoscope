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

import re
import subprocess

from diffoscope import tool_required
from diffoscope.difference import Difference
from diffoscope.comparators.utils import Command
from diffoscope.comparators.binary import File
from diffoscope.comparators.libarchive import LibarchiveContainer


@tool_required('isoinfo')
def get_iso9660_names(path):
    # We always use RockRidge for names. Let's see if this proves
    # problematic later
    cmd = ['isoinfo', '-R', '-f', '-i', path]
    return subprocess.check_output(cmd, shell=False).strip().split('\n')


class ISO9660PVD(Command):
    @tool_required('isoinfo')
    def cmdline(self):
        return ['isoinfo', '-d', '-i', self.path]


class ISO9660Listing(Command):
    def __init__(self, path, extension=None, *args, **kwargs):
        self._extension = extension
        super().__init__(path, *args, **kwargs)

    @tool_required('isoinfo')
    def cmdline(self):
        cmd = ['isoinfo', '-l', '-i', self.path]
        if self._extension == 'joliet':
            cmd.extend(['-J', '-j', 'iso8859-15'])
        elif self._extension == 'rockridge':
            cmd.extend(['-R'])
        return cmd

    def filter(self, line):
        if self._extension == 'joliet':
            return line.decode('iso-8859-15').encode('utf-8')
        else:
            return line


class Iso9660File(File):
    CONTAINER_CLASS = LibarchiveContainer
    RE_FILE_TYPE = re.compile(r'\bISO 9660\b')

    @staticmethod
    def recognizes(file):
        return Iso9660File.RE_FILE_TYPE.search(file.magic_file_type)

    def compare_details(self, other, source=None):
        differences = []
        differences.append(Difference.from_command(ISO9660PVD, self.path, other.path))
        differences.append(Difference.from_command(ISO9660Listing, self.path, other.path))
        for extension in ('joliet', 'rockridge'):
            try:
                differences.append(Difference.from_command(ISO9660Listing, self.path, other.path, command_args=(extension,)))
            except subprocess.CalledProcessError:
                pass # probably no joliet or rockridge data
        return differences
