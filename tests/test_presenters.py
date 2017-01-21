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
    args = list(args) + [
        os.path.join(os.path.dirname(__file__), 'data', x)
        for x in ('test1.tar', 'test2.tar')
    ]

    with pytest.raises(SystemExit) as exc:
        main(args)

    out, err = capsys.readouterr()

    assert err == ''
    assert exc.value.code == 1

    return out

def test_text_option_with_file(tmpdir, capsys):
    report_path = str(tmpdir.join('report.txt'))

    out = run(capsys, '--text', report_path)

    assert out == ''
    with open(report_path, 'r', encoding='utf-8') as f:
        assert f.read().startswith('--- ')

def test_text_option_with_stdiout(capsys):
    out = run(capsys, '--text', '-')

    assert out.startswith('--- ')

def test_markdown(capsys):
    out = run(capsys, '--markdown', '-')

    assert out.startswith('# Comparing')

def test_restructuredtext(capsys):
    out = run(capsys, '--restructured-text', '-')

    assert out.startswith('=====')
    assert "Comparing" in out

def test_no_report_option(capsys):
    out = run(capsys)

    assert out.startswith('--- ')

def test_html_option_with_file(tmpdir, capsys):
    report_path = str(tmpdir.join('report.html'))

    out = run(capsys, '--html', report_path)

    assert out == ''
    with open(report_path, 'r', encoding='utf-8') as f:
        assert 'meta name="generator" content="diffoscope"' in f.read()

def test_htmldir_option(tmpdir, capsys):
    html_dir = os.path.join(str(tmpdir), 'target')

    out = run(capsys, '--html-dir', html_dir, '--jquery', 'disable')

    assert out == ''
    assert os.path.isdir(html_dir)
    with open(os.path.join(html_dir, 'index.html'), 'r', encoding='utf-8') as f:
        assert 'meta name="generator" content="diffoscope"' in f.read()

def test_html_option_with_stdout(capsys):
    out = run(capsys, '--html', '-')

    assert 'meta name="generator" content="diffoscope"' in out
