# -*- coding: utf-8 -*-
#
# diffoscope: in-depth comparison of files, archives, and directories
#
# Copyright © 2015 Jérémy Bobbio <lunar@debian.org>
#             2017 Chris Lamb <lamby@debian.org>
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

import os
import shutil
import pytest

from diffoscope.comparators.binary import FilesystemFile
from diffoscope.comparators.directory import compare_directories
from diffoscope.comparators.utils.specialize import specialize

from utils.data import data, get_data


TEST_FILE1_PATH = data('text_ascii1')
TEST_FILE2_PATH = data('text_ascii2')

def test_no_differences():
    difference = compare_directories(os.path.dirname(__file__), os.path.dirname(__file__))
    assert difference is None

def test_no_differences_with_extra_slash():
    difference = compare_directories(os.path.dirname(__file__) + '/', os.path.dirname(__file__))
    assert difference is None

@pytest.fixture
def differences(tmpdir):
    tmpdir.mkdir('a')
    tmpdir.mkdir('a/dir')
    tmpdir.mkdir('b')
    tmpdir.mkdir('b/dir')
    shutil.copy(TEST_FILE1_PATH, str(tmpdir.join('a/dir/text')))
    shutil.copy(TEST_FILE2_PATH, str(tmpdir.join('b/dir/text')))
    os.utime(str(tmpdir.join('a/dir/text')), (0, 0))
    os.utime(str(tmpdir.join('b/dir/text')), (0, 0))
    os.utime(str(tmpdir.join('a/dir')), (0, 0))
    os.utime(str(tmpdir.join('b/dir')), (0, 0))
    os.utime(str(tmpdir.join('a')), (0, 0))
    os.utime(str(tmpdir.join('b')), (0, 0))
    return compare_directories(str(tmpdir.join('a')), str(tmpdir.join('b'))).details

def test_content(differences):
    assert differences[0].source1 == 'dir'
    assert differences[0].details[0].source1 == 'text'
    expected_diff = get_data('text_ascii_expected_diff')
    assert differences[0].details[0].unified_diff == expected_diff

def test_stat(differences):
    assert 'stat' in differences[0].details[0].details[0].source1


def test_compare_to_file(tmpdir):
    path = str(tmpdir.join('file'))

    with open(path, 'w') as f:
        f.write("content")

    a = specialize(FilesystemFile(str(tmpdir.mkdir('dir'))))
    b = specialize(FilesystemFile(path))

    assert a.compare(b).unified_diff == get_data('test_directory_file_diff')

def test_compare_to_device(tmpdir):
    a = specialize(FilesystemFile(str(tmpdir.mkdir('dir'))))
    b = specialize(FilesystemFile('/dev/null'))

    assert a.compare(b).unified_diff == get_data('test_directory_device_diff')

def test_compare_to_symlink(tmpdir):
    path = str(tmpdir.join('src'))
    os.symlink('/etc/passwd', path)

    a = specialize(FilesystemFile(str(tmpdir.mkdir('dir'))))
    b = specialize(FilesystemFile(path))

    assert a.compare(b).unified_diff == get_data('test_directory_symlink_diff')

def test_compare_to_dangling_symlink(tmpdir):
    path = str(tmpdir.join('src'))
    os.symlink('/dangling', path)

    a = specialize(FilesystemFile(str(tmpdir.mkdir('dir'))))
    b = specialize(FilesystemFile(path))

    assert a.compare(b).unified_diff == get_data('test_directory_symlink_diff')
