#!/bin/bash
# WARNING: This file is auto-generated by snipinator. Do not edit directly.
# SOURCE: `mdreftidy/examples/simple_example.sh.jinja2`.

# https://gist.github.com/mohanpedala/1e2ff5661761d3abd0385e8223e16425
set -e -x -v -u -o pipefail
set +v
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color
PS4="${GREEN}$ ${NC}"

: ECHO_SNIPPET_START
# SNIPPET_START
# View the template file.
cat "mdreftidy/examples/SIMPLE.md"

python -m mdreftidy.cli \
  "mdreftidy/examples/SIMPLE.md" \
  -o "mdreftidy/examples/SIMPLE.tidied.md" \
  --move-to-bottom --remove-unused --sort-ref-blocks --renumber

# Now --check to verify:
python -m mdreftidy.cli \
  --check \
  "mdreftidy/examples/SIMPLE.tidied.md" \
  --move-to-bottom --remove-unused --sort-ref-blocks --renumber

# View the remotified file.
cat "mdreftidy/examples/SIMPLE.tidied.md"

# SNIPPET_END
: ECHO_SNIPPET_END
