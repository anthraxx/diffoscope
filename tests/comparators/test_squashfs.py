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
# along with diffoscope.  If not, see <http://www.gnu.org/licenses/>.

import os.path
import pwd
import pytest
from diffoscope.comparators import specialize
from diffoscope.comparators.binary import FilesystemFile, NonExistingFile
from diffoscope.comparators.squashfs import SquashfsFile
from diffoscope.config import Config
from conftest import tool_missing, try_except

TEST_FILE1_PATH = os.path.join(os.path.dirname(__file__), '../data/test1.squashfs')
TEST_FILE2_PATH = os.path.join(os.path.dirname(__file__), '../data/test2.squashfs')

@pytest.fixture
def squashfs1():
    return specialize(FilesystemFile(TEST_FILE1_PATH))

@pytest.fixture
def squashfs2():
    return specialize(FilesystemFile(TEST_FILE2_PATH))

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

@pytest.mark.skipif(tool_missing('unsquashfs'), reason='missing unsquashfs')
def test_superblock(differences):
    expected_diff = open(os.path.join(os.path.dirname(__file__), '../data/squashfs_superblock_expected_diff')).read()
    assert differences[0].unified_diff == expected_diff

# I know, the next line is pretty lame. But fixing #794096 would be the real fix for this.
@pytest.mark.skipif(try_except(lambda: pwd.getpwuid(1000).pw_name != 'lunar', True, KeyError), reason='uid 1000 is not lunar')
@pytest.mark.skipif(tool_missing('unsquashfs'), reason='missing unsquashfs')
def test_listing(differences):
    expected_diff = open(os.path.join(os.path.dirname(__file__), '../data/squashfs_listing_expected_diff')).read()
    assert differences[1].unified_diff == expected_diff

@pytest.mark.skipif(tool_missing('unsquashfs'), reason='missing unsquashfs')
def test_symlink(differences):
    assert differences[2].comment == 'symlink'
    expected_diff = open(os.path.join(os.path.dirname(__file__), '../data/symlink_expected_diff')).read()
    assert differences[2].unified_diff == expected_diff

@pytest.mark.skipif(tool_missing('unsquashfs'), reason='missing unsquashfs')
def test_compressed_files(differences):
    assert differences[3].source1 == '/text'
    assert differences[3].source2 == '/text'
    expected_diff = open(os.path.join(os.path.dirname(__file__), '../data/text_ascii_expected_diff')).read()
    assert differences[3].unified_diff == expected_diff

@pytest.mark.skipif(tool_missing('unsquashfs'), reason='missing unsquashfs')
def test_compare_non_existing(monkeypatch, squashfs1):
    monkeypatch.setattr(Config.general, 'new_file', True)
    difference = squashfs1.compare(NonExistingFile('/nonexisting', squashfs1))
    assert difference.source2 == '/nonexisting'
    assert difference.details[-1].source2 == '/dev/null'
