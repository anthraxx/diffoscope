# -*- coding: utf-8 -*-
#
# diffoscope: in-depth comparison of files, archives, and directories
#
# Copyright © 2015 Reiner Herrmann <reiner@reiner-h.de>
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
# along with diffoscope.  If not, see <http://www.gnu.org/licenses/>.

import os.path
import pytest
try:
    import guestfs
    miss_guestfs = False
except ImportError:
    miss_guestfs = True
from diffoscope.comparators import specialize
from diffoscope.comparators.binary import FilesystemFile, NonExistingFile
from diffoscope.comparators.fsimage import FsImageFile
from diffoscope.config import Config
from conftest import tool_missing

TEST_FILE1_PATH = os.path.join(os.path.dirname(__file__), '../data/test1.ext4')
TEST_FILE2_PATH = os.path.join(os.path.dirname(__file__), '../data/test2.ext4')

def guestfs_working():
    if miss_guestfs:
        return False
    g = guestfs.GuestFS (python_return_dict=True)
    g.add_drive_opts("/dev/null", format="raw", readonly=1)
    try:
        g.launch()
    except RuntimeError:
        return False
    return True

@pytest.fixture
def img1():
    return specialize(FilesystemFile(TEST_FILE1_PATH))

@pytest.fixture
def img2():
    return specialize(FilesystemFile(TEST_FILE2_PATH))

def test_identification(img1):
    assert isinstance(img1, FsImageFile)

@pytest.mark.skipif(not guestfs_working(), reason='guestfs not working on the system')
@pytest.mark.skipif(tool_missing('qemu-img'), reason='missing qemu-img')
@pytest.mark.skipif(miss_guestfs, reason='guestfs is missing')
def test_no_differences(img1):
    difference = img1.compare(img1)
    assert difference is None

@pytest.fixture
def differences(img1, img2):
    return img1.compare(img2).details

@pytest.mark.skipif(not guestfs_working(), reason='guestfs not working on the system')
@pytest.mark.skipif(tool_missing('qemu-img'), reason='missing qemu-img')
@pytest.mark.skipif(miss_guestfs, reason='guestfs is missing')
def test_differences(differences):
    assert differences[0].source1 == 'test1.ext4.tar'
    tarinfo = differences[0].details[0]
    tardiff = differences[0].details[1]
    encodingdiff = tardiff.details[0]
    assert tarinfo.source1 == 'file list'
    assert tarinfo.source2 == 'file list'
    assert tardiff.source1 == './date.txt'
    assert tardiff.source2 == './date.txt'
    assert encodingdiff.source1 == 'encoding'
    assert encodingdiff.source2 == 'encoding'
    expected_diff = open(os.path.join(os.path.dirname(__file__), '../data/ext4_expected_diffs'), encoding='utf-8').read()
    found_diff = tarinfo.unified_diff + tardiff.unified_diff + encodingdiff.unified_diff
    assert expected_diff == found_diff

@pytest.mark.skipif(not guestfs_working(), reason='guestfs not working on the system')
@pytest.mark.skipif(tool_missing('qemu-img'), reason='missing qemu-img')
@pytest.mark.skipif(miss_guestfs, reason='guestfs is missing')
def test_compare_non_existing(monkeypatch, img1):
    monkeypatch.setattr(Config.general, 'new_file', True)
    difference = img1.compare(NonExistingFile('/nonexisting', img1))
    assert difference.source2 == '/nonexisting'
    assert difference.details[-1].source2 == '/dev/null'
