#!/usr/bin/python2
# -*- coding: utf-8 -*-
#
# debbindiff: highlight differences between two builds of Debian packages
#
# Copyright © 2012 Jeff Bryner
#
# Original version of this file can be found at
# https://github.com/jeffbryner/pyHex/blob/master/pyxxd.py
# 
# debdindiff is free software: you can redistribute it and/or modify
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

import os
import sys
from optparse import OptionParser
from StringIO import StringIO

def readChunk(data,start,end):
    data.seek(start)
    readdata=data.read(end)
    return readdata


#Hex dump code from:
# Author: Boris Mazic
# Date: 04.06.2012
#package rfid.libnfc.hexdump

def hexbytes(xs, group_size=1, byte_separator=' ', group_separator=' '):
    def ordc(c):
        return ord(c) if isinstance(c,str) else c
    
    if len(xs) <= group_size:
        s = byte_separator.join('%02X' % (ordc(x)) for x in xs)
    else:
        r = len(xs) % group_size
        s = group_separator.join(
            [byte_separator.join('%02X' % (ordc(x)) for x in group) for group in zip(*[iter(xs)]*group_size)]
        )
        if r > 0:
            s += group_separator + byte_separator.join(['%02X' % (ordc(x)) for x in xs[-r:]])
    return s.lower()



def hexprint(xs):
    def chrc(c):
        return c if isinstance(c,str) else chr(c)
    
    def ordc(c):
        return ord(c) if isinstance(c,str) else c
    
    def isprint(c):
        return ordc(c) in range(32,127) if isinstance(c,str) else c > 31
    
    return ''.join([chrc(x) if isprint(x) else '.' for x in xs])



def hexdump(xs, group_size=4, byte_separator=' ', group_separator='-', printable_separator='  ', address=0, address_format='%04X', line_size=16):
    if address is None:
        s = hexbytes(xs, group_size, byte_separator, group_separator)
        if printable_separator:
            s += printable_separator + hexprint(xs)
    else:
        r = len(xs) % line_size
        s = ''
        bytes_len = 0
        for offset in range(0, len(xs)-r, line_size):
            chunk = xs[offset:offset+line_size]
            bytes = hexbytes(chunk, group_size, byte_separator, group_separator)
            s += (address_format + ': %s%s\n') % (address + offset, bytes, printable_separator + hexprint(chunk) if printable_separator else '')
            bytes_len = len(bytes)
        
        if r > 0:
            offset = len(xs)-r
            chunk = xs[offset:offset+r]
            bytes = hexbytes(chunk, group_size, byte_separator, group_separator)
            bytes = bytes + ' '*(bytes_len - len(bytes))
            s += (address_format + ': %s%s\n') % (address + offset, bytes, printable_separator + hexprint(chunk) if printable_separator else '')
    
    return s

if __name__ == '__main__':
    parser = OptionParser()
    parser.add_option("-b", dest='bytes'  , default=16, type="int", help="number of bytes to show per line")
    parser.add_option("-s", dest='start' , default=0, type="int", help="starting byte")
    parser.add_option("-l", dest='length' , default=16, type="int", help="length in bytes to dump")     
    parser.add_option("-f", dest='input', default="stdin",help="input: stdin default, drive name, filename, etc")

    (options,args) = parser.parse_args()

    if options.input=="stdin" or options.input == '-':
        src=sys.stdin.read()
        src=StringIO(src)
    else:
        if os.path.exists(options.input):
            src=file(options.input,'rb')
        else:
            sys.stderr.write(options.input)
            sys.stderr.write("No input file specified\n")
            sys.exit()

    data=readChunk(src,options.start,options.length)
    print(hexdump(data, byte_separator='', group_size=2, group_separator=' ', printable_separator='  ', address=options.start, line_size=16,address_format='%07X'))
