#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
여행 계획 도우미 - 실제 항공권 가격 프록시 서버 (Travelpayouts / Aviasales Data API)

- 파이썬 표준 라이브러리만 사용 (외부 패키지 설치 불필요).
- Travelpayouts 토큰은 서버에서만 읽고 브라우저에 절대 노출하지 않는다.
- 브라우저는 이 서버의 /api/... 만 호출하고, 서버가 Travelpayouts로 중계한다.
- 토큰은 같은 폴더의 .env 파일 또는 환경변수에서 읽는다:
      TRAVELPAYOUTS_TOKEN=...
  (토큰 발급: https://www.travelpayouts.com 무료 가입 →
   프로필 → API token 섹션 → https://app.travelpayouts.com/profile/api-token )

- 사용 엔드포인트: /aviasales/v3/prices_for_dates
  (출발/도착/날짜로 실제 최저가·항공사·편명·경유수를 반환. Aviasales 사용자 검색 캐시 기반)

실행:
    python server.py           # 기본 127.0.0.1:8777
    python server.py 8888      # 포트 지정
"""
import json
import os
import sys
import urllib.parse
import urllib.request
import urllib.error
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

HERE = os.path.dirname(os.path.abspath(__file__))
TP_BASE = "https://api.travelpayouts.com"

# ---------------------------------------------------------------- .env 로더
def load_env():
    path = os.path.join(HERE, ".env")
    if not os.path.exists(path):
        return
    try:
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                k, v = line.split("=", 1)
                k, v = k.strip(), v.strip().strip('"').strip("'")
                if k and k not in os.environ:
                    os.environ[k] = v
    except Exception as e:
        print("[.env 읽기 경고]", e)

load_env()

def token():
    return os.environ.get("TRAVELPAYOUTS_TOKEN", "").strip()

def keys_configured():
    return bool(token())

# ---------------------------------------------------------------- Travelpayouts 호출
def tp_prices_for_dates(origin, destination, departure_at, return_at, currency, one_way, direct, limit):
    params = {
        "origin": origin,
        "destination": destination,
        "departure_at": departure_at,   # YYYY-MM 또는 YYYY-MM-DD
        "currency": currency,
        "one_way": "true" if one_way else "false",
        "direct": "true" if direct else "false",
        "sorting": "price",
        "limit": str(limit),
        "page": "1",
        "token": token(),
    }
    if return_at:
        params["return_at"] = return_at
        params["one_way"] = "false"
    url = TP_BASE + "/aviasales/v3/prices_for_dates?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={"Accept-Encoding": "identity"})
    with urllib.request.urlopen(req, timeout=25) as r:
        return json.loads(r.read().decode())

def simplify(raw):
    out = []
    for t in (raw.get("data") or [])[:12]:
        out.append({
            "price": t.get("price"),
            "currency": raw.get("currency", "").upper(),
            "airline": t.get("airline"),
            "flight_number": t.get("flight_number"),
            "origin": t.get("origin"),
            "destination": t.get("destination"),
            "departure_at": t.get("departure_at"),
            "return_at": t.get("return_at"),
            "transfers": t.get("transfers", 0),
            "duration": t.get("duration"),
            # Aviasales 검색 결과로 이어지는 링크 (실제 예약 페이지)
            "link": ("https://www.aviasales.com" + t.get("link", "")) if t.get("link") else "",
        })
    return out

# ---------------------------------------------------------------- HTTP 핸들러
class Handler(BaseHTTPRequestHandler):
    def _send(self, code, obj=None):
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        if obj is not None:
            self.wfile.write(json.dumps(obj, ensure_ascii=False).encode("utf-8"))

    def log_message(self, *a):
        pass

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        qs = urllib.parse.parse_qs(parsed.query)

        if path == "/api/status":
            return self._send(200, {"keys_configured": keys_configured(),
                                    "provider": "travelpayouts"})

        if path == "/api/flights":
            if not keys_configured():
                return self._send(200, {"keys_configured": False,
                                        "error": "토큰 미설정", "flights": []})
            try:
                origin = (qs.get("origin", ["ICN"])[0]).upper()
                dest = (qs.get("dest", [""])[0]).upper()
                dep = qs.get("departureDate", [""])[0]      # YYYY-MM-DD 또는 YYYY-MM
                ret = qs.get("returnDate", [""])[0]
                cur = qs.get("currency", ["krw"])[0].lower()
                one_way = qs.get("oneWay", ["true"])[0] == "true"
                direct = qs.get("nonStop", [""])[0] == "true"
                raw = tp_prices_for_dates(origin, dest, dep, ret, cur,
                                          one_way and not ret, direct, 12)
                if not raw.get("success", True):
                    return self._send(200, {"keys_configured": True,
                                            "error": raw.get("error") or "조회 실패",
                                            "flights": []})
                return self._send(200, {"keys_configured": True,
                                        "flights": simplify(raw)})
            except urllib.error.HTTPError as e:
                body = e.read().decode(errors="replace")
                return self._send(200, {"keys_configured": True,
                                        "error": "Travelpayouts 오류 %s" % e.code,
                                        "detail": body[:400], "flights": []})
            except Exception as e:
                return self._send(200, {"keys_configured": True,
                                        "error": str(e), "flights": []})

        # 정적 파일
        rel = path.lstrip("/") or "index.html"
        safe = os.path.normpath(os.path.join(HERE, rel))
        if not safe.startswith(HERE) or not os.path.isfile(safe):
            return self._send(404, {"error": "not found"})
        ctype = "text/html"
        if safe.endswith(".js"): ctype = "text/javascript"
        elif safe.endswith(".css"): ctype = "text/css"
        elif not safe.endswith(".html"): ctype = "application/octet-stream"
        with open(safe, "rb") as f:
            data = f.read()
        self.send_response(200)
        self.send_header("Content-Type", ctype + "; charset=utf-8")
        self.end_headers()
        self.wfile.write(data)


def main():
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8777
    srv = ThreadingHTTPServer(("127.0.0.1", port), Handler)
    print("여행 계획 도우미 서버: http://127.0.0.1:%d/" % port)
    print("Travelpayouts 토큰 설정됨:", keys_configured())
    print("종료: Ctrl+C")
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        srv.shutdown()


if __name__ == "__main__":
    main()
