# -*- coding: utf-8 -*-
#
# diffoscope: in-depth comparison of files, archives, and directories
#
# Copyright © 2014-2015 Jérémy Bobbio <lunar@debian.org>
#           ©      2015 Reiner Herrmann <reiner@reiner-h.de>
#           © 2012-2013 Olivier Matz <zer0@droids-corp.org>
#           ©      2012 Alan De Smet <adesmet@cs.wisc.edu>
#           ©      2012 Sergey Satskiy <sergey.satskiy@gmail.com>
#           ©      2012 scito <info@scito.ch>
#
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
#
#
# Most of the code is borrowed from diff2html.py available at:
# http://git.droids-corp.org/?p=diff2html.git
#
# Part of the code is inspired by diff2html.rb from
# Dave Burt <dave (at) burt.id.au> (mainly for html theme)
#

import io
import os
import re
import sys
import html
import codecs
import hashlib
import logging
import contextlib

from diffoscope import VERSION
from diffoscope.config import Config

from ..icon import FAVICON_BASE64
from ..utils import PrintLimitReached, DiffBlockLimitReached, \
    create_limited_print_func

from . import templates
from .linediff import linediff

# minimum line size, we add a zero-sized breakable space every
# LINESIZE characters
LINESIZE = 20
MAX_LINE_SIZE = 1024
TABSIZE = 8

# Characters we're willing to word wrap on
WORDBREAK = " \t;.,/):-"

DIFFON = "\x01"
DIFFOFF = "\x02"

JQUERY_SYSTEM_LOCATIONS = (
    '/usr/share/javascript/jquery/jquery.js',
)

logger = logging.getLogger(__name__)
re_anchor_prefix = re.compile(r'^[^A-Za-z]')
re_anchor_suffix = re.compile(r'[^A-Za-z-_:\.]')

buf, add_cpt, del_cpt = [], 0, 0
line1, line2, has_internal_linenos = 0, 0, True
hunk_off1, hunk_size1, hunk_off2, hunk_size2 = 0, 0, 0, 0
spl_rows, spl_current_page = 0, 0
spl_print_func, spl_print_ctrl = None, None


def new_unified_diff():
    global buf, add_cpt, del_cpt
    global line1, line2, has_internal_linenos
    global hunk_off1, hunk_size1, hunk_off2, hunk_size2
    global spl_rows, spl_current_page
    global spl_print_func, spl_print_ctrl
    buf, add_cpt, del_cpt = [], 0, 0
    line1, line2, has_internal_linenos = 0, 0, True
    hunk_off1, hunk_size1, hunk_off2, hunk_size2 = 0, 0, 0, 0
    spl_rows, spl_current_page = 0, 0
    spl_print_func, spl_print_ctrl = None, None


def convert(s, ponct=0, tag=''):
    i = 0
    t = io.StringIO()
    for c in s:
        # used by diffs
        if c == DIFFON:
            t.write('<%s>' % tag)
        elif c == DIFFOFF:
            t.write('</%s>' % tag)

        # special highlighted chars
        elif c == "\t" and ponct == 1:
            n = TABSIZE-(i%TABSIZE)
            if n == 0:
                n = TABSIZE
            t.write('<span class="diffponct">\xbb</span>'+'\xa0'*(n-1))
        elif c == " " and ponct == 1:
            t.write('<span class="diffponct">\xb7</span>')
        elif c == "\n" and ponct == 1:
            t.write('<br/><span class="diffponct">\</span>')
        elif ord(c) < 32:
            conv = u"\\x%x" % ord(c)
            t.write('<em>%s</em>' % conv)
            i += len(conv)
        else:
            t.write(html.escape(c))
            i += 1

        if WORDBREAK.count(c) == 1:
            t.write('\u200b')
            i = 0
        if i > LINESIZE:
            i = 0
            t.write('\u200b')

    return t.getvalue()


def output_hunk():
    spl_print_func(u'<tr class="diffhunk"><td colspan="2">Offset %d, %d lines modified</td>'%(hunk_off1, hunk_size1))
    spl_print_func(u'<td colspan="2">Offset %d, %d lines modified</td></tr>\n'%(hunk_off2, hunk_size2))
    row_was_output()


def output_line(s1, s2):
    global line1, line2, has_internal_linenos

    orig1 = s1
    orig2 = s2

    if s1 and len(s1) > MAX_LINE_SIZE:
        s1 = s1[:MAX_LINE_SIZE] + u" ✂"
    if s2 and len(s2) > MAX_LINE_SIZE:
        s2 = s2[:MAX_LINE_SIZE] + u" ✂"

    if s1 == None and s2 == None:
        type_name = "unmodified"
    elif s1 == "" and s2 == "":
        type_name = "unmodified"
    elif s1 == None or s1 == "":
        type_name = "added"
    elif s2 == None or s2 == "":
        type_name = "deleted"
    elif orig1 == orig2 and not s1.endswith('lines removed ]') and not s2.endswith('lines removed ]'):
        type_name = "unmodified"
    else:
        type_name = "changed"
        s1, s2 = linediff(s1, s2, DIFFON, DIFFOFF)

    spl_print_func(u'<tr class="diff%s">' % type_name)
    try:
        if s1:
            if has_internal_linenos:
                spl_print_func(u'<td colspan="2" class="diffpresent">')
            else:
                spl_print_func(u'<td class="diffline">%d </td>' % line1)
                spl_print_func(u'<td class="diffpresent">')
            spl_print_func(convert(s1, ponct=1, tag='del'))
            spl_print_func(u'</td>')
        else:
            spl_print_func(u'<td colspan="2">\xa0</td>')

        if s2:
            if has_internal_linenos:
                spl_print_func(u'<td colspan="2" class="diffpresent">')
            else:
                spl_print_func(u'<td class="diffline">%d </td>' % line2)
                spl_print_func(u'<td class="diffpresent">')
            spl_print_func(convert(s2, ponct=1, tag='ins'))
            spl_print_func(u'</td>')
        else:
            spl_print_func(u'<td colspan="2">\xa0</td>')
    finally:
        spl_print_func(u"</tr>\n", force=True)
        row_was_output()

    m = orig1 and re.match(r"^\[ (\d+) lines removed \]$", orig1)
    if m:
        line1 += int(m.group(1))
    elif orig1:
        line1 += 1
    m = orig2 and re.match(r"^\[ (\d+) lines removed \]$", orig2)
    if m:
        line2 += int(m.group(1))
    elif orig2:
        line2 += 1


def empty_buffer():
    global buf
    global add_cpt
    global del_cpt

    if del_cpt == 0 or add_cpt == 0:
        for l in buf:
            output_line(l[0], l[1])

    elif del_cpt != 0 and add_cpt != 0:
        l0, l1 = [], []
        for l in buf:
            if l[0] != None:
                l0.append(l[0])
            if l[1] != None:
                l1.append(l[1])
        max_len = (len(l0) > len(l1)) and len(l0) or len(l1)
        for i in range(max_len):
            s0, s1 = "", ""
            if i < len(l0):
                s0 = l0[i]
            if i < len(l1):
                s1 = l1[i]
            output_line(s0, s1)

    add_cpt, del_cpt = 0, 0
    buf = []


def spl_print_enter(print_context, rotation_params):
    # Takes ownership of print_context
    global spl_print_func, spl_print_ctrl
    spl_print_ctrl = print_context.__exit__, rotation_params
    spl_print_func = print_context.__enter__()
    _, _, css_url = rotation_params
    # Print file and table headers
    output_header(css_url, spl_print_func)

def spl_had_entered_child():
    global spl_print_ctrl, spl_current_page
    return spl_print_ctrl and spl_print_ctrl[1] and spl_current_page > 0

def spl_print_exit(*exc_info):
    global spl_print_func, spl_print_ctrl
    if not spl_had_entered_child(): return False
    output_footer(spl_print_func)
    _exit, _ = spl_print_ctrl
    spl_print_func, spl_print_ctrl = None, None
    return _exit(*exc_info)

@contextlib.contextmanager
def spl_file_printer(directory, filename):
    with codecs.open(os.path.join(directory,filename), 'w', encoding='utf-8') as f:
        print_func = f.write
        def recording_print_func(s, force=False):
            print_func(s)
            recording_print_func.bytes_written += len(s)
        recording_print_func.bytes_written = 0
        yield recording_print_func

def row_was_output():
    global spl_print_func, spl_print_ctrl, spl_rows, spl_current_page
    spl_rows += 1
    _, rotation_params = spl_print_ctrl
    max_lines = Config().max_diff_block_lines
    max_lines_parent = Config().max_diff_block_lines_parent
    max_lines_ratio = Config().max_diff_block_lines_html_dir_ratio
    max_report_child_size = Config().max_report_child_size
    if not rotation_params:
        # html-dir single output, don't need to rotate
        if spl_rows >= max_lines:
            raise DiffBlockLimitReached()
        return
    else:
        # html-dir output, perhaps need to rotate
        directory, mainname, css_url = rotation_params
        if spl_rows >= max_lines_ratio * max_lines:
            raise DiffBlockLimitReached()

        if spl_current_page == 0: # on parent page
            if spl_rows < max_lines_parent:
                return
        else: # on child page
            # TODO: make this stay below the max, instead of going 1 row over the max
            # will require some backtracking...
            if spl_print_func.bytes_written < max_report_child_size:
                return

    spl_current_page += 1
    filename = "%s-%s.html" % (mainname, spl_current_page)

    if spl_current_page > 1:
        # previous page was a child, close it
        spl_print_func(templates.UD_TABLE_FOOTER % {"filename": html.escape(filename), "text": "load diff"}, force=True)
        spl_print_exit(None, None, None)

    # rotate to the next child page
    context = spl_file_printer(directory, filename)
    spl_print_enter(context, rotation_params)
    spl_print_func(templates.UD_TABLE_HEADER)


def output_unified_diff_table(unified_diff, _has_internal_linenos):
    global add_cpt, del_cpt
    global line1, line2, has_internal_linenos
    global hunk_off1, hunk_size1, hunk_off2, hunk_size2

    has_internal_linenos = _has_internal_linenos
    spl_print_func(templates.UD_TABLE_HEADER)
    try:
        bytes_processed = 0
        for l in unified_diff.splitlines():
            bytes_processed += len(l) + 1
            m = re.match(r'^--- ([^\s]*)', l)
            if m:
                empty_buffer()
                continue
            m = re.match(r'^\+\+\+ ([^\s]*)', l)
            if m:
                empty_buffer()
                continue

            m = re.match(r"@@ -(\d+),?(\d*) \+(\d+),?(\d*)", l)
            if m:
                empty_buffer()
                hunk_data = map(lambda x:x=="" and 1 or int(x), m.groups())
                hunk_off1, hunk_size1, hunk_off2, hunk_size2 = hunk_data
                line1, line2 = hunk_off1, hunk_off2
                output_hunk()
                continue

            if re.match(r'^\[', l):
                empty_buffer()
                spl_print_func(u'<td colspan="2">%s</td>\n' % l)

            if re.match(r"^\\ No newline", l):
                if hunk_size2 == 0:
                    buf[-1] = (buf[-1][0], buf[-1][1] + '\n' + l[2:])
                else:
                    buf[-1] = (buf[-1][0] + '\n' + l[2:], buf[-1][1])
                continue

            if hunk_size1 <= 0 and hunk_size2 <= 0:
                empty_buffer()
                continue

            m = re.match(r"^\+\[ (\d+) lines removed \]$", l)
            if m:
                add_cpt += int(m.group(1))
                hunk_size2 -= int(m.group(1))
                buf.append((None, l[1:]))
                continue

            if re.match(r"^\+", l):
                add_cpt += 1
                hunk_size2 -= 1
                buf.append((None, l[1:]))
                continue

            m = re.match(r"^-\[ (\d+) lines removed \]$", l)
            if m:
                del_cpt += int(m.group(1))
                hunk_size1 -= int(m.group(1))
                buf.append((l[1:], None))
                continue

            if re.match(r"^-", l):
                del_cpt += 1
                hunk_size1 -= 1
                buf.append((l[1:], None))
                continue

            if re.match(r"^ ", l) and hunk_size1 and hunk_size2:
                empty_buffer()
                hunk_size1 -= 1
                hunk_size2 -= 1
                buf.append((l[1:], l[1:]))
                continue

            empty_buffer()

        empty_buffer()
        return True
    except DiffBlockLimitReached:
        total = len(unified_diff)
        bytes_left = total - bytes_processed
        frac = bytes_left / total
        spl_print_func(
            u'<tr class="error">'
            u'<td colspan="4">Max diff block lines reached; %s/%s bytes (%.2f%%) of diff not shown.'
            u"</td></tr>" % (bytes_left, total, frac*100), force=True)
        return False
    except PrintLimitReached:
        assert not spl_had_entered_child() # limit reached on the parent page
        spl_print_func(u'<tr class="error"><td colspan="4">Max output size reached.</td></tr>', force=True)
        raise
    finally:
        spl_print_func(u"</table>", force=True)


def output_unified_diff(print_func, css_url, directory, unified_diff, has_internal_linenos):
    global spl_print_func, spl_print_ctrl, spl_current_page
    new_unified_diff()
    rotation_params = None
    if directory:
        mainname = hashlib.md5(unified_diff.encode('utf-8')).hexdigest()
        rotation_params = directory, mainname, css_url
    try:
        spl_print_func = print_func
        spl_print_ctrl = None, rotation_params
        truncated = not output_unified_diff_table(unified_diff, has_internal_linenos)
    except:
        if not spl_print_exit(*sys.exc_info()): raise
    else:
        spl_print_exit(None, None, None)
    finally:
        spl_print_ctrl = None
        spl_print_func = None

    if spl_current_page > 0:
        noun = "pieces" if spl_current_page > 1 else "piece"
        text = "load diff (%s %s%s)" % (spl_current_page, noun, (", truncated" if truncated else ""))
        print_func(templates.UD_TABLE_FOOTER % {"filename": html.escape("%s-1.html" % mainname), "text": text}, force=True)

def escape_anchor(val):
    """
    ID and NAME tokens must begin with a letter ([A-Za-z]) and may be followed
    by any number of letters, digits ([0-9]), hyphens ("-"), underscores ("_"),
    colons (":"), and periods (".").
    """

    for pattern, repl in (
        (re_anchor_prefix, 'D'),
        (re_anchor_suffix, '-'),
    ):
        val = pattern.sub(repl, val)

    return val

def output_difference(difference, print_func, css_url, directory, parents):
    logger.debug('html output for %s', difference.source1)
    sources = parents + [difference.source1]
    print_func(u'<div class="difference">')
    try:
        print_func(u'<div class="diffheader">')
        if difference.source1 == difference.source2:
            print_func(u'<div class="diffcontrol">[−]</div>')
            print_func(u'<div><span class="source">%s</span>'
                       % html.escape(difference.source1))
        else:
            print_func(u'<div class="diffcontrol diffcontrol-double">[−]</div>')
            print_func(u'<div><span class="source">%s</span> vs.</div>'
                       % html.escape(difference.source1))
            print_func(u'<div><span class="source">%s</span>'
                       % html.escape(difference.source2))
        anchor = escape_anchor('/'.join(sources[1:]))
        print_func(u' <a class="anchor" href="#%s" name="%s">\xb6</a>' % (anchor, anchor))
        print_func(u"</div>")
        if difference.comments:
            print_func(u'<div class="comment">%s</div>'
                       % u'<br />'.join(map(html.escape, difference.comments)))
        print_func(u"</div>")
        if difference.unified_diff:
            output_unified_diff(print_func, css_url, directory, difference.unified_diff, difference.has_internal_linenos)
        for detail in difference.details:
            output_difference(detail, print_func, css_url, directory, sources)
    except PrintLimitReached:
        logger.debug('print limit reached')
        raise
    finally:
        print_func(u"</div>", force=True)


def output_header(css_url, print_func):
    if css_url:
        css_link = '<link href="%s" type="text/css" rel="stylesheet" />' % css_url
    else:
        css_link = ''
    print_func(templates.HEADER % {'title': html.escape(' '.join(sys.argv)),
                         'favicon': FAVICON_BASE64,
                         'css_link': css_link,
                        })

def output_footer(print_func):
    print_func(templates.FOOTER % {'version': VERSION}, force=True)


def output_html(difference, css_url=None, print_func=None):
    """
    Default presenter, all in one HTML file
    """
    if print_func is None:
        print_func = print
    print_func = create_limited_print_func(print_func, Config().max_report_size)
    try:
        output_header(css_url, print_func)
        output_difference(difference, print_func, css_url, None, [])
    except PrintLimitReached:
        logger.debug('print limit reached')
        print_func(u'<div class="error">Max output size reached.</div>',
                   force=True)
    output_footer(print_func)

@contextlib.contextmanager
def file_printer(directory, filename):
    with codecs.open(os.path.join(directory,filename), 'w', encoding='utf-8') as f:
        yield f.write

def output_html_directory(directory, difference, css_url=None, jquery_url=None):
    """
    Multi-file presenter. Writes to a directory, and puts large diff tables
    into files of their own.

    This uses jQuery. By default it uses /usr/share/javascript/jquery/jquery.js
    (symlinked, so that you can still share the result over HTTP).
    You can also pass --jquery URL to diffoscope to use a central jQuery copy.
    """
    if not os.path.exists(directory):
        os.makedirs(directory)

    if not os.path.isdir(directory):
        raise ValueError("%s is not a directory" % directory)

    if not jquery_url:
        jquery_symlink = os.path.join(directory, "jquery.js")
        if os.path.exists(jquery_symlink):
            jquery_url = "./jquery.js"
        else:
            if os.path.lexists(jquery_symlink):
                os.unlink(jquery_symlink)
            for path in JQUERY_SYSTEM_LOCATIONS:
                if os.path.exists(path):
                    os.symlink(path, jquery_symlink)
                    jquery_url = "./jquery.js"
                    break
            if not jquery_url:
                logger.warning('--jquery was not specified and jQuery was not found in any known location. Disabling on-demand inline loading.')
                logger.debug('Locations searched: %s', ', '.join(JQUERY_SYSTEM_LOCATIONS))
    if jquery_url == 'disable':
        jquery_url = None

    with file_printer(directory, "index.html") as print_func:
        print_func = create_limited_print_func(print_func, Config().max_report_size)
        try:
            output_header(css_url, print_func)
            output_difference(difference, print_func, css_url, directory, [])
        except PrintLimitReached:
            logger.debug('print limit reached')
            print_func(u'<div class="error">Max output size reached.</div>',
                       force=True)
        if jquery_url:
            print_func(templates.SCRIPTS % {'jquery_url': html.escape(jquery_url)}, force=True)
        output_footer(print_func)
