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
# along with diffoscope.  If not, see <https://www.gnu.org/licenses/>.

import pytest

from diffoscope.comparators.ps import PsFile

from utils import skip_unless_tools_exist, data, load_fixture, \
    assert_non_existing

ps1 = load_fixture(data('test1.ps'))
ps2 = load_fixture(data('test2.ps'))

def test_identification(ps1):
    assert isinstance(ps1, PsFile)

def test_no_differences(ps1):
    difference = ps1.compare(ps1)
    assert difference is None

@pytest.fixture
def differences(ps1, ps2):
    return ps1.compare(ps2)

@skip_unless_tools_exist('ps2ascii')
def test_internal_diff(differences):
    expected_diff = open(data('ps_internal_expected_diff')).read()
    assert differences.unified_diff == expected_diff

@skip_unless_tools_exist('ps2ascii')
def test_text_diff(differences):
    expected_diff = open(data('ps_text_expected_diff')).read()
    assert differences.details[0].unified_diff == expected_diff

@skip_unless_tools_exist('ps2ascii')
def test_compare_non_existing(monkeypatch, ps1):
    assert_non_existing(monkeypatch, ps1, has_null_source=False)
