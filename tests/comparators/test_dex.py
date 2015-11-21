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
from diffoscope.comparators.dex import DexFile
from diffoscope.config import Config
from conftest import tool_missing

TEST_FILE1_PATH = os.path.join(os.path.dirname(__file__), '../data/test1.dex')
TEST_FILE2_PATH = os.path.join(os.path.dirname(__file__), '../data/test2.dex')

@pytest.fixture
def dex1():
    return specialize(FilesystemFile(TEST_FILE1_PATH))

@pytest.fixture
def dex2():
    return specialize(FilesystemFile(TEST_FILE2_PATH))

def test_identification(dex1):
    assert isinstance(dex1, DexFile)

def test_no_differences(dex1):
    difference = dex1.compare(dex1)
    assert difference is None

@pytest.fixture
def differences(dex1, dex2):
    return dex1.compare(dex2).details

@pytest.mark.skipif(tool_missing('enjarify'), reason='missing enjarify')
@pytest.mark.skipif(tool_missing('zipinfo'), reason='missing zipinfo')
@pytest.mark.skipif(tool_missing('javap'), reason='missing javap')
def test_differences(differences):
    assert differences[0].source1 == 'test1.jar'
    assert differences[0].source2 == 'test2.jar'
    zipinfo = differences[0].details[0]
    classdiff = differences[0].details[1]
    assert zipinfo.source1 == 'zipinfo -v {}'
    assert zipinfo.source2 == 'zipinfo -v {}'
    assert classdiff.source1 == 'com/example/MainActivity.class'
    assert classdiff.source2 == 'com/example/MainActivity.class'
    expected_diff = open(os.path.join(os.path.dirname(__file__), '../data/dex_expected_diffs')).read()
    found_diff = zipinfo.unified_diff + classdiff.details[0].unified_diff
    assert expected_diff == found_diff

@pytest.mark.skipif(tool_missing('enjarify'), reason='missing enjarify')
@pytest.mark.skipif(tool_missing('zipinfo'), reason='missing zipinfo')
@pytest.mark.skipif(tool_missing('javap'), reason='missing javap')
def test_compare_non_existing(monkeypatch, dex1):
    monkeypatch.setattr(Config.general, 'new_file', True)
    difference = dex1.compare(NonExistingFile('/nonexisting', dex1))
    assert difference.source2 == '/nonexisting'
    assert difference.details[-1].source2 == '/dev/null'
