from __future__ import annotations

import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer


def _html() -> str:
    return """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Trading Bot V5 Dashboard</title>
  <style>
    :root { color-scheme: light; --bg:#f4f7fb; --card:#ffffff; --accent:#0f766e; --text:#12202f; --muted:#5b6b7b; }
    body { margin:0; font-family:Segoe UI, sans-serif; background:linear-gradient(180deg,#e8f3f1,#f7fafc); color:var(--text); }
    .wrap { max-width:1100px; margin:0 auto; padding:24px; }
    h1 { margin:0 0 18px; font-size:32px; }
    .grid { display:grid; grid-template-columns:repeat(auto-fit,minmax(220px,1fr)); gap:16px; }
    .card { background:var(--card); border-radius:16px; padding:18px; box-shadow:0 10px 30px rgba(15,118,110,0.08); }
    .label { color:var(--muted); font-size:12px; text-transform:uppercase; letter-spacing:.08em; }
    .value { font-size:24px; font-weight:700; margin-top:8px; }
    .wide { margin-top:16px; }
    pre { white-space:pre-wrap; word-break:break-word; margin:0; font-size:14px; }
    table { width:100%; border-collapse:collapse; }
    th, td { text-align:left; padding:10px 6px; border-bottom:1px solid #e6edf5; font-size:14px; }
  </style>
</head>
<body>
  <div class="wrap">
    <h1>Trading Bot V5 Dashboard</h1>
    <div class="grid" id="cards"></div>
    <div class="card wide">
      <div class="label">Open Positions</div>
      <table id="positions"><thead><tr><th>Symbol</th><th>Qty</th><th>Entry</th><th>SL</th><th>TP</th><th>Trail</th><th>Source</th></tr></thead><tbody></tbody></table>
    </div>
    <div class="card wide">
      <div class="label">Pending Orders</div>
      <table id="orders"><thead><tr><th>Order ID</th><th>Symbol</th><th>Side</th><th>Type</th><th>Qty</th><th>Price</th><th>Status</th></tr></thead><tbody></tbody></table>
    </div>
    <div class="card wide">
      <div class="label">Raw Status</div>
      <pre id="raw"></pre>
    </div>
  </div>
  <script>
    async function refresh() {
      const res = await fetch('/api/status');
      const data = await res.json();
      const cards = [
        ['Mode', data.mode],
        ['Exchange', data.exchange],
        ['Language', data.language],
        ['Balance', Number(data.balance_quote || 0).toFixed(2) + ' USDT'],
        ['Daily PnL', Number(data.daily_pnl || 0).toFixed(2)],
        ['Signal', data.last_signal || 'NONE'],
        ['Trade', data.last_trade || 'No trade'],
        ['Error', data.last_error || 'None'],
      ];
      document.getElementById('cards').innerHTML = cards.map(([k,v]) => `<div class="card"><div class="label">${k}</div><div class="value">${v}</div></div>`).join('');
      document.querySelector('#positions tbody').innerHTML = (data.positions || []).map(p => `<tr><td>${p.symbol}</td><td>${p.quantity}</td><td>${p.entry_price}</td><td>${p.stop_loss ?? ''}</td><td>${p.take_profit ?? ''}</td><td>${p.trailing_stop_pct ?? ''}</td><td>${p.source ?? ''}</td></tr>`).join('');
      document.querySelector('#orders tbody').innerHTML = (data.pending_orders_detail || []).map(o => `<tr><td>${o.order_id}</td><td>${o.symbol}</td><td>${o.side}</td><td>${o.order_type}</td><td>${o.quantity}</td><td>${o.price}</td><td>${o.status}</td></tr>`).join('');
      document.getElementById('raw').textContent = JSON.stringify(data, null, 2);
    }
    refresh();
    setInterval(refresh, 3000);
  </script>
</body>
</html>"""


def build_dashboard_server(control_service, host: str, port: int) -> ThreadingHTTPServer:
    class DashboardHandler(BaseHTTPRequestHandler):
        def _send_json(self, payload: dict) -> None:
            body = json.dumps(payload).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def _send_html(self, body: str) -> None:
            data = body.encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

        def do_GET(self) -> None:  # noqa: N802
            if self.path == "/api/status":
                status = control_service.get_status()
                payload = {
                    **status,
                    "positions": [vars(pos) for pos in control_service.state.open_positions.values()],
                    "pending_orders_detail": [vars(order) for order in control_service.state.pending_orders.values()],
                }
                self._send_json(payload)
                return
            if self.path in {"/", "/index.html"}:
                self._send_html(_html())
                return
            self.send_response(404)
            self.end_headers()

        def log_message(self, format: str, *args) -> None:  # noqa: A003
            return

    return ThreadingHTTPServer((host, port), DashboardHandler)


def start_dashboard(control_service, host: str, port: int) -> ThreadingHTTPServer:
    server = build_dashboard_server(control_service, host, port)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server
