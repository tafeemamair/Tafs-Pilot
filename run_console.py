"""Convenience launcher for the Taf's Pilot Web Production Console.

Usage:
    python run_console.py
    python run_console.py --port 8080 --open
"""

import argparse
import os
import sys

# Ensure src/ is in the python path
SRC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "src")
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

from tafs_pilot.web.server import run_server

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Launch Taf's Pilot Web Production Console")
    parser.add_argument("--host", type=str, default="127.0.0.1", help="Host address")
    parser.add_argument("--port", type=int, default=8000, help="Port to listen on")
    parser.add_argument("--open", action="store_true", default=True, help="Open default web browser")
    args = parser.parse_args()

    run_server(host=args.host, port=args.port, open_browser=args.open)
