============
 debbindiff
============

-----------------------------------------------------------
highlight differences between two builds of Debian packages
-----------------------------------------------------------

:Author: lunar@debian.org
:Copyright: GPL-3+
:Manual section: 1
:Manual group: Debian

SYNOPSIS
========

  debbindiff [-h] [--version] [--debug] [--html output] [--text output] [--max-report-size bytes] [--css url] file1 file2

DESCRIPTION
===========

debbindiff was designed to easily compare two builds of the same Debian
package, and understand their differences.

It can be scripted through error codes, and a report can be produced
with the detected differences. The report can be text or HTML.
When no type of report has been selected, debbindiff defaults
to write a text report on the standard output.

debbindiff was written as part of the “reproducible builds” Debian
project.

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

* `<https://wiki.debian.org/ReproducibleBuilds>`
