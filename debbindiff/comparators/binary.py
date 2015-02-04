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

from debbindiff.difference import Difference
import subprocess


def get_hexdump(path):
    return subprocess.check_output(['xxd', path], shell=False)


def compare_binary_files(path1, path2, source=None):
    hexdump1 = get_hexdump(path1)
    hexdump2 = get_hexdump(path2)
    if hexdump1 == hexdump2:
        return []
    return [Difference(hexdump1.splitlines(1), hexdump2.splitlines(1),
                       path1, path2, source)]
