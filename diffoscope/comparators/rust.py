# -*- coding: utf-8 -*-
#
# diffoscope: in-depth comparison of files, archives, and directories
#
# Copyright © 2014-2015 Jérémy Bobbio <lunar@debian.org>
# Copyright © 2016 Ximin Luo <infinity0@debian.org>
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

import zlib
import os.path
import collections

from diffoscope import logger, tool_required
from diffoscope.difference import Difference
from diffoscope.comparators.utils import Archive, get_compressed_content_name


RLIB_BYTECODE_OBJECT_V1_DATASIZE_OFFSET = 15
RLIB_BYTECODE_OBJECT_V1_DATA_OFFSET = 23
ZLIB_DEFAULT_COMPRESSION = b'\x78\x9C'


class RustObjectContainer(Archive):
    def open_archive(self):
        return self

    def close_archive(self):
        pass

    def get_members(self):
        return collections.OrderedDict({'deflate-content': self.get_member(self.get_member_names()[0])})

    def get_member_names(self):
        return [get_compressed_content_name(self.source.path, '.deflate')]

    def extract(self, member_name, dest_dir):
        dest_path = os.path.join(dest_dir, member_name)
        logger.debug('rust-object extracting to %s', dest_path)
        # See librustc_trans/back/link.rs for details of this format
        with open(dest_path, 'wb') as fpw, open(self.source.path, 'rb') as fpr:
            raw_deflate = fpr.read()[RLIB_BYTECODE_OBJECT_V1_DATA_OFFSET:]
            # decompressobj() ignores the (non-existent) checksum; a zlib.decompress() would error
            raw_inflate = zlib.decompressobj().decompress(ZLIB_DEFAULT_COMPRESSION + raw_deflate)
            fpw.write(raw_inflate)
        return dest_path


class RustObjectFile(object):
    CONTAINER_CLASS = RustObjectContainer

    @staticmethod
    def recognizes(file):
        if not file.name.endswith(".deflate"):
            return False
        # See librustc_trans/back/link.rs for details of this format
        with open(file.path, "rb") as fp:
            return fp.read(RLIB_BYTECODE_OBJECT_V1_DATASIZE_OFFSET) == b'RUST_OBJECT\x01\x00\x00\x00'

    def compare_details(self, other, source=None):
        return [Difference.from_text(self.magic_file_type, other.magic_file_type, self, other, source='metadata')]
