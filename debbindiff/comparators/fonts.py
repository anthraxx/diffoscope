# -*- coding: utf-8 -*-
#
# debbindiff: highlight differences between two builds of Debian packages
#
# Copyright © 2014 Jérémy Bobbio <lunar@debian.org>
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

import locale
import subprocess
from debbindiff import tool_required
from debbindiff.comparators.utils import binary_fallback, Command
from debbindiff.difference import Difference


class Showttf(Command):
    @tool_required('showttf')
    def cmdline(self):
        return ['showttf', self.path]

    def filter(self, line):
        return line.decode('latin-1').encode('utf-8')

@binary_fallback
def compare_ttf_files(path1, path2, source=None):
    difference = Difference.from_command(Showttf, path1, path2)
    if not difference:
        return []
    return [difference]
