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

  debbindiff [-h] [--version] [--debug] [--html output] file1 file2

DESCRIPTION
===========

debbindiff was designed to easily compare two builds of the same Debian
package, and understand their differences.

It can be scripted through error codes, and an HTML report can be produced
with the detected differences.

debbindiff was written as part of the “reproducible builds” Debian
project.

OPTIONS
=======

-h, --help     show this help message and exit
--version      show program's version number and exit
--debug        display debug messages
--html output  write HTML report to given file

SEE ALSO
========

* `<https://wiki.debian.org/ReproducibleBuilds>`
