#!/bin/bash
# https://gist.github.com/mohanpedala/1e2ff5661761d3abd0385e8223e16425
set -e -x -v -u -o pipefail


python -m mdreftidy.cli \
  "mdreftidy/examples/LONG-EXAMPLE.md" \
  -o "mdreftidy/examples/LONG-EXAMPLE.no-opts.tidied.md"
python -m mdreftidy.cli --check "mdreftidy/examples/LONG-EXAMPLE.no-opts.tidied.md"

python -m mdreftidy.cli \
  "mdreftidy/examples/LONG-EXAMPLE.md" \
  -o "mdreftidy/examples/LONG-EXAMPLE.renumber.tidied.md" \
  --renumber
python -m mdreftidy.cli --check \
  "mdreftidy/examples/LONG-EXAMPLE.renumber.tidied.md" --renumber

python -m mdreftidy.cli \
  "mdreftidy/examples/LONG-EXAMPLE.md" \
  -o "mdreftidy/examples/LONG-EXAMPLE.move-to-bottom.tidied.md" \
  --move-to-bottom
python -m mdreftidy.cli --check \
  "mdreftidy/examples/LONG-EXAMPLE.move-to-bottom.tidied.md" --move-to-bottom

python -m mdreftidy.cli \
  "mdreftidy/examples/LONG-EXAMPLE.md" \
  -o "mdreftidy/examples/LONG-EXAMPLE.sort-ref-blocks.tidied.md" \
  --sort-ref-blocks
python -m mdreftidy.cli --check \
  "mdreftidy/examples/LONG-EXAMPLE.sort-ref-blocks.tidied.md" --sort-ref-blocks

python -m mdreftidy.cli \
  "mdreftidy/examples/LONG-EXAMPLE.md" \
  -o "mdreftidy/examples/LONG-EXAMPLE.remove-unused.tidied.md" \
  --remove-unused
python -m mdreftidy.cli --check \
  "mdreftidy/examples/LONG-EXAMPLE.remove-unused.tidied.md" --remove-unused

python -m mdreftidy.cli \
  "mdreftidy/examples/LONG-EXAMPLE.md" \
  -o "mdreftidy/examples/LONG-EXAMPLE.all-opts.tidied.md" \
  --move-to-bottom --remove-unused --sort-ref-blocks --renumber
python -m mdreftidy.cli --check \
  "mdreftidy/examples/LONG-EXAMPLE.all-opts.tidied.md" \
  --move-to-bottom --remove-unused --sort-ref-blocks --renumber
