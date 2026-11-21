"""Round 71 private World Builder route: atomic wilderness grid generation."""
import json

import app
import round57_http
import round71_wilderness


class Handler(round57_http.Handler):
    def do_POST(self):
        if self.path != "/api/wilderness-grid":
            return super().do_POST()
        try:
            length = int(self.headers.get("Content-Length", "0"))
            if not 0 < length <= 1048576:
                raise ValueError("Invalid request size")
            payload = json.loads(self.rfile.read(length))
            required = {
                "plan", "anchor", "first_id", "rows", "columns", "direction", "prefix"
            }
            if not isinstance(payload, dict) or not required <= payload.keys() <= required | {"seed"}:
                raise ValueError("Unsupported wilderness request")
            result = round71_wilderness.grid(
                payload["plan"], payload["anchor"], payload["first_id"],
                payload["rows"], payload["columns"], payload["direction"], payload["prefix"], payload.get("seed")
            )
            self.reply(200, result)
        except (ValueError, TypeError, KeyError) as exc:
            self.reply(400, {"error": str(exc)})
