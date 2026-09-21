"""Launcher for the long-running live server:  uv run python scripts/serve_live.py --host … --port …

Same flags as `python -m strutture.web`. It exists so that the live server's command line does NOT
contain the module name: helper scripts and agents that stop their own dev servers by process-name
pattern then cannot match (and kill) the live one. Works the same on Windows and macOS.
"""
from strutture.web.__main__ import main

if __name__ == "__main__":
    main()
