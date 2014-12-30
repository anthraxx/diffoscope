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

import subprocess
from debbindiff.comparators.utils import binary_fallback
from debbindiff.difference import Difference


def sng(path):
    with open(path) as f:
        p = subprocess.Popen(['sng'], shell=False, close_fds=True,
                             stdin=f, stdout=subprocess.PIPE)
        out, err = p.communicate()
        p.wait()
        if p.returncode != 0:
            return 'sng exited with error %d\n%s' % (p.returncode, err)
        return out

@binary_fallback
def compare_png_files(path1, path2, source=None):
    sng1 = sng(path1)
    sng2 = sng(path2)
    if sng1 != sng2:
        return [Difference(sng1.splitlines(1), sng2.splitlines(1),
                           path1, path2, source='sng')]
    return []

