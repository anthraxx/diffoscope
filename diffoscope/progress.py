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

import os
import sys
import json
import logging

logger = logging.getLogger(__name__)


class ProgressManager(object):
    _singleton = {}

    def __init__(self):
        self.__dict__ = self._singleton

        if not self._singleton:
            self.total = 0
            self.current = 0
            self.observers = []

    def setup(self, parsed_args):
        # Show progress bar if user explicitly asked for it, otherwise show if
        # STDOUT is a tty.
        if parsed_args.progress or \
                (parsed_args.progress is None and sys.stdout.isatty()):
            try:
                self.register(ProgressBar())
            except ImportError:
                # User asked for bar, so show them the error
                if parsed_args.progress:
                    raise

        if parsed_args.status_fd:
            self.register(StatusFD(parsed_args.status_fd))

    ##

    def register(self, observer):
        logger.debug("Registering %s as a progress observer", observer)

        self.observers.append(observer)

    def step(self, delta=1, msg=""):
        delta = min(self.total - self.current, delta) # clamp

        self.current += delta
        for x in self.observers:
            x.notify(self.current, self.total, msg)

    def new_total(self, delta, msg):
        self.total += delta
        for x in self.observers:
            x.notify(self.current, self.total, msg)

    def finish(self):
        for x in self.observers:
            x.finish()

class Progress(object):
    def __init__(self, total, msg=""):
        self.current = 0
        self.total = total

        ProgressManager().new_total(total, msg)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, exc_traceback):
        self.step(self.total - self.current)

    def step(self, delta=1, msg=""):
        delta = min(self.total - self.current, delta) # clamp
        if not delta:
            return

        self.current += delta
        ProgressManager().step(delta, msg)

class ProgressBar(object):
    def __init__(self):
        import progressbar

        self.msg = ""

        class Message(progressbar.Widget):
            def update(self, pbar, _observer=self):
                msg = _observer.msg
                width = 25

                if len(msg) <= width:
                    return msg.rjust(width)

                # Print the last `width` characters with an ellipsis.
                return '…{}'.format(msg[-width + 1:])

        class OurProgressBar(progressbar.ProgressBar):
            def _need_update(self):
                return True

        self.bar = OurProgressBar(widgets=(
            ' ',
            progressbar.Bar(),
            '  ',
            progressbar.Percentage(),
            '  ',
            Message(),
            '  ',
            progressbar.ETA(),
            ' ',
        ))
        self.bar.start()

    def notify(self, current, total, msg):
        self.msg = msg

        self.bar.maxval = total
        self.bar.currval = current
        self.bar.update()

    def finish(self):
        self.bar.finish()

class StatusFD(object):
    def __init__(self, fileno):
        self.fileobj = os.fdopen(fileno, 'w')

    def notify(self, current, total, msg):
        print(json.dumps({
            'msg': msg,
            'total': total,
            'current': current,
        }), file=self.fileobj)

    def finish(self):
        pass
