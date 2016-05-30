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
from collections import OrderedDict
from contextlib import contextmanager
from io import BytesIO
from itertools import starmap
# The following would be shutil.which in Python 3.3
import os
import shutil
from stat import S_ISCHR, S_ISBLK
import subprocess
import tempfile
from threading import Thread
import diffoscope.comparators
from diffoscope.comparators.binary import File, NonExistingFile
from diffoscope.config import Config
from diffoscope.difference import Difference
from diffoscope import logger, tool_required, get_temporary_directory


class Command(object, metaclass=ABCMeta):
    def __init__(self, path):
        self._path = path
        logger.debug('running %s', self.cmdline())
        self._process = subprocess.Popen(self.cmdline(),
                                         shell=False, close_fds=True,
                                         env=self.env(),
                                         stdin=subprocess.PIPE,
                                         stdout=subprocess.PIPE,
                                         stderr=subprocess.PIPE)
        if hasattr(self, 'feed_stdin'):
            self._stdin_feeder = Thread(target=self._feed_stdin, args=(self._process.stdin,))
            self._stdin_feeder.daemon = True
            self._stdin_feeder.start()
        else:
            self._stdin_feeder = None
            self._process.stdin.close()
        self._stderr = BytesIO()
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

    def env(self):
        return None # inherit parent environment by default

    # Define only if needed. We take care of closing stdin.
    #def feed_stdin(self, stdin)

    def _feed_stdin(self, stdin):
        try:
            self.feed_stdin(stdin)
        finally:
            stdin.close()

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
        returncode = self._process.wait()
        logger.debug('done with %s. exit code %d', self.cmdline()[0], returncode)
        return returncode

    MAX_STDERR_LINES = 50

    def _read_stderr(self):
        for line in iter(self._process.stderr.readline, b''):
            self._stderr_line_count += 1
            if self._stderr_line_count <= Command.MAX_STDERR_LINES:
                self._stderr.write(line)
        if self._stderr_line_count > Command.MAX_STDERR_LINES:
            self._stderr.write('[ {} lines ignored ]\n'.format(self._stderr_line_count - Command.MAX_STDERR_LINES).encode('utf-8'))
        self._process.stderr.close()

    @property
    def stderr_content(self):
        return self._stderr.getvalue().decode('utf-8', errors='replace')

    @property
    def stderr(self):
        return self._stderr

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


NO_COMMENT = None


class Container(object, metaclass=ABCMeta):
    def __new__(cls, source):
        if isinstance(source, NonExistingFile):
            new = super(Container, NonExistingContainer).__new__(NonExistingContainer)
            new.__init__(source)
            return new
        else:
            return super(Container, cls).__new__(cls)

    def __init__(self, source):
        self._source = source

    @property
    def source(self):
        return self._source

    def get_members(self):
        """Returns a directory. The key is what is used to match when comparing containers."""
        return OrderedDict([(name, self.get_member(name)) for name in self.get_member_names()])

    def lookup_file(self, *names):
        """Try to fetch a specific file by digging in containers."""
        name, remainings = names[0], names[1:]
        try:
            file = self.get_member(name)
        except KeyError:
            return None
        logger.debug('lookup_file(%s) -> %s', names, file)
        diffoscope.comparators.specialize(file)
        if not remainings:
            return file
        container = file.as_container
        if not container:
            return None
        return container.lookup_file(*remainings)

    @abstractmethod
    def get_member_names(self):
        raise NotImplemented

    @abstractmethod
    def get_member(self, member_name):
        raise NotImplemented

    def comparisons(self, other):
        my_members = self.get_members()
        my_reminders = OrderedDict()
        other_members = other.get_members()
        # keep it sorted like my members
        while my_members:
            my_member_name, my_member = my_members.popitem(last=False)
            if my_member_name in other_members:
                yield my_member, other_members.pop(my_member_name), NO_COMMENT
            else:
                my_reminders[my_member_name] = my_member
        my_members = my_reminders
        for my_name, other_name, score in diffoscope.comparators.perform_fuzzy_matching(my_members, other_members):
            comment = 'Files similar despite different names (difference score: %d)' % score
            yield my_members.pop(my_name), other_members.pop(other_name), comment
        if Config.general.new_file:
            for my_member in my_members.values():
                yield my_member, NonExistingFile('/dev/null', my_member), NO_COMMENT
            for other_member in other_members.values():
                yield NonExistingFile('/dev/null', other_member), other_member, NO_COMMENT

    def compare(self, other, source=None):
        return starmap(diffoscope.comparators.compare_commented_files, self.comparisons(other))


class NonExistingContainer(Container):
    def get_member_names(self):
        return self.source.other_file.as_container.get_member_names()

    def get_member(self, member_name):
        return NonExistingFile('/dev/null')


class ArchiveMember(File):
    def __init__(self, container, member_name):
        super().__init__(container=container)
        self._name = member_name
        self._temp_dir = None
        self._path = None

    @property
    def path(self):
        if self._path is None:
            logger.debug('unpacking %s', self._name)
            assert self._temp_dir is None
            self._temp_dir = get_temporary_directory()
            self._path = self.container.extract(self._name, self._temp_dir.name)
        return self._path

    def cleanup(self):
        if self._path is not None:
            self._path = None
        if self._temp_dir is not None:
            self._temp_dir.cleanup()
            self._temp_dir = None
        super().cleanup()

    def is_directory(self):
        return False

    def is_symlink(self):
        return False

    def is_device(self):
        return False


class Archive(Container, metaclass=ABCMeta):
    def __new__(cls, source, *args, **kwargs):
        if isinstance(source, NonExistingFile):
            return super(Container, NonExistingArchive).__new__(NonExistingArchive)
        else:
            return super(Container, cls).__new__(cls)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._archive = self.open_archive()

    def __del__(self):
        self.close_archive()

    @property
    def archive(self):
        return self._archive

    @abstractmethod
    def open_archive(self):
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


class NonExistingArchiveLikeObject(object):
    def getnames(self):
        return []

    def list(self, *args, **kwargs):
        return ''

    def close(self):
        pass


class NonExistingArchive(Archive):
    @property
    def source(self):
        return None

    def open_archive(self):
        return NonExistingArchiveLikeObject()

    def close_archive(self):
        pass

    def get_member_names(self):
        return []

    def extract(self, member_name, dest_dir):
        # should never be called
        raise NotImplemented

    def get_member(self, member_name):
        return NonExistingFile('/dev/null')

    # Be nice to gzip and the likes
    @property
    def path(self):
        return '/dev/null'


class Xxd(Command):
    @tool_required('xxd')
    def cmdline(self):
        return ['xxd', self.path]
