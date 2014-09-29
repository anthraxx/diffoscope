# -*- coding: utf-8 -*-
#
# debbindiff: highlight differences between two builds of Debian packages
#
# Copyright © 2014 Jérémy Bobbio <lunar@debian.org>
#
# debdindiff is free software: you can redistribute it and/or modify
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
from debbindiff.pyxxd import hexdump

def compare_binary_files(path1, path2, source=None):
    hexdump1 = hexdump(open(path1, 'rb').read())
    hexdump2 = hexdump(open(path2, 'rb').read())
    if hexdump1 == hexdump2:
        return []
    return [Difference(hexdump1.splitlines(1), hexdump2.splitlines(1), path1, path2, source)]


