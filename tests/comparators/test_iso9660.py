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

import codecs
import os.path
import shutil
import pytest
from debbindiff.comparators import specialize
from debbindiff.comparators.binary import FilesystemFile
from debbindiff.comparators.iso9660 import Iso9660File
from conftest import tool_missing

TEST_FILE1_PATH = os.path.join(os.path.dirname(__file__), '../data/test1.iso')
TEST_FILE2_PATH = os.path.join(os.path.dirname(__file__), '../data/test2.iso')

@pytest.fixture
def iso1():
    return specialize(FilesystemFile(TEST_FILE1_PATH))

@pytest.fixture
def iso2():
    return specialize(FilesystemFile(TEST_FILE2_PATH))

def test_identification(iso1):
    assert isinstance(iso1, Iso9660File)

def test_no_differences(iso1):
    difference = iso1.compare(iso1)
    assert difference is None

@pytest.fixture
def differences(iso1, iso2):
    return iso1.compare(iso2).details

@pytest.mark.skipif(tool_missing('isoinfo'), reason='missing isoinfo')
def test_iso9660_content(differences):
    expected_diff = open(os.path.join(os.path.dirname(__file__), '../data/iso9660_content_expected_diff')).read()
    assert differences[0].unified_diff == expected_diff

@pytest.mark.skipif(tool_missing('isoinfo'), reason='missing isoinfo')
def test_iso9660_rockridge(differences):
    expected_diff = open(os.path.join(os.path.dirname(__file__), '../data/iso9660_rockridge_expected_diff')).read()
    assert differences[1].unified_diff == expected_diff

@pytest.mark.skipif(tool_missing('isoinfo'), reason='missing isoinfo')
def test_symlink(differences):
    assert differences[2].comment == 'symlink'
    expected_diff = open(os.path.join(os.path.dirname(__file__), '../data/symlink_expected_diff')).read()
    assert differences[2].unified_diff == expected_diff

@pytest.mark.skipif(tool_missing('isoinfo'), reason='missing isoinfo')
def test_compressed_files(differences):
    assert differences[3].source1 == 'text'
    assert differences[3].source2 == 'text'
    expected_diff = open(os.path.join(os.path.dirname(__file__), '../data/text_ascii_expected_diff')).read()
    assert differences[3].unified_diff == expected_diff
