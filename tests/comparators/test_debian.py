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

from __future__ import print_function

import os.path
import shutil
import pytest
from diffoscope.comparators import specialize
from diffoscope.comparators.binary import FilesystemFile, NonExistingFile
from diffoscope.comparators.debian import DotChangesFile
from diffoscope.config import Config
from diffoscope.presenters.text import output_text

TEST_DOT_CHANGES_FILE1_PATH = os.path.join(os.path.dirname(__file__), '../data/test1.changes')
TEST_DOT_CHANGES_FILE2_PATH = os.path.join(os.path.dirname(__file__), '../data/test2.changes')
TEST_DEB_FILE1_PATH = os.path.join(os.path.dirname(__file__), '../data/test1.deb')
TEST_DEB_FILE2_PATH = os.path.join(os.path.dirname(__file__), '../data/test2.deb')

# XXX: test validate failure

@pytest.fixture
def dot_changes1(tmpdir):
    tmpdir.mkdir('a')
    dot_changes_path = str(tmpdir.join('a/test_1.changes'))
    shutil.copy(TEST_DOT_CHANGES_FILE1_PATH, dot_changes_path)
    shutil.copy(TEST_DEB_FILE1_PATH, str(tmpdir.join('a/test_1_all.deb')))
    return specialize(FilesystemFile(dot_changes_path))

@pytest.fixture
def dot_changes2(tmpdir):
    tmpdir.mkdir('b')
    dot_changes_path = str(tmpdir.join('b/test_1.changes'))
    shutil.copy(TEST_DOT_CHANGES_FILE2_PATH, dot_changes_path)
    shutil.copy(TEST_DEB_FILE2_PATH, str(tmpdir.join('b/test_1_all.deb')))
    return specialize(FilesystemFile(dot_changes_path))

def test_identification(dot_changes1):
    assert isinstance(dot_changes1, DotChangesFile)

def test_no_differences(dot_changes1):
    difference = dot_changes1.compare(dot_changes1)
    assert difference is None

@pytest.fixture
def differences(dot_changes1, dot_changes2):
    difference = dot_changes1.compare(dot_changes2)
    output_text(difference, print_func=print)
    return difference.details

def test_description(differences):
    assert differences[0]
    expected_diff = open(os.path.join(os.path.dirname(__file__), '../data/dot_changes_description_expected_diff')).read()
    assert differences[0].unified_diff == expected_diff

def test_internal_diff(differences):
    assert differences[2].source1 == 'test_1_all.deb'

def test_compare_non_existing(monkeypatch, dot_changes1):
    monkeypatch.setattr(Config.general, 'new_file', True)
    difference = dot_changes1.compare(NonExistingFile('/nonexisting', dot_changes1))
    output_text(difference, print_func=print)
    assert difference.source2 == '/nonexisting'
    assert difference.details[-1].source2 == '/dev/null'
