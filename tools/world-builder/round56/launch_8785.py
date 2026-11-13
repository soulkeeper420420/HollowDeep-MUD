"""Round 56 isolated visual World Builder."""
from http.server import ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit
import round55_http

ROOT = Path(__file__).resolve().parent

class Handler(round55_http.Handler):
    def do_GET(self):
        if urlsplit(self.path).path == "/":
            data = (ROOT / "visual.html").read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)
            return
        return super().do_GET()

if __name__ == "__main__":
    print("Round 56 listening on 127.0.0.1:8785", flush=True)
    ThreadingHTTPServer(("127.0.0.1", 8785), Handler).serve_forever()
