# -*- coding: utf-8 -*-
#
# diffoscope: in-depth comparison of files, archives, and directories
#
# Copyright © 2015 Daniel Kahn Gillmor <dkg@fifthhorseman.net>
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

from diffoscope.config import Config
from diffoscope.comparators.mono import MonoExeFile
from diffoscope.comparators.binary import NonExistingFile

from utils import skip_unless_tools_exist, data, load_fixture

# these were generated with:

# echo 'public class Test { static public void Main () {} }' > test.cs
# mcs -out:test1.exe test.cs ; sleep 2; mcs -out:test2.exe test.cs

exe1 = load_fixture(data('test1.exe'))
exe2 = load_fixture(data('test2.exe'))

def test_identification(exe1):
    assert isinstance(exe1, MonoExeFile)

def test_no_differences(exe1):
    difference = exe1.compare(exe1)
    assert difference is None

@pytest.fixture
def differences(exe1, exe2):
    return exe1.compare(exe2).details

@skip_unless_tools_exist('pedump')
def test_diff(differences):
    expected_diff = open(data('pe_expected_diff')).read()
    assert differences[0].unified_diff == expected_diff

@skip_unless_tools_exist('pedump')
def test_compare_non_existing(monkeypatch, exe1):
    monkeypatch.setattr(Config(), 'new_file', True)
    difference = exe1.compare(NonExistingFile('/nonexisting', exe1))
    assert difference.source2 == '/nonexisting'
    assert len(difference.details) > 0
