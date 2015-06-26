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
from debbindiff.comparators.fonts import compare_ttf_files

TEST_FILE1_PATH = os.path.join(os.path.dirname(__file__), '../data/Samyak-Malayalam1.ttf') 
TEST_FILE2_PATH = os.path.join(os.path.dirname(__file__), '../data/Samyak-Malayalam2.ttf') 

def test_no_differences():
    difference = compare_ttf_files(TEST_FILE1_PATH, TEST_FILE1_PATH)
    assert difference is None

@pytest.fixture
def differences():
    return compare_ttf_files(TEST_FILE1_PATH, TEST_FILE2_PATH).details

def test_diff(differences):
    expected_diff = open(os.path.join(os.path.dirname(__file__), '../data/ttf_expected_diff')).read()
    assert differences[0].unified_diff == expected_diff
