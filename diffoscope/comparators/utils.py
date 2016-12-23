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

import abc
import os
import re
import io
import stat
import threading
import itertools
import subprocess
import collections

import diffoscope.comparators

from diffoscope import logger, tool_required, get_temporary_directory
from diffoscope.config import Config
from diffoscope.progress import Progress
from diffoscope.profiling import profile
from diffoscope.comparators.binary import File, NonExistingFile


class Command(object, metaclass=abc.ABCMeta):
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
            self._stdin_feeder = threading.Thread(target=self._feed_stdin, args=(self._process.stdin,))
            self._stdin_feeder.daemon = True
            self._stdin_feeder.start()
        else:
            self._stdin_feeder = None
            self._process.stdin.close()
        self._stderr = io.BytesIO()
        self._stderr_line_count = 0
        self._stderr_reader = threading.Thread(target=self._read_stderr)
        self._stderr_reader.daemon = True
        self._stderr_reader.start()

    @property
    def path(self):
        return self._path

    @abc.abstractmethod
    def cmdline(self):
        raise NotImplementedError()

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
    if stat.S_ISCHR(mode):
        kind = 'character'
    elif stat.S_ISBLK(mode):
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


DIFF_LINE_NUMBERS_RE = re.compile(r"(^|\n)@@ -(\d+),(\d+) \+(\d+),(\d+) @@(?=\n|$)")

def diff_ignore_line_numbers(diff):
    return DIFF_LINE_NUMBERS_RE.sub(r"\1@@ -XX,XX +XX,XX @@", diff)


NO_COMMENT = None


class Container(object, metaclass=abc.ABCMeta):
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
        """Returns a dictionary. The key is what is used to match when comparing containers."""
        return collections.OrderedDict(self.get_all_members())

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

    @abc.abstractmethod
    def get_member_names(self):
        raise NotImplementedError()

    @abc.abstractmethod
    def get_member(self, member_name):
        raise NotImplementedError()

    def get_all_members(self):
        # If your get_member implementation is O(n) then this will be O(n^2) cost
        # In such cases it is HIGHLY RECOMMENDED to override this as well
        for name in self.get_member_names():
            yield name, self.get_member(name)

    def comparisons(self, other):
        my_members = self.get_members()
        my_reminders = collections.OrderedDict()
        other_members = other.get_members()

        with Progress(max(len(my_members), len(other_members))) as p:
            # keep it sorted like my members
            while my_members:
                my_member_name, my_member = my_members.popitem(last=False)
                if my_member_name in other_members:
                    yield my_member, other_members.pop(my_member_name), NO_COMMENT
                    p.step()
                else:
                    my_reminders[my_member_name] = my_member
            my_members = my_reminders
            for my_name, other_name, score in diffoscope.comparators.perform_fuzzy_matching(my_members, other_members):
                comment = 'Files similar despite different names (difference score: %d)' % score
                yield my_members.pop(my_name), other_members.pop(other_name), comment
                p.step(2)
            if Config().new_file:
                for my_member in my_members.values():
                    yield my_member, NonExistingFile('/dev/null', my_member), NO_COMMENT
                    p.step()
                for other_member in other_members.values():
                    yield NonExistingFile('/dev/null', other_member), other_member, NO_COMMENT
                    p.step()

    def compare(self, other, source=None):
        return itertools.starmap(diffoscope.comparators.compare_commented_files, self.comparisons(other))


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
            with profile('container_extract', self.container):
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


class Archive(Container, metaclass=abc.ABCMeta):
    def __new__(cls, source, *args, **kwargs):
        if isinstance(source, NonExistingFile):
            return super(Container, NonExistingArchive).__new__(NonExistingArchive)
        else:
            return super(Container, cls).__new__(cls)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        with profile('open_archive', self):
            self._archive = self.open_archive()

    def __del__(self):
        with profile('close_archive', self):
            self.close_archive()

    @property
    def archive(self):
        return self._archive

    @abc.abstractmethod
    def open_archive(self):
        raise NotImplementedError()

    @abc.abstractmethod
    def close_archive(self):
        raise NotImplementedError()

    @abc.abstractmethod
    def get_member_names(self):
        raise NotImplementedError()

    @abc.abstractmethod
    def extract(self, member_name, dest_dir):
        raise NotImplementedError()

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
        raise NotImplementedError()

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
