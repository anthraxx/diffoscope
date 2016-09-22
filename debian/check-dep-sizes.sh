#!/bin/sh
# Check sizes of diffoscope's dependencies (including recommends)
# Give ~i to only list packages installed on your system.
pkg=diffoscope
d=~R
r=~Rrecommends:
LC_ALL=C aptitude search "($d$pkg|$r$pkg|$d$d$pkg|$d$r$pkg|$r$d$pkg|$r$r$pkg) $1" \
  --disable-columns -F '%I %p' \
  | sed -e 's/ kB / KB /g' \
  | LC_ALL=C sort -k2,2 -k1n,1n \
  | sed -e 's/ KB / kB /g'
