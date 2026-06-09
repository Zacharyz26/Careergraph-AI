#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

cd "$ROOT_DIR/frontend"
npm install

if [[ ! -f .env.local ]]; then
  cp .env.example .env.local
fi

printf 'Frontend dependencies installed in %s\n' "$ROOT_DIR/frontend"
