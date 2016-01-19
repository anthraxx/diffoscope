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
from diffoscope.comparators.png import PngFile
from diffoscope.config import Config
from conftest import tool_missing

TEST_FILE1_PATH = os.path.join(os.path.dirname(__file__), '../data/test1.png')
TEST_FILE2_PATH = os.path.join(os.path.dirname(__file__), '../data/test2.png')

@pytest.fixture
def png1():
    return specialize(FilesystemFile(TEST_FILE1_PATH))

@pytest.fixture
def png2():
    return specialize(FilesystemFile(TEST_FILE2_PATH))

def test_identification(png1):
    assert isinstance(png1, PngFile)

def test_no_differences(png1):
    difference = png1.compare(png1)
    assert difference is None

@pytest.fixture
def differences(png1, png2):
    return png1.compare(png2).details

@pytest.mark.skipif(tool_missing('sng'), reason='missing sng')
def test_diff(differences):
    expected_diff = open(os.path.join(os.path.dirname(__file__), '../data/png_expected_diff')).read()
    assert differences[0].unified_diff == expected_diff

@pytest.mark.skipif(tool_missing('sng'), reason='missing sng')
def test_compare_non_existing(monkeypatch, png1):
    monkeypatch.setattr(Config, 'new_file', True)
    difference = png1.compare(NonExistingFile('/nonexisting', png1))
    assert difference.source2 == '/nonexisting'
    assert len(difference.details) > 0
