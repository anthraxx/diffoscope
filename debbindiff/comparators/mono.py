# -*- coding: utf-8 -*-
#
# debbindiff: highlight differences between two builds of Debian packages
#
# Copyright © 2015 Daniel Kahn Gillmor <dkg@fifthhorseman.net>
#             2015 Jérémy Bobbio <lunar@debian.org>
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

import re
from debbindiff import tool_required
from debbindiff.comparators.binary import File, needs_content
from debbindiff.comparators.utils import Command
from debbindiff.difference import Difference


class Pedump(Command):
    @tool_required('pedump')
    def cmdline(self):
        return ['pedump', self.path]


class MonoExeFile(File):
    RE_FILE_TYPE = re.compile(r'\bPE[0-9]+\b.*\bMono\b')

    @staticmethod
    def recognizes(file):
        return MonoExeFile.RE_FILE_TYPE.search(file.magic_file_type)

    @needs_content
    def compare_details(self, other, source=None):
        return [Difference.from_command(Pedump, self.path, other.path)]
