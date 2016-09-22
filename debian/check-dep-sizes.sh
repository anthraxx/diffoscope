#!/bin/sh
# Check sizes of diffoscope's dependencies (including recommends)
# Give ~i to only list packages installed on your system.
LC_ALL=C aptitude search '~Rrecommends:diffoscope|~R~Rrecommends:diffoscope'" $1" \
  --disable-columns -F '%I %p' \
  | sed -e 's/ kB / KB /g' \
  | LC_ALL=C sort -k2,2 -k1n,1n \
  | sed -e 's/ KB / kB /g'
