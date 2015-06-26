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

import os
import os.path
import shutil
import pytest
import debbindiff.comparators.binary
from debbindiff.comparators.directory import compare_directories
from debbindiff.presenters.text import output_text

TEST_FILE1_PATH = os.path.join(os.path.dirname(__file__), '../data/text_ascii1') 
TEST_FILE2_PATH = os.path.join(os.path.dirname(__file__), '../data/text_ascii2') 

def test_no_differences():
    difference = compare_directories(os.path.dirname(__file__), os.path.dirname(__file__))
    assert difference is None

@pytest.fixture
def differences(tmpdir):
    tmpdir.mkdir('a')
    tmpdir.mkdir('a/dir')
    tmpdir.mkdir('b')
    tmpdir.mkdir('b/dir')
    shutil.copy(TEST_FILE1_PATH, str(tmpdir.join('a/dir/text')))
    shutil.copy(TEST_FILE2_PATH, str(tmpdir.join('b/dir/text')))
    os.utime(str(tmpdir.join('a/dir/text')), (0, 0))
    os.utime(str(tmpdir.join('b/dir/text')), (0, 0))
    return compare_directories(str(tmpdir.join('a')), str(tmpdir.join('b'))).details

def test_content(differences):
    assert differences[0].source1 == 'dir'
    assert differences[0].details[0].source1 == 'text'
    expected_diff = open(os.path.join(os.path.dirname(__file__), '../data/text_ascii_expected_diff')).read()
    assert differences[0].details[0].unified_diff == expected_diff

def test_stat(differences):
    output_text(differences[0], print_func=print)
    assert 'stat' in differences[0].details[0].details[0].source1
