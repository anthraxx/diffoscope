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
import signal
import logging
import argparse
import traceback

from . import VERSION
from .tools import tool_required, OS_NAMES, get_current_os
from .config import Config
from .locale import set_locale
from .logging import setup_logging
from .progress import ProgressManager, Progress
from .profiling import ProfileManager, profile
from .tempfiles import clean_all_temp_files
from .difference import Difference
from .comparators import ComparatorManager
from .external_tools import EXTERNAL_TOOLS
from .presenters.html import JQUERY_SYSTEM_LOCATIONS
from .presenters.formats import output_all
from .comparators.utils.compare import compare_root_paths

logger = logging.getLogger(__name__)


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
        description='Calculate differences between two files or directories',
        add_help=False)
    parser.add_argument('path1', help='First file or directory to compare')
    parser.add_argument('path2', help='Second file or directory to compare')
    parser.add_argument('--debug', dest='debug', action='store_true',
                        default=False, help='Display debug messages')
    parser.add_argument('--debugger', action='store_true',
                        help='Open the Python debugger in case of crashes')
    parser.add_argument('--status-fd', dest='status_fd', metavar='FD', type=int,
                        help='Send machine-readable status to file descriptor FD')
    parser.add_argument('--progress', dest='progress', action='store_const',
                        const=True, help='Show an approximate progress bar')
    parser.add_argument('--no-progress', dest='progress', action='store_const',
                        const=False, help='Do not show any progress bar')

    group1 = parser.add_argument_group('output types')
    group1.add_argument('--text', metavar='OUTPUT_FILE', dest='text_output',
                        help='Write plain text output to given file (use - for stdout)')
    group1.add_argument('--text-color', metavar='WHEN', default='auto',
                        choices=['never', 'auto', 'always'],
                        help='When to output color diff. WHEN is one of {%(choices)s}. '
                        'Default: auto, meaning yes if the output is a terminal, otherwise no.')
    group1.add_argument('--output-empty', action='store_true',
                        help='If there was no difference, then output an empty '
                        'diff for each output type that was specified. In '
                        '--text output, an empty file is written.')
    group1.add_argument('--html', metavar='OUTPUT_FILE', dest='html_output',
                        help='Write HTML report to given file (use - for stdout)')
    group1.add_argument('--html-dir', metavar='OUTPUT_DIR', dest='html_output_directory',
                        help='Write multi-file HTML report to given directory')
    group1.add_argument('--css', metavar='URL', dest='css_url',
                        help='Link to an extra CSS for the HTML report')
    group1.add_argument('--jquery', metavar='URL', dest='jquery_url',
                        help='Link to the jQuery url, with --html-dir. Specify '
                        '"disable" to disable JavaScript. When omitted '
                        'diffoscope will try to create a symlink to a system '
                        'installation. Known locations: %s' % ', '.join(JQUERY_SYSTEM_LOCATIONS))
    group1.add_argument('--json', metavar='OUTPUT_FILE', dest='json_output',
                        help='Write JSON text output to given file (use - for stdout)')
    group1.add_argument('--markdown', metavar='OUTPUT_FILE', dest='markdown_output',
                        help='Write Markdown text output to given file (use - for stdout)')
    group1.add_argument('--restructured-text', metavar='OUTPUT_FILE',
                        dest='restructuredtext_output',
                        help='Write RsT text output to given file (use - for stdout)')
    group1.add_argument('--profile', metavar='OUTPUT_FILE', dest='profile_output',
                        help='Write profiling info to given file (use - for stdout)')

    group2 = parser.add_argument_group('output limits')
    group2.add_argument('--no-default-limits', action='store_true', default=False,
                        help='Disable most default limits. Note that text '
                        'output already ignores most of these.')
    group2.add_argument('--max-text-report-size', metavar='BYTES',
                        dest='max_text_report_size', type=int,
                        help='Maximum bytes written in --text report. (0 to '
                        'disable)', default=None).completer=RangeCompleter(0,
                        Config().max_text_report_size, 200000)
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
                        help='In --html-dir output, this is the max bytes of '
                        'each child page (0 to disable, default: %(default)s, '
                        'remaining in effect even with --no-default-limits)',
                        default=Config().max_report_child_size).completer=RangeCompleter(0,
                        Config().max_report_child_size, 50000)
    group2.add_argument('--max-diff-block-lines', dest='max_diff_block_lines',
                        metavar='LINES', type=int,
                        help='Maximum number of lines output per diff block. '
                        'In --html-dir output, we use %d times this number instead, '
                        'taken over all pages. (0 to disable, default: %d)' %
                        (Config().max_diff_block_lines_html_dir_ratio,
                        Config().max_diff_block_lines),
                        default=None).completer=RangeCompleter(0,
                        Config().max_diff_block_lines, 5)
    group2.add_argument('--max-diff-block-lines-parent', dest='max_diff_block_lines_parent',
                        metavar='LINES', type=int,
                        help='In --html-dir output, this is maximum number of '
                        'lines output per diff block on the parent page '
                        'before spilling it into child pages (0 to disable, '
                        'default: %(default)s, remaining in effect even with '
                        '--no-default-limits)',
                        default=Config().max_diff_block_lines_parent).completer=RangeCompleter(0,
                        Config().max_diff_block_lines_parent, 200)
    group2.add_argument('--max-diff-block-lines-saved', dest='max_diff_block_lines_saved',
                        metavar='LINES', type=int,
                        help='Maximum number of lines saved per diff block. '
                        'Most users should not need this, unless you run out '
                        'of memory. This truncates diff(1) output before even '
                        'trying to emit it in a report. This also affects --text '
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
                        help='Maximum number of lines fed to diff(1) '
                        '(0 to disable, default: %d)' %
                        Config().max_diff_input_lines,
                        default=None).completer=RangeCompleter(0,
                        Config().max_diff_input_lines, 5000)

    group4 = parser.add_argument_group('information commands')
    group4.add_argument('--help', '-h', action='help',
                        help="Show this help and exit")
    group4.add_argument('--version', action='version',
                        version='diffoscope %s' % VERSION,
                        help="Show program's version number and exit")
    group4.add_argument('--list-tools', nargs='?', type=str, action=ListToolsAction,
                        metavar='DISTRO', choices=OS_NAMES,
                        help='Show external tools required and exit. '
                        'DISTRO can be one of {%(choices)s}. '
                        'If specified, the output will list packages in that '
                        'distribution that satisfy these dependencies.')

    if not tlsh:
        parser.epilog = 'File renaming detection based on fuzzy-matching is currently disabled. It can be enabled by installing the "tlsh" module available at https://github.com/trendmicro/tlsh'
    if argcomplete:
        argcomplete.autocomplete(parser)
    elif '_ARGCOMPLETE' in os.environ:
        logger.error('Argument completion requested but the "argcomplete" module is not installed. It can be obtained at https://pypi.python.org/pypi/argcomplete')
        sys.exit(1)

    return parser


class RangeCompleter(object):
    def __init__(self, start, end, step):
        self.choices = range(start, end + 1, step)

    def __call__(self, prefix, **kwargs):
        return (str(i) for i in self.choices if str(i).startswith(prefix))

class ListToolsAction(argparse.Action):
    def __call__(self, parser, namespace, os_override, option_string=None):
        # Ensure all comparators are imported so tool_required.all is
        # populated.
        ComparatorManager().reload()

        print("External-Tools-Required: ", end='')
        print(', '.join(sorted(tool_required.all)))
        if os_override:
            os_list = [os_override]
        else:
            current_os = get_current_os()
            os_list = [current_os] if (current_os in OS_NAMES) else iter(OS_NAMES)
        for os in os_list:
            print("Available-in-{}-packages: ".format(OS_NAMES[os]), end='')
            print(', '.join(sorted(filter(None, {
                EXTERNAL_TOOLS.get(k, {}).get(os, None)
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
    setup_logging(parsed_args.debug)
    ProfileManager().setup(parsed_args)
    logger.debug("Starting diffoscope %s", VERSION)
    if not tlsh and Config().fuzzy_threshold != parsed_args.fuzzy_threshold:
        logger.warning('Fuzzy-matching is currently disabled as the "tlsh" module is unavailable.')
    maybe_set_limit(Config(), parsed_args, "max_report_size")
    maybe_set_limit(Config(), parsed_args, "max_text_report_size")
    maybe_set_limit(Config(), parsed_args, "max_report_child_size")
    # need to set them in this order due to Config._check_constraints
    maybe_set_limit(Config(), parsed_args, "max_diff_block_lines_saved")
    maybe_set_limit(Config(), parsed_args, "max_diff_block_lines_parent")
    maybe_set_limit(Config(), parsed_args, "max_diff_block_lines")
    maybe_set_limit(Config(), parsed_args, "max_diff_input_lines")
    Config().fuzzy_threshold = parsed_args.fuzzy_threshold
    Config().new_file = parsed_args.new_file
    set_locale()
    logger.debug('Starting comparison')
    ProgressManager().setup(parsed_args)
    with Progress(1, parsed_args.path1):
        with profile('main', 'outputs'):
            difference = compare_root_paths(
                parsed_args.path1, parsed_args.path2)
    ProgressManager().finish()
    # Generate an empty, dummy diff to write, saving for exit code first.
    has_differences = bool(difference is not None)
    if difference is None and parsed_args.output_empty:
        difference = Difference(None, parsed_args.path1, parsed_args.path2)
    with profile('main', 'outputs'):
        output_all(difference, parsed_args, has_differences)
    return 1 if has_differences else 0


def sigterm_handler(signo, stack_frame):
    clean_all_temp_files()
    os._exit(2)

def main(args=None):
    if args is None:
        args = sys.argv[1:]
    signal.signal(signal.SIGTERM, sigterm_handler)
    parsed_args = None
    try:
        with profile('main', 'parse_args'):
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
        with profile('main', 'cleanup'):
            clean_all_temp_files()

        # Print profiling output at the very end
        if parsed_args is not None:
            ProfileManager().finish(parsed_args)

if __name__ == '__main__':
    main()
