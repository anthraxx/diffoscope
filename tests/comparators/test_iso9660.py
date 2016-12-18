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

from diffoscope.config import Config
from diffoscope.comparators.binary import NonExistingFile
from diffoscope.comparators.iso9660 import Iso9660File

from utils import skip_unless_tools_exist, data, load_fixture

iso1 = load_fixture(data('test1.iso'))
iso2 = load_fixture(data('test2.iso'))

def test_identification(iso1):
    assert isinstance(iso1, Iso9660File)

def test_no_differences(iso1):
    difference = iso1.compare(iso1)
    assert difference is None

@pytest.fixture
def differences(iso1, iso2):
    return iso1.compare(iso2).details

@skip_unless_tools_exist('isoinfo')
def test_iso9660_content(differences):
    expected_diff = open(data('iso9660_content_expected_diff')).read()
    assert differences[0].unified_diff == expected_diff

@skip_unless_tools_exist('isoinfo')
def test_iso9660_rockridge(differences):
    expected_diff = open(data('iso9660_rockridge_expected_diff')).read()
    assert differences[1].unified_diff == expected_diff

@skip_unless_tools_exist('isoinfo')
def test_symlink(differences):
    assert differences[3].comment == 'symlink'
    expected_diff = open(data('symlink_expected_diff')).read()
    assert differences[3].unified_diff == expected_diff

@skip_unless_tools_exist('isoinfo')
def test_compressed_files(differences):
    assert differences[2].source1 == 'text'
    assert differences[2].source2 == 'text'
    expected_diff = open(data('text_ascii_expected_diff')).read()
    assert differences[2].unified_diff == expected_diff

@skip_unless_tools_exist('isoinfo')
def test_compare_non_existing(monkeypatch, iso1):
    monkeypatch.setattr(Config(), 'new_file', True)
    difference = iso1.compare(NonExistingFile('/nonexisting', iso1))
    assert difference.source2 == '/nonexisting'
    assert difference.details[-1].source2 == '/dev/null'
