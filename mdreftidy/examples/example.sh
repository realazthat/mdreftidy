#!/bin/bash
# https://gist.github.com/mohanpedala/1e2ff5661761d3abd0385e8223e16425
set -e -x -v -u -o pipefail


python -m mdreftidy.cli \
  "mdreftidy/examples/EXAMPLE.md" \
  -o "mdreftidy/examples/EXAMPLE.all-opts.tidied.md" \
  --move-to-bottom --remove-unused --sort-ref-blocks --renumber
python -m mdreftidy.cli --check \
  "mdreftidy/examples/EXAMPLE.all-opts.tidied.md" \
  --move-to-bottom --remove-unused --sort-ref-blocks --renumber
