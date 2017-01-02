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
import codecs
import contextlib

from ..logging import logger
from ..profiling import ProfileManager, profile

from .text import output_text
from .html import output_html, output_html_directory


def output_all(difference, parsed_args, has_differences):
    """
    Generate all known output formats.
    """

    # If no output specified, default to printing --text output to stdout
    if not any((
        parsed_args.text_output,
        parsed_args.html_output,
        parsed_args.html_output_directory,
    )):
        parsed_args.text_output = '-'

    for name, fn, target in (
        ('text', text, parsed_args.text_output),
        ('html', html, parsed_args.html_output),
        ('html_directory', html_directory, parsed_args.html_output_directory),
        ('profile', profiling, parsed_args.profile_output),
    ):
        if target is None:
            continue

        logger.debug("Generating %r output at %r", name, target)

        with profile('output', name):
            fn(difference, parsed_args, has_differences)

def text(difference, parsed_args, has_differences):
    if difference is None:
        return

    # As a sppecial case, write an empty file instead of an empty diff.
    if not has_differences:
        open(parsed_args.text_output, 'w').close()
        return

    with make_printer(parsed_args.text_output or '-') as fn:
        color = {
            'auto': fn.output.isatty(),
            'never': False,
            'always': True,
        }[parsed_args.text_color]

        output_text(difference, print_func=fn, color=color)

def html(difference, parsed_args, has_differences):
    if difference is None:
        return

    with make_printer(parsed_args.html_output) as fn:
        output_html(
            difference,
            css_url=parsed_args.css_url,
            print_func=fn,
        )

def html_directory(difference, parsed_args, has_differences):
    if difference is None:
        return

    output_html_directory(
        parsed_args.html_output_directory,
        difference,
        css_url=parsed_args.css_url,
        jquery_url=parsed_args.jquery_url,
    )

def profiling(difference, parsed_args, has_differences):
    with make_printer(parsed_args.profile_output or '-') as fn:
        ProfileManager().output(fn)

@contextlib.contextmanager
def make_printer(path):
    output = sys.stdout

    if path != '-':
        output = codecs.open(path, 'w', encoding='utf-8')

    def fn(*args, **kwargs):
        kwargs['file'] = output
        print(*args, **kwargs)
    fn.output = output

    yield fn

    if path != '-':
        output.close()
