#!/usr/bin/env bash
#
# Farmhand - Phase 11: bd-claim wrapper
#
# Installs the atomic bead claim command.
#

set -euo pipefail

_SCRIPT_DIR_11="${SCRIPT_DIR:-$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)}"

# Colors (inherit from parent or define)
BLUE="${BLUE:-\033[0;34m}"
GREEN="${GREEN:-\033[0;32m}"
RED="${RED:-\033[0;31m}"
YELLOW="${YELLOW:-\033[0;33m}"
NC="${NC:-\033[0m}"

echo -e "${BLUE}[11/11] Installing bd-claim...${NC}"

# Ensure ~/.local/bin exists
mkdir -p ~/.local/bin

# Copy the script
if [[ -f "$_SCRIPT_DIR_11/bin/bd-claim" ]]; then
    cp "$_SCRIPT_DIR_11/bin/bd-claim" ~/.local/bin/bd-claim
    chmod +x ~/.local/bin/bd-claim
    echo -e "${GREEN}    ✓ bd-claim installed to ~/.local/bin/bd-claim${NC}"
else
    echo -e "${RED}    ERROR: bin/bd-claim not found in $_SCRIPT_DIR_11${NC}"
    exit 1
fi

# Verify it works
if command -v bd-claim &>/dev/null; then
    echo "    bd-claim is available in PATH"
elif [[ -x ~/.local/bin/bd-claim ]]; then
    echo -e "${YELLOW}    WARNING: bd-claim installed but not in PATH. Add ~/.local/bin to PATH.${NC}"
fi

echo ""
echo "    Usage:"
echo "      bd-claim <bead-id> --paths 'src/**/*.py'"
echo "      bd-claim bd-a1b2 --paths 'src/**/*.py,tests/**/*.py' --ttl 7200"
echo ""
