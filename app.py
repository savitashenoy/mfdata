"""Mutual Fund Analysis Dashboard - Flask backend.

The frontend never calls api.mfapi.in, mfdata.in, or third-party CORS proxies
from the browser. Flask acts as the single proxy layer for all external mutual
fund API requests, which makes the app suitable for Vercel/Render deployment
and avoids browser CORS failures.
"""
from __future__ import annotations

import os
import re
from typing import Any

import requests
from flask import Flask, Response, jsonify, render_template, request

MFAPI_UPSTREAM = "https://api.mfapi.in"
MFDATA_UPSTREAM = "https://mfdata.in"
TIMEOUT = int(os.environ.get("UPSTREAM_TIMEOUT", "20"))
CACHE_SECONDS = int(os.environ.get("CACHE_SECONDS", "300"))

app = Flask(__name__, template_folder="templates", static_folder="static")

_session = requests.Session()
_session.headers.update(
    {
        "User-Agent": "MF-Analysis-Dashboard/1.0 (+Flask proxy)",
        "Accept": "application/json,text/plain,*/*",
    }
)


def _json_error(message: str, status: int, **extra: Any):
    payload = {"error": message}
    payload.update(extra)
    return jsonify(payload), status


def _proxy_get(base_url: str, path: str, params: dict[str, Any] | None = None) -> Response:
    """Fetch an upstream URL and return it as a Flask response with cache headers."""
    path = path.lstrip("/")
    url = f"{base_url}/{path}"
    try:
        upstream = _session.get(url, params=params, timeout=TIMEOUT)
    except requests.Timeout:
        return _json_error("upstream_timeout", 504, upstream=url)
    except requests.RequestException as exc:
        return _json_error("upstream_unreachable", 502, detail=str(exc), upstream=url)

    content_type = upstream.headers.get("Content-Type", "application/json")
    response = Response(upstream.content, status=upstream.status_code, content_type=content_type)
    response.headers["Cache-Control"] = f"public, max-age={CACHE_SECONDS}"
    response.headers["X-Backend-Proxy"] = "flask"
    return response


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/healthz")
def healthz():
    return {"ok": True, "proxy": "flask", "mfapi": MFAPI_UPSTREAM, "mfdata": MFDATA_UPSTREAM}


@app.route("/api/mf/search")
def mf_search():
    q = request.args.get("q", "").strip()
    if not q:
        return jsonify([])
    return _proxy_get(MFAPI_UPSTREAM, "mf/search", {"q": q})


@app.route("/api/mf/<scheme_code>")
def mf_scheme(scheme_code: str):
    if not scheme_code.isdigit():
        return _json_error("invalid_scheme_code", 400)
    return _proxy_get(MFAPI_UPSTREAM, f"mf/{scheme_code}")


@app.route("/api/mf/<scheme_code>/latest")
def mf_latest(scheme_code: str):
    if not scheme_code.isdigit():
        return _json_error("invalid_scheme_code", 400)
    return _proxy_get(MFAPI_UPSTREAM, f"mf/{scheme_code}/latest")


@app.route("/api/mfdata/<path:mfdata_path>")
def mfdata_proxy(mfdata_path: str):
    # Basic path guard: allow normal endpoint paths only, no URL smuggling.
    if not mfdata_path or re.search(r"(^|/)\.\.(/|$)|^https?:", mfdata_path, re.I):
        return _json_error("invalid_mfdata_path", 400)
    return _proxy_get(MFDATA_UPSTREAM, mfdata_path, dict(request.args))


@app.errorhandler(404)
def not_found(_):
    # Vercel sometimes probes paths directly. Keep API errors JSON; otherwise show app.
    if request.path.startswith("/api/"):
        return _json_error("not_found", 404)
    return render_template("index.html"), 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=True)
