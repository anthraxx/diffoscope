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

import os.path
import subprocess
from debbindiff.difference import Difference
import debbindiff.comparators


def ls(path):
    return subprocess.check_output(['ls', '-l', path], shell=False).decode('utf-8')


def compare_directories(path1, path2):
    differences = []
    for name in sorted(set(os.listdir(path1)).intersection(os.listdir(path2))):
        in_path1 = os.path.join(path1, name)
        in_path2 = os.path.join(path2, name)
        differences.extend(debbindiff.comparators.compare_files(
                               in_path1, in_path2, source=name))
    ls1 = ls(path1)
    ls2 = ls(path2)
    if ls1 != ls2:
        differences.append(Difference(
            ls1.splitlines(1), ls2.splitlines(2),
            path1, path2, source="ls -l"))
    if differences:
        d = Difference(None, None, path1, path2)
        d.add_details(differences)
        return [d]
    return []
