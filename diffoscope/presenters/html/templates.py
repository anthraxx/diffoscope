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

HEADER = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta http-equiv="x-ua-compatible" content="IE=edge">
  <meta name="referrer" content="no-referrer" />
  <meta name="generator" content="diffoscope" />
  <link rel="icon" type="image/png" href="data:image/png;base64,%(favicon)s" />
  <title>%(title)s</title>
  <style type="text/css">
    body.diffoscope {
      background: white;
      color: black;
    }
    .diffoscope .footer {
      font-size: small;
    }
    .diffoscope .difference {
      border: outset #888 1px;
      background: #E8E8E8;
      background: rgba(0,0,0,.1);
      padding: 0.5em;
      margin: 0.5em 0;
    }
    .diffoscope .difference table {
      table-layout: fixed;
      width: 100%%;
      border: 0;
    }
    .diffoscope .difference th,
    .diffoscope .difference td {
      border: 0;
    }
    .diffoscope table.diff {
      border: 0;
      border-collapse:collapse;
      font-size:0.75em;
      font-family: 'Lucida Console', monospace;
    }
    .diffoscope table.diff tr:hover td {
      background: #FFFF00;
    }
    .diffoscope .line {
      color:#8080a0
    }
    .diffoscope th {
      background: black;
      color: white
    }
    .diffoscope .diffunmodified td {
      background: #D0D0E0
    }
    .diffoscope .diffhunk td {
      background: #A0A0A0
    }
    .diffoscope .diffadded td {
      background: #CCFFCC
    }
    .diffoscope .diffdeleted td {
      background: #FFCCCC
    }
    .diffoscope .diffchanged td {
      background: #FFFFA0
    }
    .diffoscope ins, del {
      background: #E0C880;
      text-decoration: none
    }
    .diffoscope .diffponct {
      color: #B08080
    }
    .diffoscope .comment {
      font-style: italic;
    }
    .diffoscope .source {
      font-weight: bold;
    }
    .diffoscope .error {
      border: solid black 1px;
      background: red;
      color: white;
      padding: 0.2em;
    }
    .diffoscope .anchor {
      margin-left: 0.5em;
      font-size: 80%%;
      color: #333;
      text-decoration: none;
      display: none;
    }
    .diffoscope .diffheader:hover .anchor {
      display: inline;
    }
    .diffoscope table.diff tr.ondemand td {
      background: #f99;
      text-align: center;
      padding: 0.5em 0;
    }
    .diffoscope table.diff tr.ondemand:hover td {
      background: #faa;
      cursor: pointer;
    }
    .diffoscope .diffcontrol {
      float: left;
      margin-right: 0.3em;
      cursor: pointer;
      display: none; /* currently, only available in html-dir output where jquery is enabled */
    }
    .diffoscope .diffcontrol-double {
      line-height: 200%%;
    }
    .diffoscope .colines {
      width: 3em;
    }
    .diffoscope .coldiff {
      width: 99%%;
    }
  </style>
  %(css_link)s
</head>
<body class="diffoscope">
"""

FOOTER = """
<div class="footer">Generated by <a href="https://diffoscope.org" rel="noopener noreferrer" target="_blank">diffoscope</a> %(version)s</div>
</body>
</html>
"""

SCRIPTS = """
<script src="%(jquery_url)s"></script>
<script type="text/javascript">
$(function() {
  var load_cont = function() {
    var a = $(this).find("a");
    var textparts = /^(.*)\((\d+) pieces?(.*)\)$/.exec(a.text());
    var numleft = Number.parseInt(textparts[2]) - 1;
    var noun = numleft == 1 ? "piece" : "pieces";
    var newtext = textparts[1] + "(" + numleft + " " + noun + textparts[3] + ")";
    var filename = a.attr('href');
    var td = a.parent();
    td.text('... loading ...');
    td.parent().load(filename + " tr", function() {
        // https://stackoverflow.com/a/8452751/946226
        var elems = $(this).children(':first').unwrap();
        // set this behaviour for the next link too
        var td = elems.parent().find(".ondemand td");
        td.find("a").text(newtext);
        td.on('click', load_cont);
    });
    return false;
  };
  $(".ondemand td").on('click', load_cont);
  var diffcontrols = $(".diffcontrol");
  diffcontrols.on('click', function(evt) {
    var control = $(this);
    var target = control.parent().siblings('table.diff, div.difference');
    var orig = target;
    if (evt.shiftKey) {
        var parent = control.parent().parent();
        control = parent.find('.diffcontrol');
        target = parent.find('table.diff, div.difference');
    }
    if (orig.is(":visible")) {
        target.hide();
        control.text("[+]");
    } else {
        target.show();
        control.text("[−]");
    }
  });
  diffcontrols.attr('title','shift-click to show/hide all children too.');
  diffcontrols.show();
});
</script>
"""

UD_TABLE_HEADER = u"""<table class="diff">
<colgroup><col class="colines"/><col class="coldiff"/>
<col class="colines"/><col class="coldiff"/></colgroup>
"""

UD_TABLE_FOOTER = u"""<tr class="ondemand"><td colspan="4">
... <a href="%(filename)s">%(text)s</a> ...
</td></tr>
</table>
"""
