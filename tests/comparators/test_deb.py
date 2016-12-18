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

import diffoscope.comparators

from diffoscope.config import Config
from diffoscope.comparators import specialize
from diffoscope.comparators.deb import DebFile, Md5sumsFile, DebDataTarFile
from diffoscope.comparators.binary import FilesystemFile, NonExistingFile

from utils import data, load_fixture


deb1 = load_fixture(data('test1.deb'))
deb2 = load_fixture(data('test2.deb'))

def test_identification(deb1):
    assert isinstance(deb1, DebFile)

def test_no_differences(deb1):
    difference = deb1.compare(deb1)
    assert difference is None

@pytest.fixture
def differences(deb1, deb2):
    return deb1.compare(deb2).details

def test_metadata(differences):
    expected_diff = open(data('deb_metadata_expected_diff')).read()
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
    assert differences[1].details[0].details[1].details[0].comment == 'Files in package differ'

def test_identical_files_in_md5sums(deb1, deb2):
    for name in ['./usr/share/doc/test/README.Debian', './usr/share/doc/test/copyright']:
        assert deb1.md5sums[name] == deb2.md5sums[name]

def test_identification_of_data_tar(deb1, deb2, monkeypatch):
    orig_func = DebDataTarFile.recognizes
    @staticmethod
    def probe(file):
        ret = orig_func(file)
        if ret:
            test_identification_of_data_tar.found = True
        return ret
    test_identification_of_data_tar.found = False
    monkeypatch.setattr(DebDataTarFile, 'recognizes', probe)
    deb1.compare(deb2)
    assert test_identification_of_data_tar.found

def test_skip_comparison_of_known_identical_files(deb1, deb2, monkeypatch):
    compared = set()
    orig_func = diffoscope.comparators.compare_files
    def probe(file1, file2, source=None):
        compared.add(file1.name)
        return orig_func(file1, file2, source=None)
    monkeypatch.setattr(diffoscope.comparators, 'compare_files', probe)
    deb1.compare(deb2)
    assert './usr/share/doc/test/README.Debian' not in compared

def test_compare_non_existing(monkeypatch, deb1):
    monkeypatch.setattr(Config(), 'new_file', True)
    difference = deb1.compare(NonExistingFile('/nonexisting', deb1))
    assert difference.source2 == '/nonexisting'
    assert difference.details[-1].source2 == '/dev/null'
