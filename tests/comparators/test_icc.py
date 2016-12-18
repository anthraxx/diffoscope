# -*- coding: utf-8 -*-
#
# diffoscope: in-depth comparison of files, archives, and directories
#
# Copyright © 2016 Jérémy Bobbio <lunar@debian.org>
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
from diffoscope.comparators.icc import IccFile
from diffoscope.comparators.binary import NonExistingFile

from utils import skip_unless_tools_exist, data, load_fixture

icc1 = load_fixture(data('test1.icc'))
icc2 = load_fixture(data('test2.icc'))

def test_identification(icc1):
    assert isinstance(icc1, IccFile)

def test_no_differences(icc1):
    difference = icc1.compare(icc1)
    assert difference is None

@pytest.fixture
def differences(icc1, icc2):
    return icc1.compare(icc2).details

@skip_unless_tools_exist('cd-iccdump')
def test_diff(differences):
    expected_diff = open(data('icc_expected_diff')).read()
    assert differences[0].unified_diff == expected_diff

@skip_unless_tools_exist('cd-iccdump')
def test_compare_non_existing(monkeypatch, icc1):
    monkeypatch.setattr(Config(), 'new_file', True)
    difference = icc1.compare(NonExistingFile('/nonexisting', icc1))
    assert difference.source2 == '/nonexisting'
    assert len(difference.details) > 0

