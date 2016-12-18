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
from diffoscope.comparators.zip import ZipFile
from diffoscope.comparators.binary import NonExistingFile

from utils import skip_unless_tools_exist, data, load_fixture

epub1 = load_fixture(data('test1.epub'))
epub2 = load_fixture(data('test2.epub'))

def test_identification(epub1):
    assert isinstance(epub1, ZipFile)

def test_no_differences(epub1):
    difference = epub1.compare(epub1)
    assert difference is None

@pytest.fixture
def differences(epub1, epub2):
    return epub1.compare(epub2).details

@skip_unless_tools_exist('zipinfo')
def test_differences(differences):
    assert differences[0].source1 == 'zipinfo {}'
    assert differences[0].source2 == 'zipinfo {}'
    assert differences[1].source1 == 'content.opf'
    assert differences[1].source2 == 'content.opf'
    assert differences[2].source1 == 'toc.ncx'
    assert differences[2].source2 == 'toc.ncx'
    assert differences[3].source1 == 'ch001.xhtml'
    assert differences[3].source2 == 'ch001.xhtml'
    expected_diff = open(data('epub_expected_diffs')).read()
    assert expected_diff == "".join(map(lambda x: x.unified_diff, differences))

@skip_unless_tools_exist('zipinfo')
def test_compare_non_existing(monkeypatch, epub1):
    monkeypatch.setattr(Config(), 'new_file', True)
    difference = epub1.compare(NonExistingFile('/nonexisting', epub1))
    assert difference.source2 == '/nonexisting'
    assert difference.details[-1].source2 == '/dev/null'
