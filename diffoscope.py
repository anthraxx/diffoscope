#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# diffoscope: in-depth comparison of files, archives, and directories
#
# Copyright © 2014-2015 Jérémy Bobbio <lunar@debian.org>
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

from __future__ import print_function

import argparse
from contextlib import contextmanager
import logging
import codecs
import os
import sys
import traceback
from diffoscope import logger, VERSION, set_locale
import diffoscope.comparators
from diffoscope.config import Config
from diffoscope.presenters.html import output_html
from diffoscope.presenters.text import output_text


def create_parser():
    parser = argparse.ArgumentParser(
        description='Highlight differences between two builds '
                    'of Debian packages')
    parser.add_argument('--version', action='version',
                        version='diffoscope %s' % VERSION)
    parser.add_argument('--list-tools', nargs=0, action=ListToolsAction,
                        help='show external tools required and exit')
    parser.add_argument('--debug', dest='debug', action='store_true',
                        default=False, help='display debug messages')
    parser.add_argument('--html', metavar='output', dest='html_output',
                        help='write HTML report to given file (use - for stdout)')
    parser.add_argument('--text', metavar='output', dest='text_output',
                        help='write plain text output to given file (use - for stdout)')
    parser.add_argument('--max-report-size', metavar='BYTES',
                        dest='max_report_size', type=int,
                        help='maximum bytes written in report')
    parser.add_argument('--max-diff-block-lines', dest='max_diff_block_lines', type=int,
                        help='maximum number of lines per diff block')
    parser.add_argument('--max-diff-input-lines', dest='max_diff_input_lines', type=int,
                        help='maximum number of lines fed to diff')
    parser.add_argument('--css', metavar='url', dest='css_url',
                        help='link to an extra CSS for the HTML report')
    parser.add_argument('file1', help='first file to compare')
    parser.add_argument('file2', help='second file to compare')
    return parser


@contextmanager
def make_printer(path):
    if path == '-':
        output = sys.stdout
        if not sys.stdout.isatty():
            output = codecs.getwriter(sys.stdin.encoding)(sys.stdout)
    else:
        output = codecs.open(path, 'w', encoding='utf-8')
    def print_func(*args, **kwargs):
        kwargs['file'] = output
        print(*args, **kwargs)
    yield print_func
    if path != '-':
        output.close()


class ListToolsAction(argparse.Action):
    def __call__(self, parser, namespace, values, option_string=None):
        from diffoscope import tool_required, RequiredToolNotFound
        print("External tools required:")
        print(', '.join(tool_required.all))
        print()
        print("Available in packages:")
        print(', '.join(sorted(set([RequiredToolNotFound.PROVIDERS[k]["debian"] for k in tool_required.all]))))
        sys.exit(0)


def main():
    parser = create_parser()
    parsed_args = parser.parse_args(sys.argv[1:])
    Config.config().max_diff_block_lines = parsed_args.max_diff_block_lines
    Config.config().max_diff_input_lines = parsed_args.max_diff_input_lines
    Config.config().max_report_size = parsed_args.max_report_size
    if parsed_args.debug:
        logger.setLevel(logging.DEBUG)
    set_locale()
    difference = diffoscope.comparators.compare_root_paths(
        parsed_args.file1, parsed_args.file2)
    if difference:
        if parsed_args.html_output:
            with make_printer(parsed_args.html_output) as print_func:
                output_html(difference, css_url=parsed_args.css_url, print_func=print_func)
        if (parsed_args.text_output and parsed_args.text_output != parsed_args.html_output) or not parsed_args.html_output:
            with make_printer(parsed_args.text_output or '-') as print_func:
                output_text(difference, print_func=print_func)
        return 1
    return 0

if __name__ == '__main__':
    try:
        sys.exit(main())
    except (Exception, KeyboardInterrupt):
        traceback.print_exc()
        sys.exit(2)
