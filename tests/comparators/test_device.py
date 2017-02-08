# -*- coding: utf-8 -*-
#
# diffoscope: in-depth comparison of files, archives, and directories
#
# Copyright © 2017 Chris Lamb <lamby@debian.org>
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

from diffoscope.comparators.binary import FilesystemFile
from diffoscope.comparators.device import Device
from diffoscope.comparators.utils.specialize import specialize

from utils.data import load_fixture, get_data
from utils.tools import skip_unless_tools_exist


text_ascii1 = load_fixture('text_ascii1')

@pytest.fixture
def devnull():
    return specialize(FilesystemFile('/dev/null'))

@pytest.fixture
def differences(devnull, text_ascii1):
    return devnull.compare_bytes(text_ascii1)

@pytest.fixture
def differences_reverse(text_ascii1, devnull):
    return text_ascii1.compare_bytes(devnull)

def test_identification(devnull):
    assert isinstance(devnull, Device)

@skip_unless_tools_exist('xxd')
def test_diff(differences):
    expected_diff = get_data('device_expected_diff')
    assert differences.unified_diff == expected_diff

@skip_unless_tools_exist('xxd')
def test_diff_reverse(differences_reverse):
    expected_diff = get_data('device_expected_diff_reverse')
    assert differences_reverse.unified_diff == expected_diff
