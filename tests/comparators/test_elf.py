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
import pytest
from diffoscope.comparators import specialize
from diffoscope.comparators.binary import FilesystemFile, NonExistingFile
try:
    import diffoscope.comparators.debian
    miss_debian_module = False
except ImportError:
    miss_debian_module = True
from diffoscope.comparators.directory import FilesystemDirectory
from diffoscope.comparators.elf import ElfFile, StaticLibFile
from diffoscope.config import Config
from diffoscope.presenters.text import output_text
from conftest import tool_missing

TEST_OBJ1_PATH = os.path.join(os.path.dirname(__file__), '../data/test1.o')
TEST_OBJ2_PATH = os.path.join(os.path.dirname(__file__), '../data/test2.o')

@pytest.fixture
def obj1():
    return specialize(FilesystemFile(TEST_OBJ1_PATH))

@pytest.fixture
def obj2():
    return specialize(FilesystemFile(TEST_OBJ2_PATH))

def test_obj_identification(obj1):
    assert isinstance(obj1, ElfFile)

def test_obj_no_differences(obj1):
    difference = obj1.compare(obj1)
    assert difference is None

@pytest.fixture
def obj_differences(obj1, obj2):
    return obj1.compare(obj2).details

@pytest.mark.skipif(tool_missing('readelf'), reason='missing readelf')
def test_obj_compare_non_existing(monkeypatch, obj1):
    monkeypatch.setattr(Config, 'new_file', True)
    difference = obj1.compare(NonExistingFile('/nonexisting', obj1))
    assert difference.source2 == '/nonexisting'
    assert len(difference.details) > 0

@pytest.mark.skipif(tool_missing('readelf'), reason='missing readelf')
def test_diff(obj_differences):
    assert len(obj_differences) == 1
    expected_diff = open(os.path.join(os.path.dirname(__file__), '../data/elf_obj_expected_diff')).read()
    assert obj_differences[0].unified_diff == expected_diff

TEST_LIB1_PATH = os.path.join(os.path.dirname(__file__), '../data/test1.a')
TEST_LIB2_PATH = os.path.join(os.path.dirname(__file__), '../data/test2.a')

@pytest.fixture
def lib1():
    return specialize(FilesystemFile(TEST_LIB1_PATH))

@pytest.fixture
def lib2():
    return specialize(FilesystemFile(TEST_LIB2_PATH))

def test_lib_identification(lib1):
    assert isinstance(lib1, StaticLibFile)

def test_lib_no_differences(lib1):
    difference = lib1.compare(lib1)
    assert difference is None

@pytest.fixture
def lib_differences(lib1, lib2):
    return lib1.compare(lib2).details

@pytest.mark.skipif(tool_missing('readelf') or tool_missing('objdump'), reason='missing readelf or objdump')
def test_lib_differences(lib_differences):
    assert len(lib_differences) == 2
    assert lib_differences[0].source1 == 'file list'
    expected_metadata_diff = open(os.path.join(os.path.dirname(__file__), '../data/elf_lib_metadata_expected_diff')).read()
    assert lib_differences[0].unified_diff == expected_metadata_diff
    assert 'objdump' in lib_differences[1].source1
    expected_objdump_diff = open(os.path.join(os.path.dirname(__file__), '../data/elf_lib_objdump_expected_diff')).read()
    assert lib_differences[1].unified_diff == expected_objdump_diff

@pytest.mark.skipif(tool_missing('readelf') or tool_missing('objdump'), reason='missing readelf')
def test_lib_compare_non_existing(monkeypatch, lib1):
    monkeypatch.setattr(Config, 'new_file', True)
    difference = lib1.compare(NonExistingFile('/nonexisting', lib1))
    assert difference.source2 == '/nonexisting'
    assert len(difference.details) > 0

TEST_DBGSYM_DEB1_PATH = os.path.join(os.path.dirname(__file__), '../data/dbgsym/add/test-dbgsym_1_amd64.deb')
TEST_DBGSYM_DEB2_PATH = os.path.join(os.path.dirname(__file__), '../data/dbgsym/mult/test-dbgsym_1_amd64.deb')

@pytest.fixture
def dbgsym_dir1():
    container = FilesystemDirectory(os.path.dirname(TEST_DBGSYM_DEB1_PATH)).as_container
    return specialize(FilesystemFile(TEST_DBGSYM_DEB1_PATH, container=container))

@pytest.fixture
def dbgsym_dir2():
    container = FilesystemDirectory(os.path.dirname(TEST_DBGSYM_DEB2_PATH)).as_container
    return specialize(FilesystemFile(TEST_DBGSYM_DEB2_PATH, container=container))

@pytest.fixture
def dbgsym_differences(dbgsym_dir1, dbgsym_dir2):
    return dbgsym_dir1.compare(dbgsym_dir2)

@pytest.mark.skipif(any([tool_missing(tool) for tool in ['readelf', 'objdump', 'objcopy']]), reason='missing readelf, objdump, or objcopy')
@pytest.mark.skipif(miss_debian_module, reason='debian module is not installed')
def test_differences_with_dbgsym(dbgsym_differences):
    output_text(dbgsym_differences, print)
    assert dbgsym_differences.details[2].source1 == 'data.tar.xz'
    bin_details = dbgsym_differences.details[2].details[0].details[0]
    assert bin_details.source1 == './usr/bin/test'
    assert bin_details.details[1].source1.startswith('objdump')
    assert 'test-cases/dbgsym/package/test.c:2' in bin_details.details[1].unified_diff

@pytest.mark.skipif(any([tool_missing(tool) for tool in ['readelf', 'objdump', 'objcopy']]), reason='missing readelf, objdump, or objcopy')
@pytest.mark.skipif(miss_debian_module, reason='debian module is not installed')
def test_original_gnu_debuglink(dbgsym_differences):
    bin_details = dbgsym_differences.details[2].details[0].details[0]
    assert '.gnu_debuglink' in bin_details.details[2].source1
    expected_gnu_debuglink = open(os.path.join(os.path.dirname(__file__), '../data/gnu_debuglink_expected_diff')).read()
    assert bin_details.details[2].unified_diff == expected_gnu_debuglink
