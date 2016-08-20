# -*- coding: utf-8 -*-
#
# diffoscope: in-depth comparison of files, archives, and directories
#
# Copyright © 2016 Chris Lamb <lamby@debian.org>
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
# along with diffoscope.  If not, see <http://www.gnu.org/licenses/>.

import pytest

from diffoscope.comparators import specialize
from diffoscope.comparators.binary import FilesystemFile
from diffoscope.comparators.haskell import HiFile

from conftest import data

TEST_FILE1_PATH = data('test1.hi')
TEST_FILE2_PATH = data('test2.hi')

@pytest.fixture
def haskell1():
    return specialize(FilesystemFile(TEST_FILE1_PATH))

@pytest.fixture
def haskell2():
    return specialize(FilesystemFile(TEST_FILE2_PATH))

def test_identification(haskell1):
    assert isinstance(haskell1, HiFile)

def test_no_differences(haskell1):
    assert haskell1.compare(haskell1) is None

@pytest.fixture
def differences(haskell1, haskell2):
    return haskell1.compare(haskell2).details

def test_diff(differences):
    with open(data('haskell_expected_diff')) as f:
        expected_diff = f.read()
    assert differences[0].unified_diff == expected_diff
