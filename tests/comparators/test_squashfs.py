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

import codecs
import os.path
import shutil
import pytest
from debbindiff.comparators.squashfs import compare_squashfs_files

TEST_FILE1_PATH = os.path.join(os.path.dirname(__file__), '../data/test1.squashfs')
TEST_FILE2_PATH = os.path.join(os.path.dirname(__file__), '../data/test2.squashfs')

def test_no_differences():
    differences = compare_squashfs_files(TEST_FILE1_PATH, TEST_FILE1_PATH)
    assert len(differences) == 0

@pytest.mark.xfail
def test_no_warnings(capfd, differences):
     compare_squashfs_files(TEST_FILE1_PATH, TEST_FILE2_PATH)[0].details # skip container with path
     _, err = capfd.readouterr()
     assert err == ''

@pytest.fixture
def differences():
    return compare_squashfs_files(TEST_FILE1_PATH, TEST_FILE2_PATH)[0].details # skip container with path

def test_superblock(differences):
    expected_diff = open(os.path.join(os.path.dirname(__file__), '../data/squashfs_superblock_expected_diff')).read()
    assert differences[0].unified_diff == expected_diff

def test_listing(differences):
    expected_diff = open(os.path.join(os.path.dirname(__file__), '../data/squashfs_listing_expected_diff')).read()
    assert differences[1].unified_diff == expected_diff

def test_compressed_files(differences):
    assert differences[2].source1 == 'text'
    assert differences[2].source2 == 'text'
    expected_diff = open(os.path.join(os.path.dirname(__file__), '../data/text_ascii_expected_diff')).read()
    assert differences[2].unified_diff == expected_diff
