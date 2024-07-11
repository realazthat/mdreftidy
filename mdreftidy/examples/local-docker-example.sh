#!/bin/bash
# https://gist.github.com/mohanpedala/1e2ff5661761d3abd0385e8223e16425
set -e -x -v -u -o pipefail

YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Don't run this in act/GH actions because act doesn't play with with nested
# docker; the paths mess up.
if [[ -n "${GITHUB_ACTIONS:-}" ]]; then
  echo -e "${YELLOW}This script is not meant to be run in GitHub Actions.${NC}"
  exit 0
fi

# DOCKER_START
# Build the docker image.
docker build -t my-mdreftidy-image .

# Print usage.
docker run --rm --tty my-mdreftidy-image --help

# /data in the docker image is the working directory, so paths are simpler.
docker run --rm --tty \
  -u "$(id -u):$(id -g)" \
  -v "${PWD}:/data" \
  my-mdreftidy-image \
  mdreftidy/examples/EXAMPLE.md \
  --move-to-bottom --remove-unused --sort-ref-blocks --renumber \
  -o -
# DOCKER_END
