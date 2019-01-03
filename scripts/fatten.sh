#!/usr/bin/env bash
set -xe

tarfile=$1

DIR=$(mktemp -d) || exit 1
SCRIPT_DIR="$(cd -P "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
EXCLUDES_FILE=$(readlink -f "$SCRIPT_DIR"/exclude.txt)

echo "tmpdir = $DIR"
cd "$DIR"

tar -xzvf "$tarfile"
PKGDIR=$(find . -maxdepth 1 -type d -name '[^.]?*' -printf %f -quit)

for i in ./**/libs/*.so; do
  # for each library (binary)
  echo "fattening $i"

  # tell it that libs in ../deps are preferred over OS deps

  # shellcheck disable=SC2016
  patchelf --set-rpath '$ORIGIN/../deps' "$i"

  # find path to relative ../deps & create it (if it doesn't exist)
  LIBDIR=$(dirname "$i")
  DEPSDIR=$(readlink -f "$LIBDIR"/../deps/)
  mkdir -p "$DEPSDIR"

  # copy libs to ../deps but exclude low-level ones like libc/libR
  ldd "$i" | grep "=> /" | grep -vf "$EXCLUDES_FILE" |awk '{print $3}' | xargs -I '{}' echo cp -vu '{}' "$DEPSDIR" | bash
done


# recompress the fattened package into original tarfile
tar -czkf "$tarfile" "$PKGDIR"

# clean up
rm -rf "$DIR"
