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
import shutil
import pytest
from diffoscope.comparators import specialize
from diffoscope.comparators.binary import FilesystemFile, NonExistingFile
from diffoscope.comparators.bzip2 import Bzip2File
from diffoscope.config import Config
from conftest import tool_missing

TEST_FILE1_PATH = os.path.join(os.path.dirname(__file__), '../data/test1.bz2')
TEST_FILE2_PATH = os.path.join(os.path.dirname(__file__), '../data/test2.bz2')



@pytest.fixture
def bzip1():
    return specialize(FilesystemFile(TEST_FILE1_PATH))

@pytest.fixture
def bzip2():
    return specialize(FilesystemFile(TEST_FILE2_PATH))

def test_identification(bzip1):
    assert isinstance(bzip1, Bzip2File)

def test_no_differences(bzip1):
    difference = bzip1.compare(bzip1)
    assert difference is None

@pytest.fixture
def differences(bzip1, bzip2):
    return bzip1.compare(bzip2).details

@pytest.mark.skipif(tool_missing('bzip2'), reason='missing bzip2')
def test_content_source(differences):
    assert differences[0].source1 == 'test1'
    assert differences[0].source2 == 'test2'

@pytest.mark.skipif(tool_missing('bzip2'), reason='missing bzip2')
def test_content_source_without_extension(tmpdir):
    path1 = str(tmpdir.join('test1'))
    path2 = str(tmpdir.join('test2'))
    shutil.copy(TEST_FILE1_PATH, path1)
    shutil.copy(TEST_FILE2_PATH, path2)
    bzip1 = specialize(FilesystemFile(path1))
    bzip2 = specialize(FilesystemFile(path2))
    differences = bzip1.compare(bzip2).details
    assert differences[0].source1 == 'test1-content'
    assert differences[0].source2 == 'test2-content'

@pytest.mark.skipif(tool_missing('bzip2'), reason='missing bzip2')
def test_content_diff(differences):
    expected_diff = open(os.path.join(os.path.dirname(__file__), '../data/text_ascii_expected_diff')).read()
    assert differences[0].unified_diff == expected_diff

@pytest.mark.skipif(tool_missing('bzip2'), reason='missing bzip2')
def test_compare_non_existing(monkeypatch, bzip1):
    monkeypatch.setattr(Config, 'new_file', True)
    difference = bzip1.compare(NonExistingFile('/nonexisting', bzip1))
    assert difference.source2 == '/nonexisting'
    assert difference.details[-1].source2 == '/dev/null'
