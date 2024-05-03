#!/bin/bash
# https://gist.github.com/mohanpedala/1e2ff5661761d3abd0385e8223e16425
set -e -x -v -u -o pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
NC='\033[0m'

python -m mdreftidy.cli --help


# multiline EOF
MARKDOWN=$(cat <<EOF

[5]: https://example.com/5
[5]: https://example.com/6

EOF
)
echo "${MARKDOWN}" | python -m mdreftidy.cli - -o "-" || EXIT_CODE=$? && true
if [[ ${EXIT_CODE} -eq 0 ]]; then
  echo -e "${RED}ERROR: Expected non-zero exit code${NC}"
  exit 1
else
  echo -e "${GREEN}PASSED: mdreftidy fails on duplicate refs, as expected${NC}"
fi


echo -e "${GREEN}duplicate_refs_test.sh PASSED${NC}"
