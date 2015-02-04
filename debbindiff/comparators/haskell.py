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

import subprocess
from debbindiff.comparators.utils import binary_fallback
from debbindiff.difference import Difference


def show_iface(path):
    return subprocess.check_output(['ghc', '--show-iface', path], shell=False)


@binary_fallback
def compare_hi_files(path1, path2, source=None):
    iface1 = show_iface(path1)
    iface2 = show_iface(path2)
    if iface1 != iface2:
        return [Difference(iface1.splitlines(1), iface2.splitlines(1),
                           path1, path2, source='ghc --show-iface')]
    return []
