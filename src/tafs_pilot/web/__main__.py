"""Entrypoint for running the web production console directly via python -m tafs_pilot.web"""

import argparse
from tafs_pilot.web.server import run_server

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Taf's Pilot Web Production Console")
    parser.add_argument("--host", type=str, default="127.0.0.1", help="Host IP")
    parser.add_argument("--port", type=int, default=8000, help="Server port")
    parser.add_argument("--open", action="store_true", help="Automatically open browser")
    args = parser.parse_args()

    run_server(host=args.host, port=args.port, open_browser=args.open)
