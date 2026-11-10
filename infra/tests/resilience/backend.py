from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

failing = False


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        global failing

        path = urlparse(self.path)
        if path.path == "/control":
            failing = parse_qs(path.query).get("fail") == ["1"]
            status = 200
        elif path.path == "/health":
            status = 200
        elif path.path == "/probe":
            status = 500 if failing else 200
        else:
            status = 404

        self.send_response(status)
        self.end_headers()
        self.wfile.write(b"ok" if status == 200 else b"error")

    def log_message(self, format, *args):
        return


ThreadingHTTPServer(("0.0.0.0", 8000), Handler).serve_forever()
