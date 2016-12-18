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

from diffoscope.comparators.pdf import PdfFile

from utils import skip_unless_tools_exist, data, load_fixture, \
    assert_non_existing

pdf1 = load_fixture(data('test1.pdf'))
pdf2 = load_fixture(data('test2.pdf'))

def test_identification(pdf1):
    assert isinstance(pdf1, PdfFile)

def test_no_differences(pdf1):
    difference = pdf1.compare(pdf1)
    assert difference is None

@pytest.fixture
def differences(pdf1, pdf2):
    return pdf1.compare(pdf2).details

@skip_unless_tools_exist('pdftk', 'pdftotext')
def test_text_diff(differences):
    expected_diff = open(data('pdf_text_expected_diff')).read()
    assert differences[0].unified_diff == expected_diff

@skip_unless_tools_exist('pdftk', 'pdftotext')
def test_internal_diff(differences):
    expected_diff = open(data('pdf_internal_expected_diff')).read()
    assert differences[1].unified_diff == expected_diff

@skip_unless_tools_exist('pdftk', 'pdftotext')
def test_compare_non_existing(monkeypatch, pdf1):
    assert_non_existing(monkeypatch, pdf1, has_null_source=False)
