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
from debbindiff.comparators.elf import compare_elf_files, compare_static_lib_files

TEST_OBJ1_PATH = os.path.join(os.path.dirname(__file__), '../data/test1.o') 
TEST_OBJ2_PATH = os.path.join(os.path.dirname(__file__), '../data/test2.o') 

def test_obj_no_differences():
    difference = compare_elf_files(TEST_OBJ1_PATH, TEST_OBJ1_PATH)
    assert difference is None

@pytest.fixture
def obj_differences():
    return compare_elf_files(TEST_OBJ1_PATH, TEST_OBJ2_PATH).details

def test_diff(obj_differences):
    assert len(obj_differences) == 1
    expected_diff = open(os.path.join(os.path.dirname(__file__), '../data/elf_obj_expected_diff')).read()
    assert obj_differences[0].unified_diff == expected_diff

TEST_LIB1_PATH = os.path.join(os.path.dirname(__file__), '../data/test1.a') 
TEST_LIB2_PATH = os.path.join(os.path.dirname(__file__), '../data/test2.a') 

def test_lib_no_differences():
    difference = compare_elf_files(TEST_LIB1_PATH, TEST_LIB1_PATH)
    assert difference is None

@pytest.fixture
def lib_differences():
    return compare_static_lib_files(TEST_LIB1_PATH, TEST_LIB2_PATH).details

def test_lib_differences(lib_differences):
    assert len(lib_differences) == 2
    assert lib_differences[0].source1 == 'metadata'
    expected_metadata_diff = open(os.path.join(os.path.dirname(__file__), '../data/elf_lib_metadata_expected_diff')).read()
    assert lib_differences[0].unified_diff == expected_metadata_diff
    assert 'objdump' in lib_differences[1].source1
    expected_objdump_diff = open(os.path.join(os.path.dirname(__file__), '../data/elf_lib_objdump_expected_diff')).read()
    assert lib_differences[1].unified_diff == expected_objdump_diff
