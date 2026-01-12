#!/usr/bin/env python3
"""
Claude Code History Viewer - Backward compatibility entry point
This file provides backward compatibility for users who run python3 app.py directly.
"""

try:
    # Try to import from the package (when installed via pip)
    from claude_code_history.app import main
except ImportError:
    # Fallback: import from local package directory
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent))
    from claude_code_history.app import main

if __name__ == '__main__':
    main()
