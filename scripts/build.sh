#!/usr/bin/env bash
set -xe

DIR=$(mktemp -d) || exit 1
cd "$DIR"
COMPILE_PATH=$1
OUTPUT_PATH=$2

Rscript -e "devtools::install_deps('"$COMPILE_PATH"')"
R CMD INSTALL --no-demo --no-help --no-docs --clean --preclean --build "$COMPILE_PATH"
PACKAGE=$(find . -maxdepth 1 -type f -name '[^.]?*' -printf %f -quit)
TAR_FILENAME=$(basename $PACKAGE)
cp "$PACKAGE" "$OUTPUT_PATH"
rm -rf "$COMPILE_PATH"
rm -rf "$DIR"
BIN_DIR=$(readlink -f "$OUTPUT_PATH"/"$TAR_FILENAME")
echo "$BIN_DIR"
