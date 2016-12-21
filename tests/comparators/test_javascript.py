# -*- coding: utf-8 -*-
#
# diffoscope: in-depth comparison of files, archives, and directories
#
# Copyright © 2016 Emanuel Bronshtein <e3amn2l@gmx.com>
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

from diffoscope.config import Config
from diffoscope.comparators.javascript import JavaScriptFile
from diffoscope.comparators.binary import NonExistingFile

from utils import skip_unless_tools_exist, data, load_fixture

javascript1 = load_fixture(data('test1.js'))
javascript2 = load_fixture(data('test2.js'))

def test_identification(javascript1):
    assert isinstance(javascript1, JavaScriptFile)

def test_no_differences(javascript1):
    difference = javascript1.compare(javascript1)
    assert difference is None

@pytest.fixture
def differences(javascript1, javascript2):
    return javascript1.compare(javascript2).details

@skip_unless_tools_exist('js-beautify')
def test_diff(differences):
    expected_diff = open(data('javascript_expected_diff')).read()
    assert differences[0].unified_diff == expected_diff

@skip_unless_tools_exist('js-beautify')
def test_compare_non_existing(monkeypatch, javascript1):
    monkeypatch.setattr(Config(), 'new_file', True)
    difference = javascript1.compare(NonExistingFile('/nonexisting', javascript1))
    assert difference.source2 == '/nonexisting'
    assert len(difference.details) > 0
