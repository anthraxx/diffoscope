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
from diffoscope.comparators.iso9660 import Iso9660File
from diffoscope.config import Config
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
    assert differences[3].comment == 'symlink'
    expected_diff = open(os.path.join(os.path.dirname(__file__), '../data/symlink_expected_diff')).read()
    assert differences[3].unified_diff == expected_diff

@pytest.mark.skipif(tool_missing('isoinfo'), reason='missing isoinfo')
def test_compressed_files(differences):
    assert differences[2].source1 == 'text'
    assert differences[2].source2 == 'text'
    expected_diff = open(os.path.join(os.path.dirname(__file__), '../data/text_ascii_expected_diff')).read()
    assert differences[2].unified_diff == expected_diff

@pytest.mark.skipif(tool_missing('isoinfo'), reason='missing isoinfo')
def test_compare_non_existing(monkeypatch, iso1):
    monkeypatch.setattr(Config.general, 'new_file', True)
    difference = iso1.compare(NonExistingFile('/nonexisting', iso1))
    assert difference.source2 == '/nonexisting'
    assert difference.details[-1].source2 == '/dev/null'
