#!/bin/sh
# Prepare a checkout: enables the publication check hooks. Everything the catalogue and the viewer are built from is
# committed in this repository (game data read with Odradek, see THIRD_PARTY_NOTICES.md); nothing is downloaded.
set -e
git config core.hooksPath .githooks
echo "ready: python viewer/build_viewer_data.py --example catalog/example_save.json && python viewer/build_page.py"
