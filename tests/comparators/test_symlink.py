# -*- coding: utf-8 -*-
#
# diffoscope: in-depth comparison of files, archives, and directories
#
# Copyright © 2017 Chris Lamb <lamby@debian.org>
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

import os

from diffoscope.comparators.binary import FilesystemFile
from diffoscope.comparators.utils.specialize import specialize

from utils.data import get_data


def test_destination(tmpdir):
    def create(x):
        path = os.path.join(str(tmpdir.mkdir(x)), 'src')
        os.symlink('/{}'.format(x), path)
        return specialize(FilesystemFile(path))

    a = create('a')
    b = create('b')

    expected_diff = get_data('symlink_expected_destination_diff')

    assert a.compare(b).unified_diff == expected_diff
