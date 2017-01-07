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
import time
import contextlib
import collections

_ENABLED = False


@contextlib.contextmanager
def profile(namespace, key):
    start = time.time()
    yield

    if _ENABLED:
        ProfileManager().increment(start, namespace, key)

class ProfileManager(object):
    _singleton = {}

    def __init__(self):
        self.__dict__ = self._singleton

        if not self._singleton:
            self.data = collections.defaultdict(
                lambda: collections.defaultdict(lambda: {
                    'time': 0.0,
                    'count': 0,
                }),
            )

    def setup(self, parsed_args):
        global _ENABLED
        _ENABLED = parsed_args.profile_output is not None

    def increment(self, start, namespace, key):
        if not isinstance(key, str):
            key = '{}.{}'.format(
                key.__class__.__module__,
                key.__class__.__name__,
            )

        self.data[namespace][key]['time'] += time.time() - start
        self.data[namespace][key]['count'] += 1

    def finish(self, parsed_args):
        from .presenters.utils import make_printer

        if parsed_args.profile_output is None:
            return

        with make_printer(parsed_args.profile_output) as fn:
            self.output(fn)

    def output(self, print):
        title = "Profiling output for: {}".format(' '.join(sys.argv))

        print(title)
        print("=" * len(title))

        for namespace, keys in sorted(self.data.items(), key=lambda x: x[0]):
            subtitle = "{} (total time: {:.3f}s)".format(
                namespace,
                sum(x['time'] for x in keys.values()),
            )

            print("\n{}\n{}\n".format(subtitle, "-" * len(subtitle)))

            for value, totals in sorted(keys.items(), key=lambda x: x[1]['time'], reverse=True):
                print("  {:10.3f}s {:5d} call{}    {}".format(
                    totals['time'],
                    totals['count'],
                    ' ' if totals['count'] == 1 else 's',
                    value,
                ))
