#!/usr/bin/env python3
# PYTHON_ARGCOMPLETE_OK
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
# along with diffoscope.  If not, see <https://www.gnu.org/licenses/>.

import os
import sys
import codecs
import signal
import logging
import argparse
import traceback
import contextlib

import diffoscope.comparators

from diffoscope import logger, VERSION, set_locale, clean_all_temp_files
from diffoscope.exc import RequiredToolNotFound
from diffoscope.config import Config
from diffoscope.difference import Difference
from diffoscope.progress import ProgressManager, Progress
from diffoscope.profiling import ProfileManager, profile
from diffoscope.presenters.html import output_html, output_html_directory, \
    JQUERY_SYSTEM_LOCATIONS
from diffoscope.presenters.text import output_text

try:
    import tlsh
except ImportError:
    tlsh = None

try:
    import argcomplete
except ImportError:
    argcomplete = None


def create_parser():
    parser = argparse.ArgumentParser(
        description='Calculate differences between two files or directories.')
    parser.add_argument('path1', help='First file or directory to compare')
    parser.add_argument('path2', help='Second file or directory to compare')
    parser.add_argument('--version', action='version',
                        version='diffoscope %s' % VERSION)
    parser.add_argument('--list-tools', nargs='?', type=str, action=ListToolsAction,
                        help='Show external tools required and exit')
    parser.add_argument('--debug', dest='debug', action='store_true',
                        default=False, help='Display debug messages')
    parser.add_argument('--debugger', action='store_true',
                        help='Open the python debugger in case of crashes.')
    parser.add_argument('--status-fd', dest='status_fd', metavar='N', type=int,
                        help='Send machine-readable status to file descriptor N')
    parser.add_argument('--progress', dest='progress', action='store_const',
                        const=True, help='Show an (approximate) progress bar')
    parser.add_argument('--no-progress', dest='progress', action='store_const',
                        const=False, help='Do not show an (approximate) progress bar')

    group1 = parser.add_argument_group('output types')
    group1.add_argument('--text', metavar='OUTPUT_FILE', dest='text_output',
                        help='Write plain text output to given file (use - for stdout)')
    group1.add_argument('--text-color', metavar='WHEN', default='auto',
                        choices=['never', 'auto', 'always'],
                        help='When to output color diff. WHEN is one of {%(choices)s}. '
                        'Default: auto, meaning yes if the output is a terminal, otherwise no.')
    group1.add_argument('--output-empty', action='store_true',
                        help='If there was no difference, then output an empty '
                        'diff for each output type that was specified. (For '
                        '--text, an empty file is written.)')
    group1.add_argument('--html', metavar='OUTPUT_FILE', dest='html_output',
                        help='Write HTML report to given file (use - for stdout)')
    group1.add_argument('--html-dir', metavar='OUTPUT_DIR', dest='html_output_directory',
                        help='Write multi-file HTML report to given directory')
    group1.add_argument('--css', metavar='url', dest='css_url',
                        help='Link to an extra CSS for the HTML report')
    group1.add_argument('--jquery', metavar='url', dest='jquery_url',
                        help='Link to the jquery url, with --html-dir. Specify '
                        '"disable" to disable JavaScript. When omitted '
                        'diffoscope will try to create a symlink to a system '
                        'installation. Known locations: %s' % ', '.join(JQUERY_SYSTEM_LOCATIONS))
    group1.add_argument('--profile', metavar='OUTPUT_FILE', dest='profile_output',
                        help='Write profiling info to given file (use - for stdout)')

    group2 = parser.add_argument_group('output limits')
    group2.add_argument('--no-default-limits', action='store_true', default=False,
                        help='Disable most default limits. Note that text '
                        'output already ignores most of these.')
    group2.add_argument('--max-report-size', metavar='BYTES',
                        dest='max_report_size', type=int,
                        help='Maximum bytes written in report. In html-dir '
                        'output, this is the max bytes of the parent page. '
                        '(0 to disable, default: %d)' %
                        Config().max_report_size,
                        default=None).completer=RangeCompleter(0,
                        Config().max_report_size, 200000)
    group2.add_argument('--max-report-child-size', metavar='BYTES',
                        dest='max_report_child_size', type=int,
                        help='In html-dir output, this is the max bytes of '
                        'each child page. (0 to disable, default: %(default)s, '
                        'remaining in effect even with --no-default-limits)',
                        default=Config().max_report_child_size).completer=RangeCompleter(0,
                        Config().max_report_child_size, 50000)
    group2.add_argument('--max-diff-block-lines', dest='max_diff_block_lines',
                        metavar='LINES', type=int,
                        help='Maximum number of lines output per diff block. '
                        'In html-dir output, we use %d * this number instead, '
                        'taken over all pages. (0 to disable, default: %d)' %
                        (Config().max_diff_block_lines_html_dir_ratio,
                        Config().max_diff_block_lines),
                        default=None).completer=RangeCompleter(0,
                        Config().max_diff_block_lines, 5)
    group2.add_argument('--max-diff-block-lines-parent', dest='max_diff_block_lines_parent',
                        metavar='LINES', type=int,
                        help='In --html-dir output, this is maximum number of '
                        'lines output per diff block on the parent page, '
                        'before spilling it into child pages. (0 to disable, '
                        'default: %(default)s, remaining in effect even with '
                        '--no-default-limits)',
                        default=Config().max_diff_block_lines_parent).completer=RangeCompleter(0,
                        Config().max_diff_block_lines_parent, 200)
    group2.add_argument('--max-diff-block-lines-saved', dest='max_diff_block_lines_saved',
                        metavar='LINES', type=int,
                        help='Maximum number of lines saved per diff block. '
                        'Most users should not need this, unless you run out '
                        'of memory. This truncates diff(1) output before even '
                        'trying to emit it in a report; also affects --text '
                        'output. (0 to disable, default: 0)',
                        default=0).completer=RangeCompleter(0, 0, 200)

    group3 = parser.add_argument_group('diff calculation')
    group3.add_argument('--new-file', dest='new_file', action='store_true',
                        help='Treat absent files as empty')
    group3.add_argument('--fuzzy-threshold', dest='fuzzy_threshold', type=int,
                        help='Threshold for fuzzy-matching '
                        '(0 to disable, %(default)s is default, 400 is high fuzziness)',
                        default=Config().fuzzy_threshold).completer=RangeCompleter(0,
                        400, 20)
    group3.add_argument('--max-diff-input-lines', dest='max_diff_input_lines',
                        metavar='LINES', type=int,
                        help='Maximum number of lines fed to diff(1). '
                        '(0 to disable, default: %d)' %
                        Config().max_diff_input_lines,
                        default=None).completer=RangeCompleter(0,
                        Config().max_diff_input_lines, 5000)

    if not tlsh:
        parser.epilog = 'File renaming detection based on fuzzy-matching is currently disabled. It can be enabled by installing the "tlsh" module available at https://github.com/trendmicro/tlsh'
    if argcomplete:
        argcomplete.autocomplete(parser)
    elif '_ARGCOMPLETE' in os.environ:
        logger.error('Argument completion requested but the "argcomplete" module is not installed. It can be obtained at https://pypi.python.org/pypi/argcomplete')
        sys.exit(1)

    return parser


@contextlib.contextmanager
def make_printer(path):
    if path == '-':
        output = sys.stdout
    else:
        output = codecs.open(path, 'w', encoding='utf-8')
    def print_func(*args, **kwargs):
        kwargs['file'] = output
        print(*args, **kwargs)
    print_func.output = output
    yield print_func
    if path != '-':
        output.close()

class RangeCompleter(object):
    def __init__(self, start, end, step):
        self.choices = range(start, end + 1, step)

    def __call__(self, prefix, **kwargs):
        return (str(i) for i in self.choices if str(i).startswith(prefix))

class ListToolsAction(argparse.Action):
    def __call__(self, parser, namespace, os_override, option_string=None):
        from diffoscope import tool_required, OS_NAMES, get_current_os

        print("External-Tools-Required: ", end='')
        print(', '.join(sorted(tool_required.all)))
        if os_override:
            if os_override in OS_NAMES.keys():
                os_list = [os_override]
            else:
                print()
                print("No package mapping found for: {} (possible values: {})".format(os_override, ", ".join(sorted(OS_NAMES.keys()))), file=sys.stderr)
                sys.exit(1)
        else:
            current_os = get_current_os()
            if current_os in OS_NAMES.keys():
                os_list = [current_os]
            else:
                os_list = OS_NAMES.keys()
        for os in os_list:
            print("Available-in-{}-packages: ".format(OS_NAMES.get(os, os)), end='')
            print(', '.join(sorted(filter(None, {
                RequiredToolNotFound.PROVIDERS.get(k, {}).get(os, None)
                for k in tool_required.all
            }))))
        sys.exit(0)


def maybe_set_limit(config, parsed_args, key):
    v = getattr(parsed_args, key)
    if v is not None:
        setattr(config, key, float("inf") if v == 0 else v)
    elif parsed_args.no_default_limits:
        setattr(config, key, float("inf"))


def run_diffoscope(parsed_args):
    if not tlsh and Config().fuzzy_threshold != parsed_args.fuzzy_threshold:
        logger.warning('Fuzzy-matching is currently disabled as the "tlsh" module is unavailable.')
    maybe_set_limit(Config(), parsed_args, "max_report_size")
    maybe_set_limit(Config(), parsed_args, "max_report_child_size")
    # need to set them in this order due to Config._check_constraints
    maybe_set_limit(Config(), parsed_args, "max_diff_block_lines_saved")
    maybe_set_limit(Config(), parsed_args, "max_diff_block_lines_parent")
    maybe_set_limit(Config(), parsed_args, "max_diff_block_lines")
    maybe_set_limit(Config(), parsed_args, "max_diff_input_lines")
    Config().fuzzy_threshold = parsed_args.fuzzy_threshold
    Config().new_file = parsed_args.new_file
    if parsed_args.debug:
        logger.setLevel(logging.DEBUG)
    set_locale()
    # no output desired? print text to stdout
    if not any((parsed_args.text_output, parsed_args.html_output, parsed_args.html_output_directory)):
        parsed_args.text_output = "-"
    logger.debug('Starting comparison')
    ProgressManager().setup(parsed_args)
    with Progress(1):
        difference = diffoscope.comparators.compare_root_paths(
            parsed_args.path1, parsed_args.path2)
    ProgressManager().finish()
    retcode = 1 if difference else 0
    if not retcode and parsed_args.output_empty:
        # dummy empty diff to write
        difference = Difference(None, parsed_args.path1, parsed_args.path2)
    if difference:
        if parsed_args.text_output:
            with profile('output', 'text'):
                if not retcode:
                    # special case for --text: write an empty file instead of an empty diff
                    open(parsed_args.text_output, 'w').close()
                else:
                    with make_printer(parsed_args.text_output or '-') as print_func:
                        color = {
                            'auto': print_func.output.isatty(),
                            'never': False,
                            'always': True,
                        }[parsed_args.text_color]
                        output_text(difference, print_func=print_func, color=color)
        if parsed_args.html_output:
            with profile('output', 'html'):
                with make_printer(parsed_args.html_output) as print_func:
                        output_html(difference, css_url=parsed_args.css_url, print_func=print_func)
        if parsed_args.html_output_directory:
            with profile('output', 'html_directory'):
                output_html_directory(parsed_args.html_output_directory, difference,
                    css_url=parsed_args.css_url, jquery_url=parsed_args.jquery_url)
    if parsed_args.profile_output:
        with make_printer(parsed_args.profile_output) as print_func:
            ProfileManager().output(print_func)
    return retcode


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
    except BrokenPipeError:
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
