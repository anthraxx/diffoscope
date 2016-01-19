# -*- coding: utf-8 -*-
#
# diffoscope: in-depth comparison of files, archives, and directories
#
# Copyright © 2015 Jérémy Bobbio <lunar@debian.org>
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
import pytest
from diffoscope.comparators import specialize
from diffoscope.comparators.binary import FilesystemFile, NonExistingFile
from diffoscope.comparators.java import ClassFile
from diffoscope.config import Config
from conftest import tool_missing

TEST_FILE1_PATH = os.path.join(os.path.dirname(__file__), '../data/Test1.class')
TEST_FILE2_PATH = os.path.join(os.path.dirname(__file__), '../data/Test2.class')

@pytest.fixture
def class1():
    return specialize(FilesystemFile(TEST_FILE1_PATH))

@pytest.fixture
def class2():
    return specialize(FilesystemFile(TEST_FILE2_PATH))

def test_identification(class1):
    assert isinstance(class1, ClassFile)

def test_no_differences(class1):
    difference = class1.compare(class1)
    assert difference is None

@pytest.fixture
def differences(class1, class2):
    return class1.compare(class2).details

@pytest.mark.skipif(tool_missing('javap'), reason='missing javap')
def test_diff(differences):
    expected_diff = open(os.path.join(os.path.dirname(__file__), '../data/class_expected_diff')).read()
    assert differences[0].unified_diff == expected_diff

@pytest.mark.skipif(tool_missing('javap'), reason='missing javap')
def test_compare_non_existing(monkeypatch, class1):
    monkeypatch.setattr(Config, 'new_file', True)
    difference = class1.compare(NonExistingFile('/nonexisting', class1))
    assert difference.source2 == '/nonexisting'
    assert len(difference.details) > 0
