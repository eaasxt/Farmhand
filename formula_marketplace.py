#!/usr/bin/env python3
"""
Formula CLI Extension - Molecule Marketplace
Integration script for extending the existing formula CLI with marketplace functionality.
"""

import sys
import os
import subprocess
from pathlib import Path

# Path to the marketplace CLI
MARKETPLACE_CLI = Path(__file__).parent / "molecule-marketplace" / "cli" / "marketplace.py"

def main():
    """Main entry point for formula marketplace commands."""

    # Check if this is being called as a subcommand of formula
    if len(sys.argv) > 1 and sys.argv[1] == 'marketplace':
        # Remove 'marketplace' from argv and pass rest to marketplace CLI
        marketplace_args = sys.argv[2:]

        # Execute marketplace CLI
        try:
            cmd = [sys.executable, str(MARKETPLACE_CLI)] + marketplace_args
            result = subprocess.run(cmd, check=False)
            sys.exit(result.returncode)
        except Exception as e:
            print(f"Error running marketplace command: {e}", file=sys.stderr)
            sys.exit(1)
    else:
        # Show help for marketplace commands
        print("Gas Town MEOW Stack - Formula Marketplace Extension")
        print()
        print("Usage: formula marketplace <command> [options]")
        print()
        print("Available Commands:")
        print("  init         Initialize the molecule marketplace")
        print("  list         List available templates")
        print("  search       Search templates")
        print("  show         Show template details")
        print("  install      Install a template")
        print("  recommend    Get AI-powered recommendations")
        print("  categories   List template categories")
        print("  stats        Show marketplace statistics")
        print()
        print("Examples:")
        print("  formula marketplace init")
        print("  formula marketplace list --category web-dev")
        print("  formula marketplace search react")
        print("  formula marketplace install react-node-fullstack ./my-project")
        print("  formula marketplace recommend --project-path .")
        print()
        print("For detailed help on a command:")
        print("  formula marketplace <command> --help")


if __name__ == '__main__':
    main()