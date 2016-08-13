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
# along with diffoscope.  If not, see <http://www.gnu.org/licenses/>.

import os.path
import shutil
import pytest
from diffoscope.comparators import specialize
from diffoscope.comparators.binary import FilesystemFile, NonExistingFile
from diffoscope.comparators.ar import ArFile
from diffoscope.comparators.llvm import LlvmBitCodeFile
from diffoscope.comparators.rust import RustObjectFile
from diffoscope.config import Config

TEST_FILE1_PATH = os.path.join(os.path.dirname(__file__), '../data/test1.rlib')
TEST_FILE2_PATH = os.path.join(os.path.dirname(__file__), '../data/test2.rlib')

@pytest.fixture
def rlib1():
    return specialize(FilesystemFile(TEST_FILE1_PATH))

@pytest.fixture
def rlib2():
    return specialize(FilesystemFile(TEST_FILE2_PATH))

def test_identification(rlib1):
    assert isinstance(rlib1, ArFile)

def test_no_differences(rlib1):
    difference = rlib1.compare(rlib1)
    assert difference is None

@pytest.fixture
def differences(rlib1, rlib2):
    return rlib1.compare(rlib2).details

def test_item0_elf(differences):
    assert differences[0].source1 == 'alloc_system-d16b8f0e.0.o'
    assert differences[0].source2 == 'alloc_system-d16b8f0e.0.o'
    expected_diff = open(os.path.join(os.path.dirname(__file__), '../data/rlib_elf_expected_diff')).read()
    assert differences[0].details[0].unified_diff == expected_diff

def test_item1_rust_metadata_bin(differences):
    assert differences[1].source1 == 'rust.metadata.bin'
    assert differences[1].source2 == 'rust.metadata.bin'

def test_item2_deflate_llvm_bitcode(differences):
    assert differences[2].source1 == 'alloc_system-d16b8f0e.0.bytecode.deflate'
    assert differences[2].source2 == 'alloc_system-d16b8f0e.0.bytecode.deflate'
    expected_diff = open(os.path.join(os.path.dirname(__file__), '../data/rlib_llvm_dis_expected_diff')).read()
    assert differences[2].details[0].details[1].unified_diff == expected_diff

def test_compare_non_existing(monkeypatch, rlib1):
    monkeypatch.setattr(Config.general, 'new_file', True)
    difference = rlib1.compare(NonExistingFile('/nonexisting', rlib1))
    assert difference.source2 == '/nonexisting'
    assert difference.details[-1].source2 == '/dev/null'
