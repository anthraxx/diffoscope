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

import io
import os
import re
import abc
import stat
import magic
import binascii
import subprocess

from diffoscope import tool_required, logger
from diffoscope.exc import OutputParsingError, RequiredToolNotFound
from diffoscope.config import Config
from diffoscope.profiling import profile
from diffoscope.difference import Difference

try:
    import tlsh
except ImportError:
    tlsh = None


# helper function to convert to bytes if necessary
def maybe_decode(s):
    if type(s) is bytes:
        return s.decode('utf-8')
    else:
        return s

def hexdump_fallback(path):
    hexdump = io.StringIO()
    with open(path, 'rb') as f:
        for buf in iter(lambda: f.read(32), b''):
            hexdump.write('%s\n' % binascii.hexlify(buf).decode('us-ascii'))
    return hexdump.getvalue()


def compare_binary_files(file1, file2, source=None):
    import diffoscope.comparators.utils

    try:
        return Difference.from_command(
            diffoscope.comparators.utils.Xxd, file1.path, file2.path,
            source=[file1.name, file2.name], has_internal_linenos=True)
    except RequiredToolNotFound:
        hexdump1 = hexdump_fallback(file1.path)
        hexdump2 = hexdump_fallback(file2.path)
        comment = 'xxd not available in path. Falling back to Python hexlify.\n'
        return Difference.from_text(hexdump1, hexdump2, file1.name, file2.name, source, comment)

SMALL_FILE_THRESHOLD = 65536 # 64 kiB


class File(object, metaclass=abc.ABCMeta):
    if hasattr(magic, 'open'): # use Magic-file-extensions from file
        @classmethod
        def guess_file_type(self, path):
            if not hasattr(self, '_mimedb'):
                self._mimedb = magic.open(magic.NONE)
                self._mimedb.load()
            return self._mimedb.file(path)

        @classmethod
        def guess_encoding(self, path):
            if not hasattr(self, '_mimedb_encoding'):
                self._mimedb_encoding = magic.open(magic.MAGIC_MIME_ENCODING)
                self._mimedb_encoding.load()
            return self._mimedb_encoding.file(path)
    else: # use python-magic
        @classmethod
        def guess_file_type(self, path):
            if not hasattr(self, '_mimedb'):
                self._mimedb = magic.Magic()
            return maybe_decode(self._mimedb.from_file(path))

        @classmethod
        def guess_encoding(self, path):
            if not hasattr(self, '_mimedb_encoding'):
                self._mimedb_encoding = magic.Magic(mime_encoding=True)
            return maybe_decode(self._mimedb_encoding.from_file(path))

    def __init__(self, container=None):
        self._container = container

    def __repr__(self):
        return '<%s %s>' % (self.__class__, self.name)

    # This should return a path that allows to access the file content
    @property
    @abc.abstractmethod
    def path(self):
        raise NotImplementedError()

    # Remove any temporary data associated with the file. The function
    # should be idempotent and work during the destructor.
    def cleanup(self):
        if hasattr(self, '_as_container'):
            del self._as_container

    def __del__(self):
        self.cleanup()

    # This might be different from path and is used to do file extension matching
    @property
    def name(self):
        return self._name

    @property
    def container(self):
        return self._container

    @property
    def as_container(self):
        if not hasattr(self.__class__, 'CONTAINER_CLASS'):
            if hasattr(self, '_other_file'):
                return self._other_file.__class__.CONTAINER_CLASS(self)
            return None
        if not hasattr(self, '_as_container'):
            logger.debug('instantiating %s for %s', self.__class__.CONTAINER_CLASS, self)
            self._as_container = self.__class__.CONTAINER_CLASS(self)
        logger.debug('returning a %s for %s', self._as_container.__class__, self)
        return self._as_container

    @property
    def magic_file_type(self):
        if not hasattr(self, '_magic_file_type'):
            self._magic_file_type = File.guess_file_type(self.path)
        return self._magic_file_type

    if tlsh:
        @property
        def fuzzy_hash(self):
            if not hasattr(self, '_fuzzy_hash'):
                # tlsh is not meaningful with files smaller than 512 bytes
                if os.stat(self.path).st_size >= 512:
                    h = tlsh.Tlsh()
                    with open(self.path, 'rb') as f:
                        for buf in iter(lambda: f.read(32768), b''):
                            h.update(buf)
                    h.final()
                    self._fuzzy_hash = h.hexdigest()
                else:
                    self._fuzzy_hash = None
            return self._fuzzy_hash

    @abc.abstractmethod
    def is_directory():
        raise NotImplementedError()

    @abc.abstractmethod
    def is_symlink():
        raise NotImplementedError()

    @abc.abstractmethod
    def is_device():
        raise NotImplementedError()

    def compare_bytes(self, other, source=None):
        return compare_binary_files(self, other, source)

    def _compare_using_details(self, other, source):
        details = []
        if hasattr(self, 'compare_details'):
            details.extend(filter(None, self.compare_details(other, source)))
        if self.as_container:
            details.extend(filter(None, self.as_container.compare(other.as_container)))
        if not details:
            return None
        difference = Difference(None, self.name, other.name, source=source)
        difference.add_details(details)
        return difference

    def has_same_content_as(self, other):
        logger.debug('Binary.has_same_content: %s %s', self, other)
        # try comparing small files directly first
        try:
            my_size = os.path.getsize(self.path)
            other_size = os.path.getsize(other.path)
        except OSError:
            # files not readable (e.g. broken symlinks) or something else,
            # just assume they are different
            return False
        if my_size == other_size and my_size <= SMALL_FILE_THRESHOLD:
            try:
                with profile('command', 'cmp (internal)'):
                    with open(self.path, 'rb') as file1, open(other.path, 'rb') as file2:
                        return file1.read() == file2.read()
            except OSError:
                # one or both files could not be opened for some reason,
                # assume they are different
                return False

        return self.cmp_external(other)

    @tool_required('cmp')
    def cmp_external(self, other):
        return 0 == subprocess.call(['cmp', '-s', self.path, other.path],
                                    shell=False, close_fds=True)


    # To be specialized directly, or by implementing compare_details
    def compare(self, other, source=None):
        if hasattr(self, 'compare_details') or self.as_container:
            try:
                difference = self._compare_using_details(other, source)
                # no differences detected inside? let's at least do a binary diff
                if difference is None:
                    difference = self.compare_bytes(other, source=source)
                    if difference is None:
                        return None
                    difference.add_comment("No file format specific differences found inside, yet data differs")
            except subprocess.CalledProcessError as e:
                difference = self.compare_bytes(other, source=source)
                if e.output:
                    output = re.sub(r'^', '    ', e.output.decode('utf-8', errors='replace'), flags=re.MULTILINE)
                else:
                    output = '<none>'
                cmd = ' '.join(e.cmd)
                if difference is None:
                    return None
                difference.add_comment("Command `%s` exited with %d. Output:\n%s"
                                       % (cmd, e.returncode, output))
            except RequiredToolNotFound as e:
                difference = self.compare_bytes(other, source=source)
                if difference is None:
                    return None
                difference.add_comment(
                    "'%s' not available in path. Falling back to binary comparison." % e.command)
                package = e.get_package()
                if package:
                    difference.add_comment("Install '%s' to get a better output." % package)
            except OutputParsingError as e:
                difference = self.compare_bytes(other, source=source)
                if difference is None:
                    return None
                difference.add_comment("Error parsing output of `%s` for %s" %
                        (e.command, e.object_class))
            return difference
        return self.compare_bytes(other, source)


class FilesystemFile(File):
    def __init__(self, path, container=None):
        super().__init__(container=container)
        self._name = path

    @property
    def path(self):
        return self._name

    def is_directory(self):
        return not os.path.islink(self._name) and os.path.isdir(self._name)

    def is_symlink(self):
        return os.path.islink(self._name)

    def is_device(self):
        mode = os.lstat(self._name).st_mode
        return stat.S_ISCHR(mode) or stat.S_ISBLK(mode)


class NonExistingFile(File):
    """Represents a missing file when comparing containers"""

    @staticmethod
    def recognizes(file):
        if isinstance(file, FilesystemFile) and not os.path.lexists(file.name):
            assert Config().new_file, '%s does not exist' % file.name
            return True
        return False

    def __init__(self, path, other_file=None):
        self._name = path
        self._other_file = other_file

    @property
    def path(self):
        return '/dev/null'

    @property
    def other_file(self):
        return self._other_file

    @other_file.setter
    def other_file(self, value):
        self._other_file = value

    def has_same_content_as(self, other):
        return False

    def is_directory(self):
        return False

    def is_symlink(self):
        return False

    def is_device(self):
        return False

    def compare(self, other, source=None):
        # So now that comparators are all object-oriented, we don't have any clue on how to
        # perform a meaningful comparison right here. So we are good do the comparison backward
        # (where knowledge of the file format lies) and and then reverse it.
        if isinstance(other, NonExistingFile):
            return Difference(None, self.name, other.name, comment='Trying to compare two non-existing files.')
        logger.debug('Performing backward comparison')
        backward_diff = other.compare(self, source)
        if not backward_diff:
            return None
        return backward_diff.get_reverse()

    # Be nice to text comparisons
    @property
    def encoding(self):
        return self._other_file.encoding

    # Be nice to device comparisons
    def get_device(self):
        return ''

    # Be nice to metadata comparisons
    @property
    def magic_file_type(self):
        return self._other_file.magic_file_type

    # Be nice to .changes and .dsc comparisons
    @property
    def deb822(self):
        class DummyChanges(dict):
            get_as_string = lambda self, _: ''
        return DummyChanges(Files=[], Version='')
