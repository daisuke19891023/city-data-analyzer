#!/bin/bash

set -e

BASE_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
TARGET_SCRIPT="${BASE_DIR}/setup_github_repo.sh"

if [ ! -x "$TARGET_SCRIPT" ]; then
  echo "❌ ERROR: Target script not found or not executable: $TARGET_SCRIPT" >&2
  exit 1
fi

exec "$TARGET_SCRIPT"

