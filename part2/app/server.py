
"""HTTP API for the lab queue."""

import json
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from app.queue import join, take

# Rebuild test: source code updated.

def serve(host: str, port: int, data_dir: str) -> None:
    """Start the queue HTTP server."""

    queue_path = Path(data_dir) / "queue.txt"

    class Handler(BaseHTTPRequestHandler):

        def send_text(self, status: int, message: str) -> None:
            data = message.encode("utf-8")

            self.send_response(status)
            self.send_header(
                "Content-Type", "text/plain; charset=utf-8"
            )
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

        def do_GET(self) -> None:
            if self.path == "/health":
                self.send_text(200, "ok")
            else:
                self.send_text(404, "not found")

        def do_POST(self) -> None:

            if self.path == "/join":
                try:
                    length = int(
                        self.headers.get("Content-Length", "0")
                    )

                    if length <= 0 or length > 65536:
                        raise ValueError("Invalid request size")

                    raw = self.rfile.read(length)
                    payload = json.loads(raw.decode("utf-8"))

                    if not isinstance(payload, dict):
                        raise TypeError("Invalid JSON object")

                    name = payload.get("name")
                    ticket = join(queue_path, name)

                    self.send_text(200, str(ticket))

                except (ValueError, UnicodeError, TypeError):
                    self.send_text(400, "invalid name")

            elif self.path == "/next":
                try:
                    name = take(queue_path)
                    self.send_text(200, name)

                except LookupError:
                    self.send_text(404, "empty")

            else:
                self.send_text(404, "not found")

    server = ThreadingHTTPServer((host, port), Handler)
    server.serve_forever()


def main() -> None:
    port = int(os.environ.get("PORT", "8000"))
    data_dir = os.environ.get("DATA_DIR", "/data")
    serve("0.0.0.0", port, data_dir)


if __name__ == "__main__":
    main()
