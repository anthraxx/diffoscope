#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# debbindiff: highlight differences between two builds of Debian packages
#
# Copyright © 2015 Daniel Kahn Gillmor <dkg@fifthhorseman.net>
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
import shutil
import pytest
from debbindiff.comparators import specialize
from debbindiff.comparators.binary import FilesystemFile
from debbindiff.comparators.mono import MonoExeFile
from conftest import tool_missing

# these were generated with:

# echo 'public class Test { static public void Main () {} }' > test.cs
# mcs -out:test1.exe test.cs ; sleep 2; mcs -out:test2.exe test.cs

TEST_FILE1_PATH = os.path.join(os.path.dirname(__file__), '../data/test1.exe') 
TEST_FILE2_PATH = os.path.join(os.path.dirname(__file__), '../data/test2.exe') 

@pytest.fixture
def exe1():
    return specialize(FilesystemFile(TEST_FILE1_PATH))

@pytest.fixture
def exe2():
    return specialize(FilesystemFile(TEST_FILE2_PATH))

def test_identification(exe1):
    assert isinstance(exe1, MonoExeFile)

def test_no_differences(exe1):
    difference = exe1.compare(exe1)
    assert difference is None

@pytest.fixture
def differences(exe1, exe2):
    return exe1.compare(exe2).details

@pytest.mark.skipif(tool_missing('pedump'), reason='missing pedump')
def test_diff(differences):
    expected_diff = open(os.path.join(os.path.dirname(__file__), '../data/pe_expected_diff')).read()
    assert differences[0].unified_diff == expected_diff
