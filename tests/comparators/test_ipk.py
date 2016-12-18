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

from diffoscope.config import Config
from diffoscope.comparators.ipk import IpkFile
from diffoscope.comparators.binary import NonExistingFile

from utils import data, load_fixture

ipk1 = load_fixture(data('base-files_157-r45695_ar71xx.ipk'))
ipk2 = load_fixture(data('base-files_157-r45918_ar71xx.ipk'))

def test_identification(ipk1):
    assert isinstance(ipk1, IpkFile)

def test_no_differences(ipk1):
    difference = ipk1.compare(ipk1)
    assert difference is None

@pytest.fixture
def differences(ipk1, ipk2):
    return ipk1.compare(ipk2).details

def test_metadata(differences):
    assert differences[0].source1 == 'metadata'
    expected_diff = open(data('ipk_metadata_expected_diff')).read()
    assert differences[0].unified_diff == expected_diff

def test_compressed_files(differences):
    assert differences[1].details[1].source1 == './data.tar.gz'
    assert differences[1].details[2].source1 == './control.tar.gz'

def test_compare_non_existing(monkeypatch, ipk1):
    monkeypatch.setattr(Config(), 'new_file', True)
    difference = ipk1.compare(NonExistingFile('/nonexisting', ipk1))
    assert difference.source2 == '/nonexisting'
    assert difference.details[-1].source2 == '/dev/null'
