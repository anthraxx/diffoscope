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
# along with diffoscope.  If not, see <https://www.gnu.org/licenses/>.

import pytest

from diffoscope.comparators.zip import ZipFile, MozillaZipFile

from utils.data import load_fixture, get_data
from utils.tools import skip_unless_tools_exist
from utils.nonexisting import assert_non_existing


zip1 = load_fixture('test1.zip')
zip2 = load_fixture('test2.zip')
mozzip1 = load_fixture('test1.mozzip')
mozzip2 = load_fixture('test2.mozzip')


def test_identification(zip1):
    assert isinstance(zip1, ZipFile)

def test_no_differences(zip1):
    difference = zip1.compare(zip1)
    assert difference is None

@pytest.fixture
def differences(zip1, zip2):
    return zip1.compare(zip2).details

@skip_unless_tools_exist('zipinfo')
def test_metadata(differences):
    expected_diff = get_data('zip_zipinfo_expected_diff')
    assert differences[0].unified_diff == expected_diff

@skip_unless_tools_exist('zipinfo')
def test_compressed_files(differences):
    assert differences[1].source1 == 'dir/text'
    assert differences[1].source2 == 'dir/text'
    expected_diff = get_data('text_ascii_expected_diff')
    assert differences[1].unified_diff == expected_diff

@skip_unless_tools_exist('zipinfo')
def test_compare_non_existing(monkeypatch, zip1):
    assert_non_existing(monkeypatch, zip1)

def test_mozzip_identification(mozzip1):
    assert isinstance(mozzip1, MozillaZipFile)

def test_mozzip_no_differences(mozzip1):
    difference = mozzip1.compare(mozzip1)
    assert difference is None

@pytest.fixture
def mozzip_differences(mozzip1, mozzip2):
    return mozzip1.compare(mozzip2).details

@skip_unless_tools_exist('zipinfo')
def test_mozzip_metadata(mozzip_differences, mozzip1, mozzip2):
    expected_diff = get_data('mozzip_zipinfo_expected_diff')
    diff = mozzip_differences[0].unified_diff
    assert (diff.replace(mozzip1.path, 'test1.mozzip')
                .replace(mozzip2.path, 'test2.mozzip')) == expected_diff

@skip_unless_tools_exist('zipinfo')
def test_mozzip_compressed_files(mozzip_differences):
    assert mozzip_differences[1].source1 == 'dir/text'
    assert mozzip_differences[1].source2 == 'dir/text'
    expected_diff = get_data('text_ascii_expected_diff')
    assert mozzip_differences[1].unified_diff == expected_diff

@skip_unless_tools_exist('zipinfo')
def test_mozzip_compare_non_existing(monkeypatch, mozzip1):
    assert_non_existing(monkeypatch, mozzip1)
