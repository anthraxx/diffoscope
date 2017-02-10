# -*- coding: utf-8 -*-
#
# diffoscope: in-depth comparison of files, archives, and directories
#
# Copyright © 2017 Chris Lamb <lamby@debian.org>
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
import pytest

from diffoscope.main import main


def run(capsys, *args):
    with pytest.raises(SystemExit) as exc:
        main(args + tuple(
            os.path.join(os.path.dirname(__file__), 'data', x)
            for x in ('test1.tar', 'test2.tar')
        ))

    out, err = capsys.readouterr()

    assert err == ''

    return exc.value.code, out

def test_none(capsys):
    ret, out = run(capsys)

    assert ret == 1
    assert '── dir/text' in out
    assert '── dir/link' in out

def test_all(capsys):
    ret, out = run(capsys, '--exclude=*')

    assert ret == 0
    assert out == ''

def test_specific(capsys):
    ret, out = run(capsys, '--exclude=dir/text')

    assert ret == 1
    assert '── dir/text' not in out
    assert '── dir/link' in out

def test_specific_case(capsys):
    ret, out = run(capsys, '--exclude=dir/TEXT')

    assert ret == 1
    assert '── dir/text' in out
    assert '── dir/link' in out

def test_multiple(capsys):
    ret, out = run(capsys, '--exclude=dir/text', '--exclude=dir/link')

    assert ret == 1
    assert '── dir/text' not in out
    assert '── dir/link' not in out

def test_nomatch(capsys):
    ret, out = run(capsys, '--exclude=nomatch')

    assert ret == 1
    assert '── dir/text' in out
    assert '── dir/link' in out

def test_wildcard(capsys):
    ret, out = run(capsys, '--exclude=*link')

    assert ret == 1
    assert '── dir/text' in out
    assert '── dir/link' not in out
