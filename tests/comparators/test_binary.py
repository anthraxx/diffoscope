#!/usr/bin/env python
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
import shutil
import pytest
import debbindiff.comparators.binary
from debbindiff.comparators.binary import compare_binary_files, are_same_binaries
from debbindiff import RequiredToolNotFound

TEST_FILE1_PATH = os.path.join(os.path.dirname(__file__), '../data/binary1') 
TEST_FILE2_PATH = os.path.join(os.path.dirname(__file__), '../data/binary2') 

def test_are_same_binaries(tmpdir):
    new_path = str(tmpdir.join('binary2'))
    shutil.copy(TEST_FILE1_PATH, new_path)
    assert are_same_binaries(TEST_FILE1_PATH, new_path)

def test_are_not_same_binaries(tmpdir):
    assert not are_same_binaries(TEST_FILE1_PATH, TEST_FILE2_PATH)

def test_no_differences_with_xxd():
    differences = compare_binary_files(TEST_FILE1_PATH, TEST_FILE1_PATH)
    assert len(differences) == 0

def test_compare_with_xxd():
    differences = compare_binary_files(TEST_FILE1_PATH, TEST_FILE2_PATH)
    assert len(differences) == 1
    expected_diff = open(os.path.join(os.path.dirname(__file__), '../data/binary_expected_diff')).read()
    assert differences[0].unified_diff == expected_diff

@pytest.fixture
def xxd_not_found(monkeypatch):
    def mock_xxd(path):
        raise RequiredToolNotFound('xxd')
    monkeypatch.setattr(debbindiff.comparators.binary, 'xxd', mock_xxd)

def test_no_differences_without_xxd(xxd_not_found):
    differences = compare_binary_files(TEST_FILE1_PATH, TEST_FILE1_PATH)
    assert len(differences) == 0

def test_compare_without_xxd(xxd_not_found):
    differences = compare_binary_files(TEST_FILE1_PATH, TEST_FILE2_PATH)
    assert len(differences) == 1
    expected_diff = open(os.path.join(os.path.dirname(__file__), '../data/binary_hexdump_expected_diff')).read()
    assert differences[0].unified_diff == expected_diff
