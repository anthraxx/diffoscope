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
import shutil
import pytest
from diffoscope.comparators import specialize
from diffoscope.comparators.binary import FilesystemFile, NonExistingFile
try:
    from diffoscope.comparators.debian import DotChangesFile, DotDscFile, DotBuildinfoFile
    miss_debian_module = False
except ImportError:
    from diffoscope.comparators.debian_fallback import DotChangesFile, DotDscFile, DotBuildinfoFile
    miss_debian_module = True
from diffoscope.config import Config
from diffoscope.presenters.text import output_text

TEST_DOT_CHANGES_FILE1_PATH = os.path.join(os.path.dirname(__file__), '../data/test1.changes')
TEST_DOT_CHANGES_FILE2_PATH = os.path.join(os.path.dirname(__file__), '../data/test2.changes')
TEST_DEB_FILE1_PATH = os.path.join(os.path.dirname(__file__), '../data/test1.deb')
TEST_DEB_FILE2_PATH = os.path.join(os.path.dirname(__file__), '../data/test2.deb')

@pytest.fixture
def dot_changes1(tmpdir):
    tmpdir.mkdir('a')
    dot_changes_path = str(tmpdir.join('a/test_1.changes'))
    shutil.copy(TEST_DOT_CHANGES_FILE1_PATH, dot_changes_path)
    shutil.copy(TEST_DEB_FILE1_PATH, str(tmpdir.join('a/test_1_all.deb')))
    return specialize(FilesystemFile(dot_changes_path))

@pytest.fixture
def dot_changes2(tmpdir):
    tmpdir.mkdir('b')
    dot_changes_path = str(tmpdir.join('b/test_1.changes'))
    shutil.copy(TEST_DOT_CHANGES_FILE2_PATH, dot_changes_path)
    shutil.copy(TEST_DEB_FILE2_PATH, str(tmpdir.join('b/test_1_all.deb')))
    return specialize(FilesystemFile(dot_changes_path))

def test_dot_changes_identification(dot_changes1):
    assert isinstance(dot_changes1, DotChangesFile)

@pytest.mark.skipif(miss_debian_module, reason='debian module is not installed')
def test_dot_changes_invalid(tmpdir):
    tmpdir.mkdir('a')
    dot_changes_path = str(tmpdir.join('a/test_1.changes'))
    shutil.copy(TEST_DOT_CHANGES_FILE1_PATH, dot_changes_path)
    # we don't copy the referenced .deb
    identified = specialize(FilesystemFile(dot_changes_path))
    assert not isinstance(identified, DotChangesFile)

def test_dot_changes_no_differences(dot_changes1):
    difference = dot_changes1.compare(dot_changes1)
    assert difference is None

@pytest.fixture
def dot_changes_differences(dot_changes1, dot_changes2):
    difference = dot_changes1.compare(dot_changes2)
    output_text(difference, print_func=print)
    return difference.details

@pytest.mark.skipif(miss_debian_module, reason='debian module is not installed')
def test_dot_changes_description(dot_changes_differences):
    assert dot_changes_differences[0]
    expected_diff = open(os.path.join(os.path.dirname(__file__), '../data/dot_changes_description_expected_diff')).read()
    assert dot_changes_differences[0].unified_diff == expected_diff

@pytest.mark.skipif(miss_debian_module, reason='debian module is not installed')
def test_dot_changes_internal_diff(dot_changes_differences):
    assert dot_changes_differences[2].source1 == 'test_1_all.deb'

@pytest.mark.skipif(miss_debian_module, reason='debian module is not installed')
def test_dot_changes_compare_non_existing(monkeypatch, dot_changes1):
    monkeypatch.setattr(Config.general, 'new_file', True)
    difference = dot_changes1.compare(NonExistingFile('/nonexisting', dot_changes1))
    output_text(difference, print_func=print)
    assert difference.source2 == '/nonexisting'
    assert difference.details[-1].source2 == '/dev/null'

TEST_DOT_DSC_FILE1_PATH = os.path.join(os.path.dirname(__file__), '../data/test1.dsc')
TEST_DOT_DSC_FILE2_PATH = os.path.join(os.path.dirname(__file__), '../data/test2.dsc')
TEST_DEB_SRC1_PATH = os.path.join(os.path.dirname(__file__), '../data/test1.debsrc.tar.gz')
TEST_DEB_SRC2_PATH = os.path.join(os.path.dirname(__file__), '../data/test2.debsrc.tar.gz')

@pytest.fixture
def dot_dsc1(tmpdir):
    tmpdir.mkdir('a')
    dot_dsc_path = str(tmpdir.join('a/test_1.dsc'))
    shutil.copy(TEST_DOT_DSC_FILE1_PATH, dot_dsc_path)
    shutil.copy(TEST_DEB_SRC1_PATH, str(tmpdir.join('a/test_1.tar.gz')))
    return specialize(FilesystemFile(dot_dsc_path))

@pytest.fixture
def dot_dsc2(tmpdir):
    tmpdir.mkdir('b')
    dot_dsc_path = str(tmpdir.join('b/test_1.dsc'))
    shutil.copy(TEST_DOT_DSC_FILE2_PATH, dot_dsc_path)
    shutil.copy(TEST_DEB_SRC2_PATH, str(tmpdir.join('b/test_1.tar.gz')))
    return specialize(FilesystemFile(dot_dsc_path))

def test_dot_dsc_identification(dot_dsc1):
    assert isinstance(dot_dsc1, DotDscFile)

@pytest.mark.skipif(miss_debian_module, reason='debian module is not installed')
def test_dot_dsc_invalid(tmpdir, dot_dsc2):
    tmpdir.mkdir('a')
    dot_dsc_path = str(tmpdir.join('a/test_1.dsc'))
    shutil.copy(TEST_DOT_CHANGES_FILE1_PATH, dot_dsc_path)
    # we don't copy the referenced .tar.gz
    identified = specialize(FilesystemFile(dot_dsc_path))
    assert not isinstance(identified, DotDscFile)

def test_dot_dsc_no_differences(dot_dsc1):
    difference = dot_dsc1.compare(dot_dsc1)
    assert difference is None

@pytest.fixture
def dot_dsc_differences(dot_dsc1, dot_dsc2):
    difference = dot_dsc1.compare(dot_dsc2)
    output_text(difference, print_func=print)
    return difference.details

@pytest.mark.skipif(miss_debian_module, reason='debian module is not installed')
def test_dot_dsc_internal_diff(dot_dsc_differences):
    assert dot_dsc_differences[1].source1 == 'test_1.tar.gz'

@pytest.mark.skipif(miss_debian_module, reason='debian module is not installed')
def test_dot_dsc_compare_non_existing(monkeypatch, dot_dsc1):
    monkeypatch.setattr(Config.general, 'new_file', True)
    difference = dot_dsc1.compare(NonExistingFile('/nonexisting', dot_dsc1))
    output_text(difference, print_func=print)
    assert difference.source2 == '/nonexisting'
    assert difference.details[-1].source2 == '/dev/null'

TEST_DOT_BUILDINFO_FILE1_PATH = os.path.join(os.path.dirname(__file__), '../data/test1.buildinfo')
TEST_DOT_BUILDINFO_FILE2_PATH = os.path.join(os.path.dirname(__file__), '../data/test2.buildinfo')

@pytest.fixture
def dot_buildinfo1(tmpdir):
    tmpdir.mkdir('a')
    dot_buildinfo_path = str(tmpdir.join('a/test_1.buildinfo'))
    shutil.copy(TEST_DOT_BUILDINFO_FILE1_PATH, dot_buildinfo_path)
    shutil.copy(TEST_DOT_DSC_FILE1_PATH, str(tmpdir.join('a/test_1.dsc')))
    shutil.copy(TEST_DEB_FILE1_PATH, str(tmpdir.join('a/test_1_all.deb')))
    return specialize(FilesystemFile(dot_buildinfo_path))

@pytest.fixture
def dot_buildinfo2(tmpdir):
    tmpdir.mkdir('b')
    dot_buildinfo_path = str(tmpdir.join('b/test_1.buildinfo'))
    shutil.copy(TEST_DOT_BUILDINFO_FILE2_PATH, dot_buildinfo_path)
    shutil.copy(TEST_DOT_DSC_FILE2_PATH, str(tmpdir.join('b/test_1.dsc')))
    shutil.copy(TEST_DEB_FILE2_PATH, str(tmpdir.join('b/test_1_all.deb')))
    return specialize(FilesystemFile(dot_buildinfo_path))

def test_dot_buildinfo_identification(dot_buildinfo1):
    assert isinstance(dot_buildinfo1, DotBuildinfoFile)

@pytest.mark.skipif(miss_debian_module, reason='debian module is not installed')
def test_dot_buildinfo_invalid(tmpdir):
    tmpdir.mkdir('a')
    dot_buildinfo_path = str(tmpdir.join('a/test_1.buildinfo'))
    shutil.copy(TEST_DOT_BUILDINFO_FILE1_PATH, dot_buildinfo_path)
    # we don't copy the referenced .deb
    identified = specialize(FilesystemFile(dot_buildinfo_path))
    assert not isinstance(identified, DotBuildinfoFile)

def test_dot_buildinfo_no_differences(dot_buildinfo1):
    difference = dot_buildinfo1.compare(dot_buildinfo1)
    assert difference is None

@pytest.fixture
def dot_buildinfo_differences(dot_buildinfo1, dot_buildinfo2):
    difference = dot_buildinfo1.compare(dot_buildinfo2)
    output_text(difference, print_func=print)
    return difference.details

@pytest.mark.skipif(miss_debian_module, reason='debian module is not installed')
def test_dot_buildinfo_internal_diff(dot_buildinfo_differences):
    assert dot_buildinfo_differences[1].source1 == 'test_1_all.deb'

@pytest.mark.skipif(miss_debian_module, reason='debian module is not installed')
def test_dot_buildinfo_compare_non_existing(monkeypatch, dot_buildinfo1):
    monkeypatch.setattr(Config.general, 'new_file', True)
    difference = dot_buildinfo1.compare(NonExistingFile('/nonexisting', dot_buildinfo1))
    output_text(difference, print_func=print)
    assert difference.source2 == '/nonexisting'
    assert difference.details[-1].source2 == '/dev/null'
