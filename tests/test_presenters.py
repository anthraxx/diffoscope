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

TEST_TAR1_PATH = os.path.join(os.path.dirname(__file__), 'data/test1.tar')
TEST_TAR2_PATH = os.path.join(os.path.dirname(__file__), 'data/test2.tar')


def run(capsys, *args):
    with pytest.raises(SystemExit) as exc:
        main(args + (TEST_TAR1_PATH, TEST_TAR2_PATH))

    out, err = capsys.readouterr()

    return exc.value.code, out, err

def test_text_option_with_file(tmpdir, capsys):
    report_path = str(tmpdir.join('report.txt'))

    ret, out, err = run(capsys, '--text', report_path)

    assert ret == 1
    assert err == ''
    assert out == ''
    with open(report_path, 'r', encoding='utf-8') as f:
        assert f.read().startswith('--- ')

def test_text_option_with_stdiout(capsys):
    ret, out, err = run(capsys, '--text', '-')

    assert ret == 1
    assert err == ''
    assert out.startswith('--- ')

def test_markdown(capsys):
    ret, out, err = run(capsys, '--markdown', '-')

    assert ret == 1
    assert err == ''
    assert out.startswith('# Comparing')

def test_restructuredtext(capsys):
    ret, out, err = run(capsys, '--restructured-text', '-')

    assert ret == 1
    assert err == ''
    assert out.startswith('=====')
    assert "Comparing" in out

def test_no_report_option(capsys):
    ret, out, err = run(capsys)

    assert ret == 1
    assert err == ''
    assert out.startswith('--- ')

def test_html_option_with_file(tmpdir, capsys):
    report_path = str(tmpdir.join('report.html'))

    ret, out, err = run(capsys, '--html', report_path)

    assert ret == 1
    assert err == ''
    assert out == ''
    with open(report_path, 'r', encoding='utf-8') as f:
        assert 'meta name="generator" content="diffoscope"' in f.read()

def test_htmldir_option(tmpdir, capsys):
    html_dir = os.path.join(str(tmpdir), 'target')

    ret, out, err = run(
        capsys,
        '--html-dir', html_dir,
        '--jquery', 'disable',
    )

    assert ret == 1
    assert err == ''
    assert out == ''
    assert os.path.isdir(html_dir)

    with open(os.path.join(html_dir, 'index.html'), 'r', encoding='utf-8') as f:
        assert 'meta name="generator" content="diffoscope"' in f.read()

def test_html_option_with_stdout(capsys):
    ret, out, err = run(capsys, '--html', '-')

    assert ret == 1
    assert err == ''
    assert 'meta name="generator" content="diffoscope"' in out
