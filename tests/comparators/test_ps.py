# -*- coding: utf-8 -*-
#
# diffoscope: in-depth comparison of files, archives, and directories
#
# Copyright © 2016 Reiner Herrmann <reiner@reiner-h.de>
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
from diffoscope.comparators.ps import PsFile
from diffoscope.config import Config
from conftest import tool_missing

TEST_FILE1_PATH = os.path.join(os.path.dirname(__file__), '../data/test1.ps')
TEST_FILE2_PATH = os.path.join(os.path.dirname(__file__), '../data/test2.ps')

@pytest.fixture
def ps1():
    return specialize(FilesystemFile(TEST_FILE1_PATH))

@pytest.fixture
def ps2():
    return specialize(FilesystemFile(TEST_FILE2_PATH))

def test_identification(ps1):
    assert isinstance(ps1, PsFile)

def test_no_differences(ps1):
    difference = ps1.compare(ps1)
    assert difference is None

@pytest.fixture
def differences(ps1, ps2):
    return ps1.compare(ps2)

@pytest.mark.skipif(tool_missing('ps2ascii'), reason='missing ps2ascii')
def test_internal_diff(differences):
    expected_diff = open(os.path.join(os.path.dirname(__file__), '../data/ps_internal_expected_diff')).read()
    assert differences.unified_diff == expected_diff

@pytest.mark.skipif(tool_missing('ps2ascii'), reason='missing ps2ascii')
def test_text_diff(differences):
    expected_diff = open(os.path.join(os.path.dirname(__file__), '../data/ps_text_expected_diff')).read()
    assert differences.details[0].unified_diff == expected_diff

@pytest.mark.skipif(tool_missing('ps2ascii'), reason='missing ps2ascii')
def test_compare_non_existing(monkeypatch, ps1):
    monkeypatch.setattr(Config, 'new_file', True)
    difference = ps1.compare(NonExistingFile('/nonexisting', ps1))
    assert difference.source2 == '/nonexisting'
    assert len(difference.details) > 0
