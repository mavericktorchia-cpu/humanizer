"""Local web interface. Binds to 127.0.0.1 only; standard library only."""
from __future__ import annotations

import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from . import MODES, analyze, humanize

_PAGE = Path(__file__).with_name("index.html")
MAX_BODY = 2_000_000


class Handler(BaseHTTPRequestHandler):
    def _send(self, status: int, body: bytes, ctype: str) -> None:
        self.send_response(status)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _json(self, status: int, obj: dict) -> None:
        self._send(status, json.dumps(obj).encode(), "application/json")

    def do_GET(self) -> None:  # noqa: N802
        if self.path in ("/", "/index.html"):
            self._send(200, _PAGE.read_bytes(), "text/html; charset=utf-8")
        else:
            self._send(404, b"not found", "text/plain")

    def do_POST(self) -> None:  # noqa: N802
        length = int(self.headers.get("Content-Length") or 0)
        if not 0 < length <= MAX_BODY:
            return self._json(413, {"error": "Text is empty or too large."})
        try:
            req = json.loads(self.rfile.read(length))
            text = str(req.get("text", ""))
        except (ValueError, AttributeError):
            return self._json(400, {"error": "Invalid request."})
        if not text.strip():
            return self._json(400, {"error": "Paste some text first."})

        if self.path == "/api/analyze":
            return self._json(200, {"before": analyze(text).to_dict()})
        if self.path == "/api/humanize":
            mode = req.get("mode", "rules")
            if mode not in MODES:
                return self._json(400, {"error": "Unknown mode."})
            try:
                seed = int(req.get("seed", 0))
                out = humanize(text, mode=mode, seed=seed)
            except (RuntimeError, ValueError) as e:
                return self._json(502, {"error": str(e)})
            except Exception as e:  # never drop the connection on the browser
                return self._json(500, {"error": f"Unexpected error: {e}"})
            return self._json(200, {
                "output": out,
                "before": analyze(text).to_dict(),
                "after": analyze(out).to_dict(),
            })
        self._json(404, {"error": "not found"})

    def log_message(self, *args) -> None:  # keep the terminal quiet
        pass


def serve(port: int = 8000) -> None:
    httpd = ThreadingHTTPServer(("127.0.0.1", port), Handler)
    print(f"Humanizer running at http://127.0.0.1:{port}  (Ctrl+C to stop)")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        httpd.server_close()
