#!/bin/bash
set -euo pipefail
kernel_build=$1
module_build=$2
if /usr/bin/grep -q '^CONFIG_CC_IS_CLANG=y$' "$kernel_build/.config"; then
  exec /usr/bin/make -C "$kernel_build" M="$module_build" LLVM=1 modules
else
  exec /usr/bin/make -C "$kernel_build" M="$module_build" modules
fi
