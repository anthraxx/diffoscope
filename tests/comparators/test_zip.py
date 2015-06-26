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
from debbindiff.comparators.zip import compare_zip_files

TEST_FILE1_PATH = os.path.join(os.path.dirname(__file__), '../data/test1.zip') 
TEST_FILE2_PATH = os.path.join(os.path.dirname(__file__), '../data/test2.zip') 

def test_no_differences():
    difference = compare_zip_files(TEST_FILE1_PATH, TEST_FILE1_PATH)
    assert difference is None

@pytest.fixture
def differences():
    return compare_zip_files(TEST_FILE1_PATH, TEST_FILE2_PATH).details

def test_compressed_files(differences):
    assert differences[0].source1 == 'dir/text'
    assert differences[0].source2 == 'dir/text'
    expected_diff = open(os.path.join(os.path.dirname(__file__), '../data/text_ascii_expected_diff')).read()
    assert differences[0].unified_diff == expected_diff

def test_metadata(differences):
    expected_diff = open(os.path.join(os.path.dirname(__file__), '../data/zip_zipinfo_expected_diff')).read()
    assert differences[-1].unified_diff == expected_diff

def test_bad_zip():
    difference = compare_zip_files(os.path.join(os.path.dirname(__file__), '../data/text_unicode1'),
                                    os.path.join(os.path.dirname(__file__), '../data/text_unicode2'))
    expected_diff = open(os.path.join(os.path.dirname(__file__), '../data/text_unicode_binary_fallback')).read()
    assert difference.unified_diff == expected_diff
