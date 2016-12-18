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

from diffoscope import tool_required
from diffoscope.difference import Difference
from diffoscope.comparators.binary import File
from diffoscope.comparators.utils import Command


class Sqlite3Dump(Command):
    @tool_required('sqlite3')
    def cmdline(self):
        return ['sqlite3', self.path, '.dump']


class Sqlite3Database(File):
    @staticmethod
    def recognizes(file):
        return file.magic_file_type and file.magic_file_type.startswith('SQLite 3.x database')

    def compare_details(self, other, source=None):
        return [Difference.from_command(Sqlite3Dump, self.path, other.path)]

