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

import os.path
import shutil
import subprocess
import pytest
from debbindiff import tool_required
from debbindiff.comparators.utils import binary_fallback, returns_details
from debbindiff.difference import Difference

def test_same_binaries():
    @binary_fallback
    def mock_comparator(path1, path2, source=None):
        raise Exception('should not be run')
    assert mock_comparator(__file__, __file__) is None

TEST_FILE1_PATH = os.path.join(os.path.dirname(__file__), '../data/text_unicode1')
TEST_FILE2_PATH = os.path.join(os.path.dirname(__file__), '../data/text_unicode2')

def test_return_differences():
    d = Difference('diff', TEST_FILE1_PATH, TEST_FILE2_PATH, source='source')
    @binary_fallback
    def mock_comparator(path1, path2, source=None):
        return d
    difference = mock_comparator(TEST_FILE1_PATH, TEST_FILE2_PATH)
    assert difference == d

def test_fallback():
    @binary_fallback
    def mock_comparator(path1, path2, source=None):
        return None
    difference = mock_comparator(TEST_FILE1_PATH, TEST_FILE2_PATH)
    expected_diff = open(os.path.join(os.path.dirname(__file__), '../data/text_unicode_binary_fallback')).read()
    assert 'yet data differs' in difference.comment
    assert difference.unified_diff == expected_diff

def test_process_failed():
    output = 'Free Jeremy Hammond'
    @binary_fallback
    def mock_comparator(path1, path2, source=None):
        subprocess.check_output(['sh', '-c', 'echo "%s"; exit 42' % output], shell=False)
        raise Exception('should not be run')
    difference = mock_comparator(TEST_FILE1_PATH, TEST_FILE2_PATH)
    expected_diff = open(os.path.join(os.path.dirname(__file__), '../data/text_unicode_binary_fallback')).read()
    assert output in difference.comment
    assert '42' in difference.comment
    assert difference.unified_diff == expected_diff

def test_tool_not_found(monkeypatch):
    monkeypatch.setattr('debbindiff.RequiredToolNotFound.get_package', lambda _: 'some-package')
    @binary_fallback
    @tool_required('nonexistent')
    def mock_comparator(path1, path2, source=None):
        raise Exception('should not be run')
    difference = mock_comparator(TEST_FILE1_PATH, TEST_FILE2_PATH)
    expected_diff = open(os.path.join(os.path.dirname(__file__), '../data/text_unicode_binary_fallback')).read()
    assert 'nonexistent' in difference.comment
    assert 'some-package' in difference.comment
    assert difference.unified_diff == expected_diff

def test_no_details():
    @returns_details
    def mock_comparator(path1, path2, source=None):
        return []
    difference = mock_comparator(TEST_FILE1_PATH, TEST_FILE2_PATH)
    assert difference is None

def test_details():
    d = Difference('diff', TEST_FILE1_PATH, TEST_FILE2_PATH)
    @returns_details
    def mock_comparator(path1, path2, source=None):
        return [d]
    difference = mock_comparator(TEST_FILE1_PATH, TEST_FILE2_PATH)
    assert difference.source1 == TEST_FILE1_PATH
    assert difference.source2 == TEST_FILE2_PATH
    assert difference.details == [d]
