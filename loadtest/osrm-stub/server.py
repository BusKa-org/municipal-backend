"""
Minimal OSRM-compatible stub server for load testing.

BusKá's routing_service.py proxies exactly one OSRM endpoint:

    GET /route/v1/driving/{lng1},{lat1};{lng2},{lat2}?overview=full&geometries=geojson

This stub implements just that shape, returning a synthetic (straight-line,
lightly-jittered) polyline instead of a real driving route. It exists so load
tests never send traffic to the public router.project-osrm.org demo server
(which is rate-limited and whose ToS this would violate at load-test volumes).

Not a routing engine — the geometry is not a real street path. Good enough
for load testing because BusKá's own code only consumes distance/duration
numbers and a coordinate list; it never validates that the polyline follows
real roads.

Configurable via env vars:
  STUB_LATENCY_MS      base artificial latency per request (default 40)
  STUB_LATENCY_JITTER_MS  +/- random jitter added to the base (default 30)
  STUB_ERROR_RATE       fraction of requests (0..1) that return a synthetic
                        503, to let error-handling paths be exercised
                        (default 0)
  PORT                  listen port (default 5001)
"""

from __future__ import annotations

import json
import math
import os
import random
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, unquote

LATENCY_MS = float(os.getenv("STUB_LATENCY_MS", "40"))
LATENCY_JITTER_MS = float(os.getenv("STUB_LATENCY_JITTER_MS", "30"))
ERROR_RATE = float(os.getenv("STUB_ERROR_RATE", "0"))
PORT = int(os.getenv("PORT", "5001"))

EARTH_RADIUS_M = 6_371_000
AVG_SPEED_MPS = 8.33  # ~30 km/h, realistic urban/school-route average


def _haversine_m(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lng2 - lng1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    return 2 * EARTH_RADIUS_M * math.asin(math.sqrt(a))


def _interpolated_route(lng1: float, lat1: float, lng2: float, lat2: float, steps: int = 16):
    coords = []
    for i in range(steps + 1):
        t = i / steps
        lat = lat1 + (lat2 - lat1) * t
        lng = lng1 + (lng2 - lng1) * t
        if 0 < i < steps:
            jitter = 0.0006  # ~60m, just enough to not be a perfectly straight line
            lat += random.uniform(-jitter, jitter)
            lng += random.uniform(-jitter, jitter)
        coords.append([lng, lat])
    return coords


class Handler(BaseHTTPRequestHandler):
    server_version = "OSRMStub/1.0"

    def log_message(self, fmt, *args):  # noqa: A002 - keep container logs quiet
        pass

    def _sleep_for_latency(self):
        delay_ms = LATENCY_MS + random.uniform(-LATENCY_JITTER_MS, LATENCY_JITTER_MS)
        time.sleep(max(delay_ms, 0) / 1000)

    def _send_json(self, status: int, payload: dict):
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):  # noqa: N802 - stdlib method name
        # NOTE: deliberately not using urllib.parse.urlparse/urlsplit here —
        # they split off a leading ";"-delimited segment into `params`
        # (legacy RFC 2396 behavior), which corrupts OSRM's
        # "{lng1},{lat1};{lng2},{lat2}" coordinate syntax. A plain partition
        # on "?" is all we need since our only two routes have static paths.
        raw_path, _, raw_query = self.path.partition("?")

        if raw_path == "/health":
            self._send_json(200, {"status": "ok"})
            return

        if not raw_path.startswith("/route/v1/driving/"):
            self._send_json(404, {"code": "NotFound", "message": "unknown endpoint"})
            return

        self._sleep_for_latency()

        if ERROR_RATE and random.random() < ERROR_RATE:
            self._send_json(503, {"code": "ServiceUnavailable", "message": "stub-injected error"})
            return

        coords_segment = unquote(raw_path[len("/route/v1/driving/") :])
        try:
            origin_str, dest_str = coords_segment.split(";")
            lng1, lat1 = (float(x) for x in origin_str.split(","))
            lng2, lat2 = (float(x) for x in dest_str.split(","))
        except (ValueError, IndexError):
            self._send_json(400, {"code": "InvalidInput", "message": "bad coordinates"})
            return

        _ = parse_qs(raw_query)  # overview/geometries accepted but not branched on

        distance_m = _haversine_m(lat1, lng1, lat2, lng2)
        duration_s = distance_m / AVG_SPEED_MPS
        coordinates = _interpolated_route(lng1, lat1, lng2, lat2)

        self._send_json(
            200,
            {
                "code": "Ok",
                "routes": [
                    {
                        "geometry": {"type": "LineString", "coordinates": coordinates},
                        "distance": round(distance_m, 1),
                        "duration": round(duration_s, 1),
                        "weight": round(duration_s, 1),
                        "weight_name": "routability",
                    }
                ],
                "waypoints": [
                    {"location": [lng1, lat1], "name": ""},
                    {"location": [lng2, lat2], "name": ""},
                ],
            },
        )


def main():
    server = ThreadingHTTPServer(("0.0.0.0", PORT), Handler)
    print(
        f"OSRM stub listening on :{PORT} (latency={LATENCY_MS}ms +/-{LATENCY_JITTER_MS}ms, error_rate={ERROR_RATE})"
    )
    server.serve_forever()


if __name__ == "__main__":
    main()
