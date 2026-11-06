#!/usr/bin/env bash
set -euo pipefail

project_root=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
cd "$project_root"
exec timeout "${SITES_BUILD_TIMEOUT:-300}" node --import ./scripts/sites-env.mjs ./node_modules/vite/bin/vite.js build "$@"
