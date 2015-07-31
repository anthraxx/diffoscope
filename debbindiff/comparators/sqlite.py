# -*- coding: utf-8 -*-
#
# debbindiff: highlight differences between two builds of Debian packages
#
# Copyright © 2015 Jérémy Bobbio <lunar@debian.org>
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

from debbindiff import tool_required
from debbindiff.comparators.binary import File, needs_content
from debbindiff.comparators.utils import Command
from debbindiff.difference import Difference


class Sqlite3Dump(Command):
    @tool_required('sqlite3')
    def cmdline(self):
        return ['sqlite3', self.path, '.dump']


class Sqlite3Database(File):
    @staticmethod
    def recognizes(file):
        return file.magic_file_type == 'SQLite 3.x database'

    @needs_content
    def compare_details(self, other, source=None):
        return [Difference.from_command(Sqlite3Dump, self.path, other.path)]

