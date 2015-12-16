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
from diffoscope.comparators.zip import ZipFile, MozillaZipFile
from diffoscope.config import Config
from conftest import tool_missing

TEST_FILE1_PATH = os.path.join(os.path.dirname(__file__), '../data/test1.zip')
TEST_FILE2_PATH = os.path.join(os.path.dirname(__file__), '../data/test2.zip')

@pytest.fixture
def zip1():
    return specialize(FilesystemFile(TEST_FILE1_PATH))

@pytest.fixture
def zip2():
    return specialize(FilesystemFile(TEST_FILE2_PATH))

def test_identification(zip1):
    assert isinstance(zip1, ZipFile)

def test_no_differences(zip1):
    difference = zip1.compare(zip1)
    assert difference is None

@pytest.fixture
def differences(zip1, zip2):
    return zip1.compare(zip2).details

@pytest.mark.skipif(tool_missing('zipinfo'), reason='missing zip')
def test_metadata(differences):
    expected_diff = open(os.path.join(os.path.dirname(__file__), '../data/zip_zipinfo_expected_diff')).read()
    assert differences[0].unified_diff == expected_diff

@pytest.mark.skipif(tool_missing('zipinfo'), reason='missing zip')
def test_compressed_files(differences):
    assert differences[1].source1 == 'dir/text'
    assert differences[1].source2 == 'dir/text'
    expected_diff = open(os.path.join(os.path.dirname(__file__), '../data/text_ascii_expected_diff')).read()
    assert differences[1].unified_diff == expected_diff

@pytest.mark.skipif(tool_missing('zipinfo'), reason='missing zip')
def test_compare_non_existing(monkeypatch, zip1):
    monkeypatch.setattr(Config.general, 'new_file', True)
    difference = zip1.compare(NonExistingFile('/nonexisting', zip1))
    assert difference.source2 == '/nonexisting'
    assert difference.details[-1].source2 == '/dev/null'

TEST_MOZZIP1_PATH = os.path.join(os.path.dirname(__file__), '../data/test1.mozzip')
TEST_MOZZIP2_PATH = os.path.join(os.path.dirname(__file__), '../data/test2.mozzip')

@pytest.fixture
def mozzip1():
    return specialize(FilesystemFile(TEST_MOZZIP1_PATH))

@pytest.fixture
def mozzip2():
    return specialize(FilesystemFile(TEST_MOZZIP2_PATH))

def test_mozzip_identification(mozzip1):
    assert isinstance(mozzip1, MozillaZipFile)

def test_mozzip_no_differences(mozzip1):
    difference = mozzip1.compare(mozzip1)
    assert difference is None

@pytest.fixture
def mozzip_differences(mozzip1, mozzip2):
    return mozzip1.compare(mozzip2).details

@pytest.mark.skipif(tool_missing('zipinfo'), reason='missing zip')
def test_mozzip_metadata(mozzip_differences):
    expected_diff = open(os.path.join(os.path.dirname(__file__), '../data/mozzip_zipinfo_expected_diff')).read()
    diff = mozzip_differences[0].unified_diff
    assert (diff.replace(TEST_MOZZIP1_PATH, 'test1.mozzip')
                .replace(TEST_MOZZIP2_PATH, 'test2.mozzip')) == expected_diff

@pytest.mark.skipif(tool_missing('zipinfo'), reason='missing zip')
def test_mozzip_compressed_files(mozzip_differences):
    assert mozzip_differences[1].source1 == 'dir/text'
    assert mozzip_differences[1].source2 == 'dir/text'
    expected_diff = open(os.path.join(os.path.dirname(__file__), '../data/text_ascii_expected_diff')).read()
    assert mozzip_differences[1].unified_diff == expected_diff

@pytest.mark.skipif(tool_missing('zipinfo'), reason='missing zip')
def test_mozzip_compare_non_existing(monkeypatch, mozzip1):
    monkeypatch.setattr(Config.general, 'new_file', True)
    difference = mozzip1.compare(NonExistingFile('/nonexisting', mozzip1))
    assert difference.source2 == '/nonexisting'
    assert difference.details[-1].source2 == '/dev/null'
