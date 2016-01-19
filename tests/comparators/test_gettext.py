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

import codecs
import os.path
import pytest
from diffoscope.comparators import specialize
from diffoscope.comparators.binary import FilesystemFile, NonExistingFile
from diffoscope.comparators.gettext import MoFile
from diffoscope.config import Config
from conftest import tool_missing

TEST_FILE1_PATH = os.path.join(os.path.dirname(__file__), '../data/test1.mo')
TEST_FILE2_PATH = os.path.join(os.path.dirname(__file__), '../data/test2.mo')

@pytest.fixture
def mo1():
    return specialize(FilesystemFile(TEST_FILE1_PATH))

@pytest.fixture
def mo2():
    return specialize(FilesystemFile(TEST_FILE2_PATH))

def test_identification(mo1):
    assert isinstance(mo1, MoFile)

def test_no_differences(mo1):
    difference = mo1.compare(mo1)
    assert difference is None

@pytest.fixture
def differences(mo1, mo2):
    return mo1.compare(mo2).details

@pytest.mark.skipif(tool_missing('msgunfmt'), reason='missing msgunfmt')
def test_diff(differences):
    expected_diff = open(os.path.join(os.path.dirname(__file__), '../data/mo_expected_diff')).read()
    assert differences[0].unified_diff == expected_diff

@pytest.fixture
def mo_no_charset():
    return specialize(FilesystemFile(os.path.join(os.path.dirname(__file__), '../data/test_no_charset.mo')))

@pytest.fixture
def mo_iso8859_1():
    return specialize(FilesystemFile(os.path.join(os.path.dirname(__file__), '../data/test_iso8859-1.mo')))

@pytest.mark.skipif(tool_missing('msgunfmt'), reason='missing msgunfmt')
def test_charsets(mo_no_charset, mo_iso8859_1):
    difference = mo_no_charset.compare(mo_iso8859_1)
    expected_diff = codecs.open(os.path.join(os.path.dirname(__file__), '../data/mo_charsets_expected_diff'), encoding='utf-8').read()
    assert difference.details[0].unified_diff == expected_diff

@pytest.mark.skipif(tool_missing('msgunfmt'), reason='missing msgunfmt')
def test_compare_non_existing(monkeypatch, mo1):
    monkeypatch.setattr(Config, 'new_file', True)
    difference = mo1.compare(NonExistingFile('/nonexisting', mo1))
    assert difference.source2 == '/nonexisting'
    assert len(difference.details) > 0
