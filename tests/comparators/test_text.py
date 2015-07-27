#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# debbindiff: highlight differences between two builds of Debian packages
#
# Copyright © 2015 Jérémy Bobbio <lunar@debian.org>
#
# debbindiff is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# debbindiff is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with debbindiff.  If not, see <http://www.gnu.org/licenses/>.

import codecs
import os.path
import pytest
from debbindiff.comparators import specialize
from debbindiff.comparators.binary import FilesystemFile
from debbindiff.comparators.text import TextFile

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
    assert difference.comment is None
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
