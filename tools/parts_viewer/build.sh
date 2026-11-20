#!/bin/sh
# Rebuild the three.js bundle used by parts.html (only needed when upgrading three.js).
set -e
cd "$(dirname "$0")"
npm i --no-save three@0.180.0 esbuild@0.24
npx esbuild entry.js --bundle --minify --format=iife --legal-comments=eof --outfile=parts_viewer.bundle.js
