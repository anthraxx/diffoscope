============
 diffoscope
============

-------------------------------------------------------
in-depth comparison of files, archives, and directories
-------------------------------------------------------

:Author: lunar@debian.org
:Copyright: GPL-3+
:Manual section: 1
:Manual group: Debian

SYNOPSIS
========

  diffoscope [-h] [--version] [--debug] [--html output] [--text output] [--max-report-size bytes] [--css url] file1 file2

DESCRIPTION
===========

diffoscope will try to get to the bottom of what makes files or
directories different. It will recursively unpack archives of many kinds
and transform various binary formats into more human readable form to
compare them. It can compare two tarballs, ISO images, or PDF just as
easily.

It can be scripted through error codes, and a report can be produced
with the detected differences. The report can be text or HTML.
When no type of report has been selected, diffoscope defaults
to write a text report on the standard output.

diffoscope is developed as part of the “reproducible builds” Debian
project and was formerly known as “debbindiff”.

OPTIONS
=======

-h, --help               show this help message and exit
--version                show program's version number and exit
--debug                  display debug messages
--html output            write HTML report to given file
                         (use - for standard output)
--text output            write plain text report to given file
                         (use - for standard output)
--max-report-size bytes  maximum bytes written in report
--css url                link to an extra CSS for the HTML report

EXIT STATUS
===========

Exit status is 0 if inputs are the same, 1 if different, 2 if trouble.

SEE ALSO
========

* `<http://diffoscope.org/>`
* `<https://wiki.debian.org/ReproducibleBuilds>`
