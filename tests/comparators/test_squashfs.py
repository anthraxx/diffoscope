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
import subprocess

from diffoscope.comparators.squashfs import SquashfsFile

from utils import skip_unless_tools_exist, data, load_fixture, \
    assert_non_existing, skip_unless_tool_is_at_least

def unsquashfs_version():
    # first line of 'unsquashfs -version' looks like:
    #   unsquashfs version 4.2-git (2013/03/13)
    try:
        out = subprocess.check_output(['unsquashfs', '-version'])
    except subprocess.CalledProcessError as e:
        out = e.output
    return out.decode('UTF-8').splitlines()[0].split()[2].strip()

squashfs1 = load_fixture(data('test1.squashfs'))
squashfs2 = load_fixture(data('test2.squashfs'))

def test_identification(squashfs1):
    assert isinstance(squashfs1, SquashfsFile)

def test_no_differences(squashfs1):
    difference = squashfs1.compare(squashfs1)
    assert difference is None

def test_no_warnings(capfd, squashfs1, squashfs2):
    _ = squashfs1.compare(squashfs2)
    _, err = capfd.readouterr()
    assert err == ''

@pytest.fixture
def differences(squashfs1, squashfs2):
    return squashfs1.compare(squashfs2).details

@skip_unless_tool_is_at_least('unsquashfs', unsquashfs_version, '4.3')
def test_superblock(differences):
    expected_diff = open(data('squashfs_superblock_expected_diff')).read()
    assert differences[0].unified_diff == expected_diff

@skip_unless_tools_exist('unsquashfs')
def test_symlink(differences):
    assert differences[2].comment == 'symlink'
    expected_diff = open(data('symlink_expected_diff')).read()
    assert differences[2].unified_diff == expected_diff

@skip_unless_tools_exist('unsquashfs')
def test_compressed_files(differences):
    assert differences[3].source1 == '/text'
    assert differences[3].source2 == '/text'
    expected_diff = open(data('text_ascii_expected_diff')).read()
    assert differences[3].unified_diff == expected_diff

@skip_unless_tools_exist('unsquashfs')
def test_compare_non_existing(monkeypatch, squashfs1):
    assert_non_existing(monkeypatch, squashfs1)
