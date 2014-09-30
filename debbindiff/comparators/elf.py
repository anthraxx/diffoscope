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

import os.path
import re
import subprocess
from debbindiff.comparators.utils import binary_fallback
from debbindiff.difference import Difference

def readelf_all(path):
    return subprocess.check_output(['readelf', '--all', path], shell=False)

def readelf_debug_dump(path):
    return subprocess.check_output(['readelf', '--debug-dump', path], shell=False)

def objdump_disassemble(path):
    output = subprocess.check_output(['objdump', '--disassemble', path], shell=False)
    # the full path appears in the output, we need to remove it
    return re.sub(re.escape(path), os.path.basename(path), output)

@binary_fallback
def compare_elf_files(path1, path2, source=None):
    differences = []
    all1 = readelf_all(path1)
    all2 = readelf_all(path2)
    if all1 != all2:
        differences.append(Difference(all1.splitlines(1), all2.splitlines(1), path1, path2, source='readelf --all'))
    debug_dump1 = readelf_debug_dump(path1)
    debug_dump2 = readelf_debug_dump(path2)
    if debug_dump1 != debug_dump2:
        differences.append(Difference(debug_dump1.splitlines(1), debug_dump2.splitlines(1), path1, path2, source='readelf --debug-dump'))
    objdump1 = objdump_disassemble(path1)
    objdump2 = objdump_disassemble(path2)
    if objdump1 != objdump2:
        differences.append(Difference(objdump1.splitlines(1), objdump2.splitlines(1), path1, path2, source='objdump --disassemble'))
    return differences
