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

import codecs
import os.path
import pytest
from diffoscope.comparators import specialize
from diffoscope.comparators.binary import FilesystemFile, NonExistingFile
from diffoscope.config import Config

@pytest.fixture
def fuzzy_tar1():
    return specialize(FilesystemFile(os.path.join(os.path.dirname(__file__), '../data/fuzzy1.tar')))

@pytest.fixture
def fuzzy_tar2():
    return specialize(FilesystemFile(os.path.join(os.path.dirname(__file__), '../data/fuzzy2.tar')))

@pytest.fixture
def fuzzy_tar3():
    return specialize(FilesystemFile(os.path.join(os.path.dirname(__file__), '../data/fuzzy3.tar')))

def test_fuzzy_matching(fuzzy_tar1, fuzzy_tar2):
    differences = fuzzy_tar1.compare(fuzzy_tar2).details
    expected_diff = codecs.open(os.path.join(os.path.dirname(__file__), '../data/text_iso8859_expected_diff'), encoding='utf-8').read()
    assert differences[1].source1 == './matching'
    assert differences[1].source2 == './fuzzy'
    assert 'similar' in differences[1].comment
    assert differences[1].unified_diff == expected_diff

def test_fuzzy_matching_only_once(fuzzy_tar1, fuzzy_tar3):
    differences = fuzzy_tar1.compare(fuzzy_tar3).details
    assert len(differences) == 2
    expected_diff = codecs.open(os.path.join(os.path.dirname(__file__), '../data/text_iso8859_expected_diff'), encoding='utf-8').read()

@pytest.fixture
def fuzzy_tar_in_tar1():
    return specialize(FilesystemFile(os.path.join(os.path.dirname(__file__), '../data/fuzzy-tar-in-tar1.tar')))

@pytest.fixture
def fuzzy_tar_in_tar2():
    return specialize(FilesystemFile(os.path.join(os.path.dirname(__file__), '../data/fuzzy-tar-in-tar2.tar')))

def test_no_fuzzy_matching(monkeypatch, fuzzy_tar_in_tar1, fuzzy_tar_in_tar2):
    monkeypatch.setattr(Config, 'fuzzy_threshold', 0)
    difference = fuzzy_tar_in_tar1.compare(fuzzy_tar_in_tar2)
    assert len(difference.details) == 1
    assert difference.details[0].source1 == 'tar --full-time -tvf {}'

def test_no_fuzzy_matching_new_file(monkeypatch, fuzzy_tar_in_tar1, fuzzy_tar_in_tar2):
    monkeypatch.setattr(Config, 'fuzzy_threshold', 0)
    monkeypatch.setattr(Config, 'new_file', True)
    difference = fuzzy_tar_in_tar1.compare(fuzzy_tar_in_tar2)
    assert len(difference.details) == 3
    assert difference.details[1].source2 == '/dev/null'
    assert difference.details[2].source1 == '/dev/null'
