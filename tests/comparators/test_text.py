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
from diffoscope.config import Config

@pytest.fixture
def ascii1():
    return specialize(FilesystemFile(os.path.join(os.path.dirname(__file__), '../data/text_ascii1')))

@pytest.fixture
def ascii2():
    return specialize(FilesystemFile(os.path.join(os.path.dirname(__file__), '../data/text_ascii2')))

def test_no_differences(ascii1):
    difference = ascii1.compare(ascii1)
    assert difference is None

def test_difference_in_ascii(ascii1, ascii2):
    difference = ascii1.compare(ascii2)
    assert difference is not None
    expected_diff = open(os.path.join(os.path.dirname(__file__), '../data/text_ascii_expected_diff')).read()
    assert difference.unified_diff == expected_diff
    assert not difference.comments
    assert len(difference.details) == 0

@pytest.fixture
def unicode1():
    return specialize(FilesystemFile(os.path.join(os.path.dirname(__file__), '../data/text_unicode1')))

@pytest.fixture
def unicode2():
    return specialize(FilesystemFile(os.path.join(os.path.dirname(__file__), '../data/text_unicode2')))

def test_difference_in_unicode(unicode1, unicode2):
    difference = unicode1.compare(unicode2)
    expected_diff = codecs.open(os.path.join(os.path.dirname(__file__), '../data/text_unicode_expected_diff'), encoding='utf-8').read()
    assert difference.unified_diff == expected_diff

@pytest.fixture
def iso8859():
    return specialize(FilesystemFile(os.path.join(os.path.dirname(__file__), '../data/text_iso8859')))

def test_difference_between_iso88591_and_unicode(iso8859, unicode1):
    difference = iso8859.compare(unicode1)
    expected_diff = codecs.open(os.path.join(os.path.dirname(__file__), '../data/text_iso8859_expected_diff'), encoding='utf-8').read()
    assert difference.unified_diff == expected_diff

def test_difference_between_iso88591_and_unicode_only(iso8859, tmpdir):
    utf8_path = str(tmpdir.join('utf8'))
    with open(utf8_path, 'wb') as f:
        f.write(codecs.open(os.path.join(os.path.dirname(__file__), '../data/text_iso8859'), encoding='iso8859-1').read().encode('utf-8'))
    utf8 = specialize(FilesystemFile(utf8_path))
    difference = iso8859.compare(utf8)
    assert difference.unified_diff is None
    assert difference.details[0].source1 == 'encoding'

def test_compare_non_existing(monkeypatch, ascii1):
    monkeypatch.setattr(Config.general, 'new_file', True)
    difference = ascii1.compare(NonExistingFile('/nonexisting', ascii1))
    assert difference.source2 == '/nonexisting'
