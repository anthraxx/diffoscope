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
from debbindiff.comparators.text import compare_text_files

def test_no_differences():
    text1 = os.path.join(os.path.dirname(__file__), '../data/text_ascii1')
    text2 = os.path.join(os.path.dirname(__file__), '../data/text_ascii1')
    differences = compare_text_files(text1, text2)
    assert len(differences) == 0

def test_difference_in_ascii():
    text1 = os.path.join(os.path.dirname(__file__), '../data/text_ascii1')
    text2 = os.path.join(os.path.dirname(__file__), '../data/text_ascii2')
    differences = compare_text_files(text1, text2)
    assert len(differences) == 1
    expected_diff = open(os.path.join(os.path.dirname(__file__), '../data/text_ascii_expected_diff')).read()
    assert differences[0].unified_diff == expected_diff
    assert differences[0].comment is None
    assert len(differences[0].details) == 0

def test_difference_in_unicode():
    text1 = os.path.join(os.path.dirname(__file__), '../data/text_unicode1')
    text2 = os.path.join(os.path.dirname(__file__), '../data/text_unicode2')
    differences = compare_text_files(text1, text2)
    expected_diff = codecs.open(os.path.join(os.path.dirname(__file__), '../data/text_unicode_expected_diff'), encoding='utf-8').read()
    assert differences[0].unified_diff == expected_diff

def test_fallback_to_binary():
    text1 = os.path.join(os.path.dirname(__file__), '../data/text_unicode1')
    text2 = os.path.join(os.path.dirname(__file__), '../data/text_unicode2')
    differences = compare_text_files(text1, text2, encoding='ascii')
    expected_diff = open(os.path.join(os.path.dirname(__file__), '../data/text_unicode_binary_fallback')).read()
    assert differences[0].unified_diff == expected_diff

@pytest.mark.xfail
def test_difference_between_iso88591_and_unicode():
    text1 = os.path.join(os.path.dirname(__file__), '../data/text_unicode1')
    text2 = os.path.join(os.path.dirname(__file__), '../data/text_iso8859')
    differences = compare_text_files(text1, text2)
    expected_diff = codecs.open(os.path.join(os.path.dirname(__file__), '../data/text_iso8859_expected_diff'), encoding='utf-8').read()
    assert differences[0].unified_diff == expected_diff
