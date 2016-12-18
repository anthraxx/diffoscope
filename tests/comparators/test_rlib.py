# -*- coding: utf-8 -*-
#
# diffoscope: in-depth comparison of files, archives, and directories
#
# Copyright © 2015 Jérémy Bobbio <lunar@debian.org>
# Copyright © 2016 Ximin Luo <infinity0@debian.org>
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
import subprocess

from diffoscope.comparators.ar import ArFile
from diffoscope.comparators.utils import diff_ignore_line_numbers

from utils import skip_unless_tools_exist, skip_unless_tool_is_at_least, \
    skip_unless_tools_exist, data, load_fixture, assert_non_existing

rlib1 = load_fixture(data('test1.rlib'))
rlib2 = load_fixture(data('test2.rlib'))

def llvm_version():
    return subprocess.check_output(['llvm-config', '--version']).decode("utf-8").strip()

def test_identification(rlib1):
    assert isinstance(rlib1, ArFile)

def test_no_differences(rlib1):
    difference = rlib1.compare(rlib1)
    assert difference is None

@pytest.fixture
def differences(rlib1, rlib2):
    return rlib1.compare(rlib2).details

@skip_unless_tools_exist('nm')
def test_num_items(differences):
    assert len(differences) == 4

@skip_unless_tools_exist('nm')
def test_item0_armap(differences):
    assert differences[0].source1 == 'nm -s {}'
    assert differences[0].source2 == 'nm -s {}'
    expected_diff = open(data('rlib_armap_expected_diff')).read()
    assert differences[0].unified_diff == expected_diff

@skip_unless_tools_exist('nm')
def test_item1_elf(differences):
    assert differences[1].source1 == 'alloc_system-d16b8f0e.0.o'
    assert differences[1].source2 == 'alloc_system-d16b8f0e.0.o'
    expected_diff = open(data('rlib_elf_expected_diff')).read()
    assert differences[1].details[0].unified_diff == expected_diff

@skip_unless_tools_exist('nm')
def test_item2_rust_metadata_bin(differences):
    assert differences[2].source1 == 'rust.metadata.bin'
    assert differences[2].source2 == 'rust.metadata.bin'

@skip_unless_tools_exist('llvm-dis')
@skip_unless_tool_is_at_least('llvm-config', llvm_version, '3.8')
def test_item3_deflate_llvm_bitcode(differences):
    assert differences[3].source1 == 'alloc_system-d16b8f0e.0.bytecode.deflate'
    assert differences[3].source2 == 'alloc_system-d16b8f0e.0.bytecode.deflate'
    expected_diff = open(data('rlib_llvm_dis_expected_diff')).read()
    actual_diff = differences[3].details[0].details[1].unified_diff
    assert diff_ignore_line_numbers(actual_diff) == diff_ignore_line_numbers(expected_diff)

@skip_unless_tools_exist('nm')
def test_compare_non_existing(monkeypatch, rlib1):
    assert_non_existing(monkeypatch, rlib1)
