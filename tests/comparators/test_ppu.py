# -*- coding: utf-8 -*-
#
# diffoscope: in-depth comparison of files, archives, and directories
#
# Copyright © 2015 Daniel Kahn Gillmor <dkg@fifthhorseman.net>
#             2015 Paul Gevers <elbrus@debian.org>
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
from diffoscope.comparators.ppu import PpuFile
from diffoscope.config import Config
from conftest import tool_missing

# These test files were taken from two different builds of the Debian package
# fp-units-castle-game-engine (version 5.1.1-2 on amd64) on the Debian
# reproducible build infrastructure. The files were originally called
# castletexturefont_dejavusans_10.ppu which are generated during package
# building of the cge package from dejavusans font in the fonts-dejavu package.

TEST_FILE1_PATH = os.path.join(os.path.dirname(__file__), '../data/test1.ppu') 
TEST_FILE2_PATH = os.path.join(os.path.dirname(__file__), '../data/test2.ppu') 

@pytest.fixture
def file1():
    return specialize(FilesystemFile(TEST_FILE1_PATH))

@pytest.fixture
def file2():
    return specialize(FilesystemFile(TEST_FILE2_PATH))

@pytest.mark.skipif(tool_missing('ppudump'), reason='missing ppudump')
def test_identification(file1):
    assert isinstance(file1, PpuFile)

def test_no_differences(file1):
    difference = file1.compare(file1)
    assert difference is None

@pytest.fixture
def differences(file1, file2):
    return file1.compare(file2).details

@pytest.mark.skipif(tool_missing('ppudump'), reason='missing ppudump')
def test_diff(differences):
    print(differences[0].unified_diff)
    expected_diff = open(os.path.join(os.path.dirname(__file__), '../data/ppu_expected_diff')).read()
    assert differences[0].unified_diff == expected_diff

@pytest.mark.skipif(tool_missing('ppudump'), reason='missing ppudump')
def test_compare_non_existing(monkeypatch, file1):
    monkeypatch.setattr(Config, 'new_file', True)
    difference = file1.compare(NonExistingFile('/nonexisting', file1))
    assert difference.source2 == '/nonexisting'
    assert len(difference.details) > 0
