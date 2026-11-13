"""Round 57: native-backed plan validation."""
import json
import app
import round55_http

class Handler(round55_http.Handler):
    def do_POST(self):
        if self.path != "/api/validate":
            return super().do_POST()

        try:
            length = int(self.headers.get("Content-Length", "0"))
            if not 0 < length <= 1048576:
                raise ValueError("Invalid request size")

            plan = json.loads(self.rfile.read(length))
            rooms = app.clean(plan)
            result = {
                "passed": True,
                "room_count": len(rooms),
                "production_deployment": False
            }
            self.reply(200, result)
        except Exception as exc:
            self.reply(400, {"error": str(exc)})
