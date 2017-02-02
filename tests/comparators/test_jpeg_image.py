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
import subprocess

from diffoscope.config import Config
from diffoscope.comparators.image import JPEGImageFile
from diffoscope.comparators.missing_file import MissingFile

from utils.data import load_fixture, get_data
from utils.tools import skip_unless_tools_exist, skip_unless_tool_is_at_least


image1 = load_fixture('test1.jpg')
image2 = load_fixture('test2.jpg')
image1_meta = load_fixture('test1_meta.jpg')
image2_meta = load_fixture('test2_meta.jpg')

def identify_version():
    out = subprocess.check_output(['identify', '-version'])
    # First line is expected to look like
    # "Version: ImageMagick 6.9.6-6 Q16 x86_64 20161125 ..."
    return out.decode('utf-8').splitlines()[0].split()[2].strip()

def test_identification(image1):
    assert isinstance(image1, JPEGImageFile)

def test_no_differences(image1):
    difference = image1.compare(image1)
    assert difference is None

@pytest.fixture
def differences(image1, image2):
    return image1.compare(image2).details

@skip_unless_tools_exist('img2txt', 'identify')
def test_diff(differences):
    expected_diff = get_data('jpeg_image_expected_diff')
    assert differences[0].unified_diff == expected_diff

@skip_unless_tools_exist('img2txt', 'identify')
def test_compare_non_existing(monkeypatch, image1):
    monkeypatch.setattr(Config(), 'new_file', True)
    difference = image1.compare(MissingFile('/nonexisting', image1))
    assert difference.source2 == '/nonexisting'
    assert len(difference.details) > 0

@pytest.fixture
def differences_meta(image1_meta, image2_meta):
    return image1_meta.compare(image2_meta).details

@skip_unless_tools_exist('img2txt', 'identify')
@skip_unless_tool_is_at_least('identify', identify_version, '6.9.6')
def test_diff_meta(differences_meta):
    expected_diff = get_data('jpeg_image_meta_expected_diff')
    assert differences_meta[-1].unified_diff == expected_diff
