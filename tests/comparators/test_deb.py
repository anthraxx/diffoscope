#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# debbindiff: highlight differences between two builds of Debian packages
#
# Copyright © 2015 Jérémy Bobbio <lunar@debian.org>
#
# debbindiff is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# debbindiff is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with debbindiff.  If not, see <http://www.gnu.org/licenses/>.

import codecs
import os.path
import shutil
import pytest
from debbindiff.comparators import specialize
from debbindiff.comparators.binary import FilesystemFile
from debbindiff.comparators.deb import DebFile, Md5sumsFile

TEST_FILE1_PATH = os.path.join(os.path.dirname(__file__), '../data/test1.deb')
TEST_FILE2_PATH = os.path.join(os.path.dirname(__file__), '../data/test2.deb')

@pytest.fixture
def deb1():
    return specialize(FilesystemFile(TEST_FILE1_PATH))

@pytest.fixture
def deb2():
    return specialize(FilesystemFile(TEST_FILE2_PATH))

def test_identification(deb1):
    assert isinstance(deb1, DebFile)

def test_no_differences(deb1):
    difference = deb1.compare(deb1)
    assert difference is None

@pytest.fixture
def differences(deb1, deb2):
    return deb1.compare(deb2).details

def test_metadata(differences):
    expected_diff = open(os.path.join(os.path.dirname(__file__), '../data/deb_metadata_expected_diff')).read()
    assert differences[0].unified_diff == expected_diff

def test_compressed_files(differences):
    assert differences[1].source1 == 'control.tar.gz'
    assert differences[2].source1 == 'data.tar.gz'

def test_identification_of_md5sums_outside_deb(tmpdir):
    path = str(tmpdir.join('md5sums'))
    open(path, 'w')
    f = specialize(FilesystemFile(path))
    assert type(f) is FilesystemFile

def test_identification_of_md5sums_in_deb(deb1, deb2, monkeypatch):
    orig_func = Md5sumsFile.recognizes
    @staticmethod
    def probe(file):
        ret = orig_func(file)
        if ret:
            test_identification_of_md5sums_in_deb.found = True
        return ret
    test_identification_of_md5sums_in_deb.found = False
    monkeypatch.setattr(Md5sumsFile, 'recognizes', probe)
    deb1.compare(deb2)
    assert test_identification_of_md5sums_in_deb.found

def test_md5sums(differences):
    assert differences[1].details[0].details[1].comment == 'Files in package differs'