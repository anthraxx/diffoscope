# -*- coding: utf-8 -*-
#
# diffoscope: in-depth comparison of files, archives, and directories
#
# Copyright © 2015 Chris Lamb <lamby@debian.org>
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

import pytest
import os.path

from conftest import tool_missing
from diffoscope.comparators import specialize
from diffoscope.comparators.binary import FilesystemFile, NonExistingFile
from diffoscope.comparators.image import ImageFile
from diffoscope.config import Config

TEST_FILE1_PATH = os.path.join(os.path.dirname(__file__), '../data/test1.jpg')
TEST_FILE2_PATH = os.path.join(os.path.dirname(__file__), '../data/test2.jpg')

@pytest.fixture
def image1():
    return specialize(FilesystemFile(TEST_FILE1_PATH))

@pytest.fixture
def image2():
    return specialize(FilesystemFile(TEST_FILE2_PATH))

def test_identification(image1):
    assert isinstance(image1, ImageFile)

def test_no_differences(image1):
    difference = image1.compare(image1)
    assert difference is None

@pytest.fixture
def differences(image1, image2):
    return image1.compare(image2).details

@pytest.mark.skipif(tool_missing('img2txt'), reason='img2txt')
def test_diff(differences):
    expected_diff = open(os.path.join(os.path.dirname(__file__), '../data/image_expected_diff')).read()
    assert differences[0].unified_diff == expected_diff

@pytest.mark.skipif(tool_missing('img2txt'), reason='img2txt')
def test_compare_non_existing(monkeypatch, image1):
    monkeypatch.setattr(Config, 'new_file', True)
    difference = image1.compare(NonExistingFile('/nonexisting', image1))
    assert difference.source2 == '/nonexisting'
    assert len(difference.details) > 0
