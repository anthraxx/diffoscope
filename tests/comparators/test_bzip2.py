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
# along with diffoscope.  If not, see <https://www.gnu.org/licenses/>.

import shutil
import pytest

from diffoscope.comparators import specialize
from diffoscope.comparators.bzip2 import Bzip2File
from diffoscope.comparators.binary import FilesystemFile

from utils import skip_unless_tools_exist, data, load_fixture, \
    assert_non_existing


TEST_FILE1_PATH = data('test1.bz2')
TEST_FILE2_PATH = data('test2.bz2')

bzip1 = load_fixture(TEST_FILE1_PATH)
bzip2 = load_fixture(TEST_FILE2_PATH)

def test_identification(bzip1):
    assert isinstance(bzip1, Bzip2File)

def test_no_differences(bzip1):
    difference = bzip1.compare(bzip1)
    assert difference is None

@pytest.fixture
def differences(bzip1, bzip2):
    return bzip1.compare(bzip2).details

@skip_unless_tools_exist('bzip2')
def test_content_source(differences):
    assert differences[0].source1 == 'test1'
    assert differences[0].source2 == 'test2'

@skip_unless_tools_exist('bzip2')
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

@skip_unless_tools_exist('bzip2')
def test_content_diff(differences):
    expected_diff = open(data('text_ascii_expected_diff')).read()
    assert differences[0].unified_diff == expected_diff

@skip_unless_tools_exist('bzip2')
def test_compare_non_existing(monkeypatch, bzip1):
    assert_non_existing(monkeypatch, bzip1)
