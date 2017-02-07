# -*- coding: utf-8 -*-
#
# diffoscope: in-depth comparison of files, archives, and directories
#
# Copyright © 2016 Chris Lamb <lamby@debian.org>
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

import sys
import logging

from ..profiling import profile

from .text import TextPresenter
from .json import JSONPresenter
from .html import output_html, output_html_directory
from .utils import make_printer
from .markdown import MarkdownTextPresenter
from .restructuredtext import RestructuredTextPresenter

logger = logging.getLogger(__name__)


def output_all(difference, parsed_args, has_differences):
    """
    Generate all known output formats.
    """

    if difference is None:
        return

    FORMATS = {
        'text': {
            'fn': text,
            'target': parsed_args.text_output,
        },
        'html': {
            'fn': html,
            'target': parsed_args.html_output,
        },
        'json': {
            'klass': JSONPresenter,
            'target': parsed_args.json_output,
        },
        'markdown': {
            'klass': MarkdownTextPresenter,
            'target': parsed_args.markdown_output,
        },
        'restructuredtext': {
            'klass': RestructuredTextPresenter,
            'target': parsed_args.restructuredtext_output,
        },
        'html_directory': {
            'fn': html_directory,
            'target': parsed_args.html_output_directory,
        },
    }

    # If no output specified, default to printing --text output to stdout
    if not any(x['target'] for x in FORMATS.values()):
        parsed_args.text_output = FORMATS['text']['target'] = '-'

    for name, data in FORMATS.items():
        if data['target'] is None:
            continue

        logger.debug("Generating %r output at %r", name, data['target'])

        with profile('output', name):
            if 'fn' in data:
                data['fn'](difference, parsed_args, has_differences)
                continue

            with make_printer(data['target']) as fn:
                data['klass'](fn).start(difference)

def text(difference, parsed_args, has_differences):
    # As a special case, write an empty file instead of an empty diff.
    if not has_differences:
        open(parsed_args.text_output, 'w').close()
        return

    with make_printer(parsed_args.text_output or '-') as fn:
        color = {
            'auto': fn.output.isatty(),
            'never': False,
            'always': True,
        }[parsed_args.text_color]

        presenter = TextPresenter(fn, color)

        try:
            presenter.start(difference)
        except UnicodeEncodeError:
            logger.critical("Console is unable to print Unicode characters. "
                "Set e.g. PYTHONIOENCODING=utf-8")
            sys.exit(2)

def html(difference, parsed_args, has_differences):
    with make_printer(parsed_args.html_output) as fn:
        output_html(
            difference,
            css_url=parsed_args.css_url,
            print_func=fn,
        )

def html_directory(difference, parsed_args, has_differences):
    output_html_directory(
        parsed_args.html_output_directory,
        difference,
        css_url=parsed_args.css_url,
        jquery_url=parsed_args.jquery_url,
    )
