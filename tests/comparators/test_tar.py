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
from diffoscope.comparators.tar import TarFile
from diffoscope.comparators.binary import NonExistingFile

from utils import data, load_fixture, assert_non_existing

tar1 = load_fixture(data('test1.tar'))
tar2 = load_fixture(data('test2.tar'))

def test_identification(tar1):
    assert isinstance(tar1, TarFile)

def test_no_differences(tar1):
    difference = tar1.compare(tar1)
    assert difference is None

@pytest.fixture
def differences(tar1, tar2):
    return tar1.compare(tar2).details

def test_listing(differences):
    expected_diff = open(data('tar_listing_expected_diff')).read()
    assert differences[0].unified_diff == expected_diff

def test_symlinks(differences):
    assert differences[2].source1 == 'dir/link'
    assert differences[2].source2 == 'dir/link'
    assert differences[2].comment == 'symlink'
    expected_diff = open(data('symlink_expected_diff')).read()
    assert differences[2].unified_diff == expected_diff

def test_text_file(differences):
    assert differences[1].source1 == 'dir/text'
    assert differences[1].source2 == 'dir/text'
    expected_diff = open(data('text_ascii_expected_diff')).read()
    assert differences[1].unified_diff == expected_diff

def test_compare_non_existing(monkeypatch, tar1):
    assert_non_existing(monkeypatch, tar1)

no_permissions_tar = load_fixture(data('no-perms.tar'))

# Reported as Debian #797164. This is a good way to notice if we unpack directories
# as we won't be able to remove files in one if we don't have write permissions.
def test_no_permissions_dir_in_tarball(monkeypatch, no_permissions_tar):
    # We want to make sure OSError is not raised.
    # Comparing with non-existing file makes it easy to make sure all files are unpacked
    monkeypatch.setattr(Config(), 'new_file', True)
    no_permissions_tar.compare(NonExistingFile('/nonexistent', no_permissions_tar))
