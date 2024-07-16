#!/bin/bash
# https://gist.github.com/mohanpedala/1e2ff5661761d3abd0385e8223e16425
set -e -x -v -u -o pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
NC='\033[0m'

python -m mdreftidy.cli --help


# multiline EOF
MARKDOWN=$(cat <<EOF


EOF
)

echo "${MARKDOWN}" | python -m mdreftidy.cli - -o "-"


echo -e "${GREEN}duplicate_refs_test.sh PASSED${NC}"
