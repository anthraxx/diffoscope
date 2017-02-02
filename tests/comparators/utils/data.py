# -*- coding: utf-8 -*-
#
# diffoscope: in-depth comparison of files, archives, and directories
#
# Copyright © 2015      Jérémy Bobbio <lunar@debian.org>
#             2016-2017 Mattia Rizzolo <mattia@debian.org>
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
import pytest

from diffoscope.comparators.binary import FilesystemFile
from diffoscope.comparators.utils.specialize import specialize


def init_fixture(filename):
    return pytest.fixture(
        lambda: specialize(FilesystemFile(filename))
    )


def data(filename):
    return os.path.join(
        os.path.dirname(os.path.dirname(__file__)),
        '..',
        'data',
        filename,
    )


def get_data(filename):
    with open(data(filename), encoding='utf-8') as f:
        return f.read()


def load_fixture(filename):
    return init_fixture(data(filename))
