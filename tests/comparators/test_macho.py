# -*- coding: utf-8 -*-
#
# diffoscope: in-depth comparison of files, archives, and directories
#
# Copyright © 2015 Jérémy Bobbio <lunar@debian.org>
# Copyright © 2015 Clemens Lang <cal@macports.org>
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

import pytest
import os.path

from diffoscope.config import Config
from diffoscope.comparators.macho import MachoFile
from diffoscope.comparators.binary import NonExistingFile

from utils import skip_unless_tools_exist, data, load_fixture

obj1 = load_fixture(data('test1.macho'))
obj2 = load_fixture(data('test2.macho'))

def test_obj_identification(obj1):
    assert isinstance(obj1, MachoFile)

def test_obj_no_differences(obj1):
    difference = obj1.compare(obj1)
    assert difference is None

@pytest.fixture
def obj_differences(obj1, obj2):
    return obj1.compare(obj2).details

@skip_unless_tools_exist('otool', 'lipo')
def test_obj_compare_non_existing(monkeypatch, obj1):
    monkeypatch.setattr(Config(), 'new_file', True)
    difference = obj1.compare(NonExistingFile('/nonexisting', obj1))
    assert difference.source2 == '/nonexisting'
    assert len(difference.details) > 0

@skip_unless_tools_exist('otool', 'lipo')
def test_diff(obj_differences):
    assert len(obj_differences) == 4
    l = ['macho_expected_diff_arch', 'macho_expected_diff_headers', 'macho_expected_diff_loadcommands', 'macho_expected_diff_disassembly']
    for idx, diff in enumerate(obj_differences):
        with open(os.path.join(os.path.dirname(__file__), '../data', l[idx]), 'w') as f:
            print(diff.unified_diff, file=f)
    expected_diff = open(data('macho_expected_diff')).read()
    assert obj_differences[0].unified_diff == expected_diff
