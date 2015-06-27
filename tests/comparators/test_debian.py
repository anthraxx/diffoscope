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

from __future__ import print_function

import os.path
import shutil
import pytest
import debbindiff.comparators.deb
from debbindiff.comparators.debian import compare_dot_changes_files
from debbindiff.presenters.text import output_text

TEST_DOT_CHANGES_FILE1_PATH = os.path.join(os.path.dirname(__file__), '../data/test1.changes')
TEST_DOT_CHANGES_FILE2_PATH = os.path.join(os.path.dirname(__file__), '../data/test2.changes')
TEST_DEB_FILE1_PATH = os.path.join(os.path.dirname(__file__), '../data/test1.deb')
TEST_DEB_FILE2_PATH = os.path.join(os.path.dirname(__file__), '../data/test2.deb')

@pytest.fixture
def copydeb(tmpdir):
    changes1_path = str(tmpdir.join('a/test_1.changes'))
    changes2_path = str(tmpdir.join('b/test_1.changes'))
    tmpdir.mkdir('a')
    tmpdir.mkdir('b')
    shutil.copy(TEST_DOT_CHANGES_FILE1_PATH, changes1_path)
    shutil.copy(TEST_DOT_CHANGES_FILE2_PATH, changes2_path)
    shutil.copy(TEST_DEB_FILE1_PATH, str(tmpdir.join('a/test_1_all.deb')))
    shutil.copy(TEST_DEB_FILE2_PATH, str(tmpdir.join('b/test_1_all.deb')))
    return (changes1_path, changes2_path)

def test_no_differences(copydeb):
    changes1_path, _ = copydeb
    difference = compare_dot_changes_files(changes1_path, changes1_path)
    assert difference is None

@pytest.fixture
def differences(copydeb):
    changes1_path, changes2_path = copydeb
    difference = compare_dot_changes_files(changes1_path, changes2_path)
    output_text(difference, print_func=print)
    return difference.details

def test_description(differences):
    assert differences[0]
    expected_diff = open(os.path.join(os.path.dirname(__file__), '../data/dot_changes_description_expected_diff')).read()
    assert differences[0].unified_diff == expected_diff

def test_internal_diff(differences):
    assert differences[2].source1 == 'test_1_all.deb'
