#!/usr/bin/env python3
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

import argparse
from contextlib import contextmanager
import logging
import codecs
import os
import signal
import sys
import traceback
try:
    import tlsh
except ImportError:
    tlsh = None
from diffoscope import logger, VERSION, set_locale, clean_all_temp_files
import diffoscope.comparators
from diffoscope.config import Config
from diffoscope.presenters.html import output_html
from diffoscope.presenters.html import output_html_directory, JQUERY_SYSTEM_LOCATIONS
from diffoscope.presenters.text import output_text


def create_parser():
    parser = argparse.ArgumentParser(
        description='Highlight differences between two builds '
                    'of Debian packages')
    parser.add_argument('--version', action='version',
                        version='diffoscope %s' % VERSION)
    parser.add_argument('--list-tools', nargs='?', type=str, action=ListToolsAction,
                        help='show external tools required and exit')
    parser.add_argument('--debug', dest='debug', action='store_true',
                        default=False, help='display debug messages')
    parser.add_argument('--debugger', action='store_true',
                        help='Open the python debugger in case of crashes.')
    parser.add_argument('--html', metavar='output', dest='html_output',
                        help='write HTML report to given file (use - for stdout)')
    parser.add_argument('--html-dir', metavar='output', dest='html_output_directory',
                        help='write multi-file HTML report to given directory')
    parser.add_argument('--text', metavar='output', dest='text_output',
                        help='write plain text output to given file (use - for stdout)')
    parser.add_argument('--max-report-size', metavar='BYTES',
                        dest='max_report_size', type=int,
                        help='maximum bytes written in report (default: %d)' %
                        Config.general.max_report_size,
                        default=Config.general.max_report_size)
    parser.add_argument('--separate-file-diff-size', metavar='BYTES',
                        dest='separate_file_diff_size', type=int,
                        help='diff size to load diff on demand, with --html-dir (default: %d)' %
                        Config.general.separate_file_diff_size,
                        default=Config.general.separate_file_diff_size)
    parser.add_argument('--max-diff-block-lines', dest='max_diff_block_lines', type=int,
                        help='maximum number of lines per diff block (default: %d)' %
                        Config.general.max_diff_block_lines,
                        default=Config.general.max_diff_block_lines)
    parser.add_argument('--max-diff-input-lines', dest='max_diff_input_lines', type=int,
                        help='maximum number of lines fed to diff (default: %d)' %
                        Config.general.max_diff_input_lines,
                        default=Config.general.max_diff_input_lines)
    parser.add_argument('--fuzzy-threshold', dest='fuzzy_threshold', type=int,
                        help='threshold for fuzzy-matching '
                             '(0 to disable, %d is default, 400 is high fuzziness)' %
                             (Config.general.fuzzy_threshold),
                        default=Config.general.fuzzy_threshold)
    parser.add_argument('--new-file', dest='new_file', action='store_true',
                        help='treat absent files as empty')
    parser.add_argument('--css', metavar='url', dest='css_url',
                        help='link to an extra CSS for the HTML report')
    parser.add_argument('--jquery', metavar='url', dest='jquery_url',
                        help='link to the jquery url, with --html-dir. Specify “disable” to disable JavaScript. When omitted diffoscope will try to create a symlink to a system installation. Known locations: %s' % ', '.join(JQUERY_SYSTEM_LOCATIONS))
    parser.add_argument('file1', help='first file to compare')
    parser.add_argument('file2', help='second file to compare')
    if not tlsh:
        parser.epilog = 'File renaming detection based on fuzzy-matching is currently disabled. It can be enabled by installing the “tlsh” module available at https://github.com/trendmicro/tlsh'
    return parser


@contextmanager
def make_printer(path):
    if path == '-':
        output = sys.stdout
    else:
        output = codecs.open(path, 'w', encoding='utf-8')
    def print_func(*args, **kwargs):
        kwargs['file'] = output
        print(*args, **kwargs)
    yield print_func
    if path != '-':
        output.close()


class ListToolsAction(argparse.Action):
    def __call__(self, parser, namespace, os_override, option_string=None):
        from functools import reduce
        from diffoscope import tool_required, RequiredToolNotFound, OS_NAMES, get_current_os
        print("External tools required:")
        print(', '.join(sorted(tool_required.all)))
        if os_override:
            if os_override in OS_NAMES.keys():
                os_list = [os_override]
            else:
                print()
                print("No package mapping found for: {} (possible values: {})".format(os_override, ", ".join(sorted(OS_NAMES.keys()))))
                sys.exit(1)
        else:
            current_os = get_current_os()
            if current_os in OS_NAMES.keys():
                os_list = [current_os]
            else:
                os_list = OS_NAMES.keys()
        for os in os_list:
            print()
            print("Available in {} packages:".format(OS_NAMES[os] if os in OS_NAMES else os))
            print(', '.join(sorted(filter(None, { RequiredToolNotFound.PROVIDERS.get(k, {}).get(os, None) for k in tool_required.all }))))
        sys.exit(0)


def run_diffoscope(parsed_args):
    if not tlsh and Config.general.fuzzy_threshold != parsed_args.fuzzy_threshold:
        logger.warning('Fuzzy-matching is currently disabled as the “tlsh” module is unavailable.')
    Config.general.max_diff_block_lines = parsed_args.max_diff_block_lines
    Config.general.max_diff_input_lines = parsed_args.max_diff_input_lines
    Config.general.max_report_size = parsed_args.max_report_size
    Config.general.separate_file_diff_size = parsed_args.separate_file_diff_size
    Config.general.fuzzy_threshold = parsed_args.fuzzy_threshold
    Config.general.new_file = parsed_args.new_file
    if parsed_args.debug:
        logger.setLevel(logging.DEBUG)
    set_locale()
    difference = diffoscope.comparators.compare_root_paths(
        parsed_args.file1, parsed_args.file2)
    if difference:
        # no output desired? print text
        if not any((parsed_args.text_output, parsed_args.html_output, parsed_args.html_output_directory)):
            parsed_args.text_output = "-"
        if parsed_args.html_output:
            with make_printer(parsed_args.html_output) as print_func:
                output_html(difference, css_url=parsed_args.css_url, print_func=print_func)
        if parsed_args.html_output_directory:
                output_html_directory(parsed_args.html_output_directory, difference, css_url=parsed_args.css_url, jquery_url=parsed_args.jquery_url)
        if parsed_args.text_output:
            with make_printer(parsed_args.text_output or '-') as print_func:
                output_text(difference, print_func=print_func)
        return 1
    return 0


def sigterm_handler(signo, stack_frame):
    sys.exit(2)


def main(args=None):
    if args is None:
        args = sys.argv[1:]
    signal.signal(signal.SIGTERM, sigterm_handler)
    parsed_args = None
    try:
        parser = create_parser()
        parsed_args = parser.parse_args(args)
        sys.exit(run_diffoscope(parsed_args))
    except KeyboardInterrupt:
        logger.info('Keyboard Interrupt')
        sys.exit(2)
    except Exception:
        traceback.print_exc()
        if parsed_args and parsed_args.debugger:
            import pdb
            pdb.post_mortem()
        sys.exit(2)
    finally:
        clean_all_temp_files()

if __name__ == '__main__':
    main()
