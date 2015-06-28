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

from debbindiff.comparators import compare_unknown

TEST_TEXT_ASCII_FILE1_PATH = os.path.join(os.path.dirname(__file__), '../data/text_ascii1')
TEST_TEXT_ASCII_FILE2_PATH = os.path.join(os.path.dirname(__file__), '../data/text_ascii2')
TEST_TEXT_UNICODE_FILE1_PATH = os.path.join(os.path.dirname(__file__), '../data/text_unicode1')
TEST_TEXT_UNICODE_FILE2_PATH = os.path.join(os.path.dirname(__file__), '../data/text_unicode2')
TEST_BINARY_FILE1_PATH = os.path.join(os.path.dirname(__file__), '../data/binary1')
TEST_BINARY_FILE2_PATH = os.path.join(os.path.dirname(__file__), '../data/binary2')

def test_same_binaries():
    difference = compare_unknown(TEST_BINARY_FILE1_PATH, TEST_BINARY_FILE1_PATH)
    assert difference is None

def test_text_ascii_files():
    difference = compare_unknown(TEST_TEXT_ASCII_FILE1_PATH, TEST_TEXT_ASCII_FILE2_PATH)
    expected_diff = open(os.path.join(os.path.dirname(__file__), '../data/text_ascii_expected_diff')).read()
    assert difference.unified_diff == expected_diff

def test_text_unicode_files():
    difference = compare_unknown(TEST_TEXT_UNICODE_FILE1_PATH, TEST_TEXT_UNICODE_FILE2_PATH)
    expected_diff = codecs.open(os.path.join(os.path.dirname(__file__), '../data/text_unicode_expected_diff'), encoding='utf-8').read()
    assert difference.unified_diff == expected_diff

def test_binary_files():
    difference = compare_unknown(TEST_BINARY_FILE1_PATH, TEST_BINARY_FILE2_PATH)
    expected_diff = codecs.open(os.path.join(os.path.dirname(__file__), '../data/binary_expected_diff')).read()
    assert difference.unified_diff == expected_diff
