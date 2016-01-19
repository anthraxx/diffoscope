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
from diffoscope.comparators.sqlite import Sqlite3Database
from diffoscope.config import Config
from conftest import tool_missing

TEST_FILE1_PATH = os.path.join(os.path.dirname(__file__), '../data/test1.sqlite3')
TEST_FILE2_PATH = os.path.join(os.path.dirname(__file__), '../data/test2.sqlite3')

@pytest.fixture
def sqlite3db1():
    return specialize(FilesystemFile(TEST_FILE1_PATH))

@pytest.fixture
def sqlite3db2():
    return specialize(FilesystemFile(TEST_FILE2_PATH))

def test_identification(sqlite3db1):
    assert isinstance(sqlite3db1, Sqlite3Database)

def test_no_differences(sqlite3db1):
    difference = sqlite3db1.compare(sqlite3db1)
    assert difference is None

@pytest.fixture
def differences(sqlite3db1, sqlite3db2):
    return sqlite3db1.compare(sqlite3db2).details

@pytest.mark.skipif(tool_missing('sqlite3'), reason='missing sqlite3')
def test_diff(differences):
    expected_diff = open(os.path.join(os.path.dirname(__file__), '../data/sqlite3_expected_diff')).read()
    assert differences[0].unified_diff == expected_diff

@pytest.mark.skipif(tool_missing('sqlite3'), reason='missing sqlite3')
def test_compare_non_existing(monkeypatch, sqlite3db1):
    monkeypatch.setattr(Config.general, 'new_file', True)
    difference = sqlite3db1.compare(NonExistingFile('/nonexisting', sqlite3db1))
    assert difference.source2 == '/nonexisting'
    assert len(difference.details) > 0
