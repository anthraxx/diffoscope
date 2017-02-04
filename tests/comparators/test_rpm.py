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
# along with diffoscope.  If not, see <https://www.gnu.org/licenses/>.

import pytest

from diffoscope.comparators import ComparatorManager
from diffoscope.comparators.binary import FilesystemFile
from diffoscope.comparators.utils.specialize import specialize

from utils.data import load_fixture, data, get_data
from utils.tools import skip_unless_tools_exist
from utils.nonexisting import assert_non_existing


try:
    from diffoscope.comparators.rpm import RpmFile
    miss_rpm_module = False
except ImportError:
    from diffoscope.comparators.rpm_fallback import RpmFile
    miss_rpm_module = True

rpm1 = load_fixture('test1.rpm')
rpm2 = load_fixture('test2.rpm')

def test_identification(rpm1):
    assert isinstance(rpm1, RpmFile)

@pytest.mark.skipif(miss_rpm_module, reason='rpm module is not installed')
def test_no_differences(rpm1):
    difference = rpm1.compare(rpm1)
    assert difference is None

@pytest.fixture
def differences(rpm1, rpm2):
    return rpm1.compare(rpm2).details

@pytest.mark.skipif(miss_rpm_module, reason='rpm module is not installed')
@skip_unless_tools_exist('rpm2cpio')
def test_header(differences):
    assert differences[0].source1 == 'header'
    expected_diff = get_data('rpm_header_expected_diff')
    assert differences[0].unified_diff == expected_diff

@pytest.mark.skipif(miss_rpm_module, reason='rpm module is not installed')
@skip_unless_tools_exist('rpm2cpio')
def test_listing(differences):
    assert differences[1].source1 == 'content'
    assert differences[1].details[0].source1 == 'file list'
    expected_diff = get_data('rpm_listing_expected_diff')
    assert differences[1].details[0].unified_diff == expected_diff

@pytest.mark.skipif(miss_rpm_module, reason='rpm module is not installed')
@skip_unless_tools_exist('rpm2cpio')
def test_content(differences):
    assert differences[1].source1 == 'content'
    assert differences[1].details[1].source1 == './dir/text'
    expected_diff = get_data('text_ascii_expected_diff')
    assert differences[1].details[1].unified_diff == expected_diff

@pytest.mark.skipif(miss_rpm_module, reason='rpm module is not installed')
@skip_unless_tools_exist('rpm2cpio')
def test_compare_non_existing(monkeypatch, rpm1):
    assert_non_existing(monkeypatch, rpm1)

def test_fallback_comparison(monkeypatch):
    manager = ComparatorManager()
    monkeypatch.setattr(manager, 'COMPARATORS', (
        ('rpm_fallback.RpmFile',),
    ))
    manager.reload()

    # Re-specialize after reloading our Comparators
    rpm1 = specialize(FilesystemFile(data('test1.rpm')))
    rpm2 = specialize(FilesystemFile(data('test2.rpm')))

    assert rpm1.compare(rpm1) is None
    assert rpm2.compare(rpm2) is None

    expected_diff = get_data('rpm_fallback_expected_diff')
    assert rpm1.compare(rpm2).unified_diff == expected_diff
