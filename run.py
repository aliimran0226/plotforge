"""PlotForge entry point.

Starts the Dash development server and opens the app in the default
browser. Run with ``python run.py`` (add ``--debug`` for hot reload
while developing).
"""

from __future__ import annotations

import argparse
import socket
import sys
import threading
import webbrowser

from plotforge.app import create_app

HOST = "127.0.0.1"
PORT = 8050


def _open_browser(url: str) -> None:
    """Open ``url`` in the default browser (called from a timer thread)."""
    webbrowser.open(url)


def _find_free_port(preferred: int, attempts: int = 20) -> int:
    """Return ``preferred`` if it is free, else the next free port after it.

    Scanning up from the preferred port keeps the URL stable across runs
    while still working when another app (or a previous PlotForge run)
    already holds the default port.
    """
    for offset in range(attempts):
        port = preferred + offset
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind((HOST, port))
            except OSError:
                continue
        return port
    sys.exit(
        f"No free port found in {preferred}-{preferred + attempts - 1}. "
        "Pass one explicitly with --port."
    )


def main() -> None:
    """Parse CLI args, launch the server, and open a browser tab."""
    parser = argparse.ArgumentParser(description="PlotForge - figure playground")
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Run with Dash debug mode (hot reload, in-browser error overlay).",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=None,
        help=f"Port to serve on (default: first free port from {PORT} upward).",
    )
    args = parser.parse_args()

    # An explicit --port is honored as-is (fail loudly if taken); otherwise
    # scan for a free one so a busy 8050 doesn't block startup.
    port = args.port if args.port is not None else _find_free_port(PORT)
    url = f"http://{HOST}:{port}"
    app = create_app()

    # Open the browser shortly after startup. In debug mode Dash restarts
    # the process for hot reload, which would open a second tab - so we
    # only auto-open when not debugging.
    if not args.debug:
        threading.Timer(1.0, _open_browser, args=(url,)).start()

    print(f"PlotForge running at {url} (Ctrl+C to stop)")
    app.run(host=HOST, port=port, debug=args.debug)


if __name__ == "__main__":
    main()
