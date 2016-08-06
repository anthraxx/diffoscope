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

import os
import pytest

from diffoscope.comparators import specialize
from diffoscope.comparators.json import JSONFile
from diffoscope.comparators.binary import FilesystemFile

TEST_FILE1_PATH = os.path.join(os.path.dirname(__file__), '../data/test1.json')
TEST_FILE2_PATH = os.path.join(os.path.dirname(__file__), '../data/test2.json')

@pytest.fixture
def json1():
    return specialize(FilesystemFile(TEST_FILE1_PATH))

@pytest.fixture
def json2():
    return specialize(FilesystemFile(TEST_FILE2_PATH))

def test_identification(json1):
    assert isinstance(json1, JSONFile)

def test_no_differences(json1):
    assert json1.compare(json1) is None

@pytest.fixture
def differences(json1, json2):
    return json1.compare(json2).details

def test_diff(differences):
    with open(os.path.join(os.path.dirname(__file__), '../data/json_expected_diff')) as f:
        expected_diff = f.read()
    assert differences[0].unified_diff == expected_diff
