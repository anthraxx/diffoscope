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

from abc import ABCMeta, abstractmethod
from contextlib import contextmanager
# The following would be shutil.which in Python 3.3
import os
import shutil
from stat import S_ISCHR, S_ISBLK
from StringIO import StringIO
import subprocess
import tempfile
from threading import Thread
import diffoscope.comparators
from diffoscope.comparators.binary import File
from diffoscope.difference import Difference
from diffoscope import logger, tool_required


@contextmanager
def make_temp_directory():
    temp_dir = tempfile.mkdtemp(suffix='diffoscope')
    try:
        yield temp_dir
    finally:
        shutil.rmtree(temp_dir)


@tool_required('ar')
def get_ar_content(path):
    return subprocess.check_output(
        ['ar', 'tv', path], stderr=subprocess.STDOUT, shell=False).decode('utf-8')


class Command(object):
    __metaclass__ = ABCMeta

    def __init__(self, path):
        self._path = path
        self._process = subprocess.Popen(self.cmdline(),
                                         shell=False, close_fds=True,
                                         stdin=subprocess.PIPE,
                                         stdout=subprocess.PIPE,
                                         stderr=subprocess.PIPE)
        if hasattr(self, 'feed_stdin'):
            self._stdin_feeder = Thread(target=self.feed_stdin, args=(self._process.stdin,))
            self._stdin_feeder.daemon = True
            self._stdin_feeder.start()
        else:
            self._stdin_feeder = None
            self._process.stdin.close()
        self._stderr = StringIO()
        self._stderr_line_count = 0
        self._stderr_reader = Thread(target=self._read_stderr)
        self._stderr_reader.daemon = True
        self._stderr_reader.start()

    @property
    def path(self):
        return self._path

    @abstractmethod
    def cmdline(self):
        raise NotImplemented

    # Define only if needed
    #def feed_stdin(self, f)

    def filter(self, line):
        # Assume command output is utf-8 by default
        return line

    def poll(self):
        return self._process.poll()

    def terminate(self):
        return self._process.terminate()

    def wait(self):
        if self._stdin_feeder:
            self._stdin_feeder.join()
        self._stderr_reader.join()
        self._process.wait()

    MAX_STDERR_LINES = 50

    def _read_stderr(self):
        for line in iter(self._process.stderr.readline, b''):
            self._stderr_line_count += 1
            if self._stderr_line_count <= Command.MAX_STDERR_LINES:
                self._stderr.write(line)
        if self._stderr_line_count > Command.MAX_STDERR_LINES:
            self._stderr.write('[ %d lines ignored ]\n' % (self._stderr_line_count - Command.MAX_STDERR_LINES))
        self._process.stderr.close()

    @property
    def stderr_content(self):
        return self._stderr.getvalue()

    @property
    def stdout(self):
        return self._process.stdout




def format_symlink(destination):
    return 'destination: %s\n' % destination


def format_device(mode, major, minor):
    if S_ISCHR(mode):
        kind = 'character'
    elif S_ISBLK(mode):
        kind = 'block'
    else:
        kind = 'weird'
    return 'device:%s\nmajor: %d\nminor: %d\n' % (kind, major, minor)


def get_compressed_content_name(path, expected_extension):
    basename = os.path.basename(path)
    if basename.endswith(expected_extension):
        name = basename[:-len(expected_extension)]
    else:
        name = "%s-content" % basename
    return name


class Container(object):
    __metaclass__ = ABCMeta

    def __init__(self, source):
        self._source = source

    @property
    def source(self):
        return self._source

    @contextmanager
    def open(self):
        raise NotImplemented

    @abstractmethod
    def get_member_names(self):
        raise NotImplemented

    @abstractmethod
    def get_member(self, member_name):
        raise NotImplemented

    def compare(self, other, source=None):
        differences = []
        my_names = set(self.get_member_names())
        other_names = set(other.get_member_names())
        for name in sorted(my_names.intersection(other_names)):
            logger.debug('compare member %s', name)
            my_file = self.get_member(name)
            other_file = other.get_member(name)
            differences.append(
                diffoscope.comparators.compare_files(
                    my_file, other_file, source=name))
        my_extra_files = map(self.get_member, my_names.difference(other_names))
        other_extra_files = map(other.get_member, other_names.difference(my_names))
        for my_file, other_file, score in diffoscope.comparators.perform_fuzzy_matching(my_extra_files, other_extra_files):
            difference = diffoscope.comparators.compare_files(my_file, other_file)
            if difference is None:
                difference = Difference(None, my_file.name, other_file.name)
            difference.add_comment(
                'Files similar despite different names (difference score: %d)' % score)
            differences.append(difference)
        return differences


class ArchiveMember(File):
    def __init__(self, container, member_name):
        self._container = container
        self._name = member_name
        self._path = None

    @property
    def container(self):
        return self._container

    @property
    def name(self):
        return self._name

    @contextmanager
    def get_content(self):
        logger.debug('%s get_content; path %s', self, self._path)
        if self._path is not None:
            yield
        else:
            with make_temp_directory() as temp_dir, \
                 self._container.open() as container:
                self._path = container.extract(self._name, temp_dir)
                yield
                self._path = None

    def is_directory(self):
        return False

    def is_symlink(self):
        return False

    def is_device(self):
        return False


class Archive(Container):
    __metaclass__ = ABCMeta

    def __init__(self, *args, **kwargs):
        super(Archive, self).__init__(*args, **kwargs)
        self._archive = None

    @contextmanager
    def open(self):
        if self._archive is not None:
            yield self
        else:
            with self.source.get_content():
                self._archive = self.open_archive(self.source.path)
                try:
                    yield self
                finally:
                    self.close_archive()
                    self._archive = None

    @property
    def archive(self):
        return self._archive

    @abstractmethod
    def open_archive(self, path):
        raise NotImplemented

    @abstractmethod
    def close_archive(self):
        raise NotImplemented

    @abstractmethod
    def get_member_names(self):
        raise NotImplemented

    @abstractmethod
    def extract(self, member_name, dest_dir):
        raise NotImplemented

    def get_member(self, member_name):
        return ArchiveMember(self, member_name)
