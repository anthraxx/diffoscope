# -*- coding: utf-8 -*-
#
# debbindiff: highlight differences between two builds of Debian packages
#
# Copyright © 2014-2015 Jérémy Bobbio <lunar@debian.org>
#
# debbindiff is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# debbindiff is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with debbindiff.  If not, see <http://www.gnu.org/licenses/>.

from abc import ABCMeta, abstractproperty, abstractmethod
from binascii import hexlify
from contextlib import contextmanager
from functools import wraps
import os
import os.path
import re
from stat import S_ISCHR, S_ISBLK
import subprocess
import ssdeep
import magic
from debbindiff.difference import Difference
from debbindiff import tool_required, RequiredToolNotFound, logger


@contextmanager
@tool_required('xxd')
def xxd(path):
    p = subprocess.Popen(['xxd', path], shell=False, stdout=subprocess.PIPE,
                         stderr=subprocess.PIPE, close_fds=True)
    yield p.stdout
    p.stdout.close()
    p.stderr.close()
    if p.poll() is None:
        p.terminate()
    p.wait()


def hexdump_fallback(path):
    hexdump = ''
    with open(path) as f:
        for buf in iter(lambda: f.read(32), b''):
            hexdump += u'%s\n' % hexlify(buf)
    return hexdump


def compare_binary_files(path1, path2, source=None):
    try:
        with xxd(path1) as xxd1:
            with xxd(path2) as xxd2:
                return Difference.from_file(xxd1, xxd2, path1, path2, source)
    except RequiredToolNotFound:
        hexdump1 = hexdump_fallback(path1)
        hexdump2 = hexdump_fallback(path2)
        comment = 'xxd not available in path. Falling back to Python hexlify.\n'
        return Difference.from_unicode(hexdump1, hexdump2, path1, path2, source, comment)

SMALL_FILE_THRESHOLD = 65536 # 64 kiB

# decorator for functions which needs to access the file content
# (and so requires a path to be set)
def needs_content(original_method):
    @wraps(original_method)
    def wrapper(self, other, *args, **kwargs):
        with self.get_content(), other.get_content():
            return original_method(self, other, *args, **kwargs)
    return wrapper

class File(object):
    __metaclass__ = ABCMeta

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

    def __repr__(self):
        return '<%s %s %s>' % (self.__class__, self.name, self.path)

    # Path should only be used when accessing the file content (through get_content())
    @property
    def path(self):
        return self._path

    # This might be different from path and is used to do file extension matching
    @property
    def name(self):
        return self._name

    @property
    def magic_file_type(self):
        if not hasattr(self, '_magic_file_type'):
            with self.get_content():
                self._magic_file_type = File.guess_file_type(self.path)
        return self._magic_file_type

    @property
    def fuzzy_hash(self):
        if not hasattr(self, '_fuzzy_hash'):
            with self.get_content():
                self._fuzzy_hash = ssdeep.hash_from_file(self.path)
        return self._fuzzy_hash

    @abstractmethod
    @contextmanager
    def get_content(self):
        raise NotImplemented

    @abstractmethod
    def is_directory():
        raise NotImplemented

    @abstractmethod
    def is_symlink():
        raise NotImplemented

    @abstractmethod
    def is_device():
        raise NotImplemented

    @needs_content
    def compare_bytes(self, other, source=None):
        return compare_binary_files(self.path, other.path, source)

    def _compare_using_details(self, other, source):
        details = [d for d in self.compare_details(other, source) if d is not None]
        if len(details) == 0:
            return None
        difference = Difference(None, self.name, other.name, source=source)
        difference.add_details(details)
        return difference

    @tool_required('cmp')
    @needs_content
    def has_same_content_as(self, other):
        logger.debug('%s has_same_content %s', self, other)
        # try comparing small files directly first
        my_size = os.path.getsize(self.path)
        other_size = os.path.getsize(other.path)
        if my_size == other_size and my_size <= SMALL_FILE_THRESHOLD:
            if file(self.path).read() == file(other.path).read():
                return True

        return 0 == subprocess.call(['cmp', '--silent', self.path, other.path],
                                    shell=False, close_fds=True)


    # To be specialized directly, or by implementing compare_details
    @needs_content
    def compare(self, other, source=None):
        if hasattr(self, 'compare_details'):
            try:
                difference = self._compare_using_details(other, source)
                # no differences detected inside? let's at least do a binary diff
                if difference is None:
                    difference = self.compare_bytes(other, source=source)
                    if difference is None:
                        return None
                    difference.add_comment("No differences found inside, yet data differs")
            except subprocess.CalledProcessError as e:
                difference = self.compare_bytes(other, source=source)
                output = re.sub(r'^', '    ', e.output, flags=re.MULTILINE)
                cmd = ' '.join(e.cmd)
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
            return difference
        return self.compare_bytes(other, source)

class FilesystemFile(File):
    def __init__(self, path):
        self._path = None
        self._name = path

    @contextmanager
    def get_content(self):
        if self._path is not None:
            yield
        else:
            self._path = self._name
            yield
            self._path = None

    def is_directory(self):
        return not os.path.islink(self._name) and os.path.isdir(self._name)

    def is_symlink(self):
        return os.path.islink(self._name)

    def is_device(self):
        mode = os.lstat(self._name).st_mode
        return S_ISCHR(mode) or S_ISBLK(mode)
