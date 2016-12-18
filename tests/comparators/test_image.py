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
# along with diffoscope.  If not, see <https://www.gnu.org/licenses/>.

import pytest

from diffoscope.config import Config
from diffoscope.comparators.image import ImageFile
from diffoscope.comparators.binary import NonExistingFile

from utils import skip_unless_tools_exist, data, load_fixture

image1 = load_fixture(data('test1.jpg'))
image2 = load_fixture(data('test2.jpg'))

def test_identification(image1):
    assert isinstance(image1, ImageFile)

def test_no_differences(image1):
    difference = image1.compare(image1)
    assert difference is None

@pytest.fixture
def differences(image1, image2):
    return image1.compare(image2).details

@skip_unless_tools_exist('img2txt')
def test_diff(differences):
    expected_diff = open(data('image_expected_diff')).read()
    assert differences[0].unified_diff == expected_diff

@skip_unless_tools_exist('img2txt')
def test_compare_non_existing(monkeypatch, image1):
    monkeypatch.setattr(Config(), 'new_file', True)
    difference = image1.compare(NonExistingFile('/nonexisting', image1))
    assert difference.source2 == '/nonexisting'
    assert len(difference.details) > 0
