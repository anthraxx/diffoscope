# -*- coding: utf-8 -*-
#
# diffoscope: in-depth comparison of files, archives, and directories
#
# Copyright © 2017 Maria Glukhova <siammezzze@gmail.com>
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

from diffoscope.comparators.apk import ApkFile

from utils.data import data, load_fixture
from utils.tools import skip_unless_tools_exist
from utils.nonexisting import assert_non_existing

apk1 = load_fixture('test1.apk')
apk2 = load_fixture('test2.apk')

def test_identification(apk1):
    assert isinstance(apk1, ApkFile)

def test_no_differences(apk1):
    difference = apk1.compare(apk1)
    assert difference is None

@pytest.fixture
def differences(apk1, apk2):
    return apk1.compare(apk2).details

@skip_unless_tools_exist('apktool', 'zipinfo')
def test_compare_non_existing(monkeypatch, apk1):
    assert_non_existing(monkeypatch, apk1)

@skip_unless_tools_exist('apktool', 'zipinfo')
def test_zipinfo(differences):
    assert differences[0].source1 == 'zipinfo {}'
    assert differences[0].source2 == 'zipinfo {}'
    expected_diff = open(data('apk_zipinfo_expected_diff')).read()
    assert differences[0].unified_diff == expected_diff

@skip_unless_tools_exist('apktool', 'zipinfo')
def test_android_manifest(differences):
    assert differences[2].source1 == 'AndroidManifest.xml'
    assert differences[2].source2 == 'AndroidManifest.xml'
    expected_diff = open(data('apk_manifest_expected_diff')).read()
    assert differences[2].unified_diff == expected_diff

@skip_unless_tools_exist('apktool', 'zipinfo')
def test_apk_metadata_source(differences):
    assert differences[1].source1 == 'APK metadata'
    assert differences[1].source2 == 'APK metadata'
