==============
 trydiffoscope
==============

-----------------------------------------------------------------------------------
in-depth comparison of files, archives, and directories (try.diffoscope.org client)
-----------------------------------------------------------------------------------

:Author: Chris Lamb <lamby@debian.org>
:Copyright: GPL-3+
:Manual section: 1
:Manual group: Debian

SYNOPSIS
========

  trydiffoscope [-h] [--endpoint ENDPOINT] [--text TEXT] [--html HTML] [--url] [--webbrowser] file file

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

trydiffoscope is a command-line API to the trydiffoscope web service.

OPTIONS
=======

-h, --help           show this help message and exit
--endpoint ENDPOINT  specify trydiffoscope API endpoint
--text TEXT          write plain text output to given file
--html HTML          write HTML report to given file
-u, --url            print URL instead of managing results locally
-w, --webbrowser     open webbrowser to URL instead of managing results
                     locally (implies -u)

EXIT STATUS
===========

Exit status is 0 if inputs are the same, 1 if different, 2 if trouble.

SEE ALSO
========

* `<https://diffoscope.org/>`
* `<https://try.diffoscope.org/>`
* `<https://wiki.debian.org/ReproducibleBuilds>`
