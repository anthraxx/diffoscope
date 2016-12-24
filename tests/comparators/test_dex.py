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

from diffoscope.config import Config
from diffoscope.comparators.dex import DexFile
from diffoscope.comparators.binary import NonExistingFile

from utils import skip_unless_tools_exist, data, load_fixture, skip_unless_tool_is_at_least
from test_java import javap_version


dex1 = load_fixture(data('test1.dex'))
dex2 = load_fixture(data('test2.dex'))

def enjarify_version():
    # Module enjarify.typeinference appeared in enjarify 1.0.3.  We use a call
    # directly to the python3 binary over importing with this module to escape
    # virtualenvs, etc.
    if subprocess.call(
        ('python3', '-c', 'import enjarify.typeinference'),
        stderr=subprocess.PIPE,
    ) == 0:
        return '1.0.3'
    return '1.0.2'

def test_identification(dex1):
    assert isinstance(dex1, DexFile)

def test_no_differences(dex1):
    difference = dex1.compare(dex1)
    assert difference is None

@pytest.fixture
def differences(dex1, dex2):
    return dex1.compare(dex2).details

@skip_unless_tools_exist('enjarify', 'zipinfo', 'javap')
@skip_unless_tool_is_at_least('javap', javap_version, '1.8')
@skip_unless_tool_is_at_least('enjarify', enjarify_version, '1.0.3')
def test_differences(differences):
    assert differences[0].source1 == 'test1.jar'
    assert differences[0].source2 == 'test2.jar'
    zipinfo = differences[0].details[0]
    classdiff = differences[0].details[1]
    assert zipinfo.source1 == 'zipinfo -v {}'
    assert zipinfo.source2 == 'zipinfo -v {}'
    assert classdiff.source1 == 'com/example/MainActivity.class'
    assert classdiff.source2 == 'com/example/MainActivity.class'
    expected_diff = open(data('dex_expected_diffs')).read()
    found_diff = zipinfo.unified_diff + classdiff.details[0].unified_diff
    assert expected_diff == found_diff

@skip_unless_tools_exist('enjarify', 'zipinfo', 'javap')
def test_compare_non_existing(monkeypatch, dex1):
    monkeypatch.setattr(Config(), 'new_file', True)
    difference = dex1.compare(NonExistingFile('/nonexisting', dex1))
    assert difference.source2 == '/nonexisting'
    assert difference.details[-1].source2 == '/dev/null'
