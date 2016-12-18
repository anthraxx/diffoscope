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

from diffoscope.comparators.cpio import CpioFile

from utils import skip_unless_tools_exist, data, load_fixture, \
    assert_non_existing


cpio1 = load_fixture(data('test1.cpio'))
cpio2 = load_fixture(data('test2.cpio'))

def test_identification(cpio1):
    assert isinstance(cpio1, CpioFile)

def test_no_differences(cpio1):
    difference = cpio1.compare(cpio1)
    assert difference is None

@pytest.fixture
def differences(cpio1, cpio2):
    return cpio1.compare(cpio2).details

@skip_unless_tools_exist('cpio')
def test_listing(differences):
    expected_diff = open(data('cpio_listing_expected_diff')).read()
    assert differences[0].unified_diff == expected_diff

@skip_unless_tools_exist('cpio')
def test_symlink(differences):
    assert differences[1].source1 == 'dir/link'
    assert differences[1].comment == 'symlink'
    expected_diff = open(data('symlink_expected_diff')).read()
    assert differences[1].unified_diff == expected_diff

@skip_unless_tools_exist('cpio')
def test_compressed_files(differences):
    assert differences[2].source1 == 'dir/text'
    assert differences[2].source2 == 'dir/text'
    expected_diff = open(data('text_ascii_expected_diff')).read()
    assert differences[2].unified_diff == expected_diff

@skip_unless_tools_exist('cpio')
def test_compare_non_existing(monkeypatch, cpio1):
    assert_non_existing(monkeypatch, cpio1)
