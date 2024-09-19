#!/bin/bash
# https://gist.github.com/mohanpedala/1e2ff5661761d3abd0385e8223e16425
set -e -x -v -u -o pipefail


python -m mdreftidy.cli \
  "examples/LONG.md" \
  -o "examples/LONG.no-opts.tidied.md"
python -m mdreftidy.cli --check "examples/LONG.no-opts.tidied.md"

python -m mdreftidy.cli \
  "examples/LONG.md" \
  -o "examples/LONG.renumber.tidied.md" \
  --renumber
python -m mdreftidy.cli --check \
  "examples/LONG.renumber.tidied.md" --renumber

python -m mdreftidy.cli \
  "examples/LONG.md" \
  -o "examples/LONG.move-to-bottom.tidied.md" \
  --move-to-bottom
python -m mdreftidy.cli --check \
  "examples/LONG.move-to-bottom.tidied.md" --move-to-bottom

python -m mdreftidy.cli \
  "examples/LONG.md" \
  -o "examples/LONG.sort-ref-blocks.tidied.md" \
  --sort-ref-blocks
python -m mdreftidy.cli --check \
  "examples/LONG.sort-ref-blocks.tidied.md" --sort-ref-blocks

python -m mdreftidy.cli \
  "examples/LONG.md" \
  -o "examples/LONG.remove-unused.tidied.md" \
  --remove-unused
python -m mdreftidy.cli --check \
  "examples/LONG.remove-unused.tidied.md" --remove-unused

python -m mdreftidy.cli \
  "examples/LONG.md" \
  -o "examples/LONG.all-opts.tidied.md" \
  --move-to-bottom --remove-unused --sort-ref-blocks --renumber
python -m mdreftidy.cli --check \
  "examples/LONG.all-opts.tidied.md" \
  --move-to-bottom --remove-unused --sort-ref-blocks --renumber
