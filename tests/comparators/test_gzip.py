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
from debbindiff.comparators.gzip import compare_gzip_files

TEST_FILE1_PATH = os.path.join(os.path.dirname(__file__), '../data/test1.gz') 
TEST_FILE2_PATH = os.path.join(os.path.dirname(__file__), '../data/test2.gz') 

def test_no_differences():
    difference = compare_gzip_files(TEST_FILE1_PATH, TEST_FILE1_PATH)
    assert difference is None

@pytest.fixture
def differences():
    return compare_gzip_files(TEST_FILE1_PATH, TEST_FILE2_PATH).details

def test_metadata(differences):
    assert differences[0].source1 == 'metadata'
    assert differences[0].source2 == 'metadata'
    expected_diff = open(os.path.join(os.path.dirname(__file__), '../data/gzip_metadata_expected_diff')).read()
    assert differences[0].unified_diff == expected_diff

def test_content_source(differences):
    assert differences[1].source1 == 'test1'
    assert differences[1].source2 == 'test2'

def test_content_source_without_extension(tmpdir):
    path1 = str(tmpdir.join('test1'))
    path2 = str(tmpdir.join('test2'))
    shutil.copy(TEST_FILE1_PATH, path1)
    shutil.copy(TEST_FILE2_PATH, path2)
    difference = compare_gzip_files(path1, path2).details
    assert difference[1].source1 == 'test1-content'
    assert difference[1].source2 == 'test2-content'

def test_content_diff(differences):
    expected_diff = open(os.path.join(os.path.dirname(__file__), '../data/text_ascii_expected_diff')).read()
    assert differences[1].unified_diff == expected_diff
