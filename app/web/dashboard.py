from __future__ import annotations

import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse


def _symbol_for_market(symbol: str, market_kind: str) -> str:
    market_kind = (market_kind or "spot").lower()
    if market_kind == "future":
        if ":" in symbol or "/" not in symbol:
            return symbol
        base, quote = symbol.split("/", 1)
        return f"{base}/{quote}:{quote}"
    if ":" in symbol and "/" in symbol:
        base_quote, suffix = symbol.split(":", 1)
        _ = suffix
        return base_quote
    return symbol


def _chart_payload(exchange, symbol: str, timeframe: str, market_kind: str = "spot", limit: int = 60) -> dict:
    resolved_symbol = _symbol_for_market(symbol, market_kind)
    candles = exchange.fetch_ohlcv(resolved_symbol, timeframe, limit=limit)
    items = [
        {
            "ts": int(candle[0]),
            "open": float(candle[1]),
            "high": float(candle[2]),
            "low": float(candle[3]),
            "close": float(candle[4]),
            "volume": float(candle[5]) if len(candle) > 5 else 0.0,
        }
        for candle in candles
    ]
    closes = [item["close"] for item in items]
    return {
        "symbol": resolved_symbol,
        "timeframe": timeframe,
        "market_kind": market_kind,
        "candles": items,
        "latest_close": closes[-1] if closes else None,
        "high": max(closes) if closes else None,
        "low": min(closes) if closes else None,
    }


def _html() -> str:
    return """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Trading Bot V5 Dashboard</title>
  <script src="https://cdn.jsdelivr.net/npm/lightweight-charts@4.2.0/dist/lightweight-charts.standalone.production.js"></script>
  <style>
    :root { color-scheme: dark; --bg:#0f1116; --panel:#14161d; --panel-2:#101319; --stroke:#2a2e39; --text:#d4d8e3; --muted:#7d8596; --accent:#f59e0b; --green:#22c55e; --red:#ef4444; --blue:#3b82f6; }
    * { box-sizing:border-box; }
    body { margin:0; font-family:Segoe UI, sans-serif; background:var(--bg); color:var(--text); }
    .wrap { max-width:1400px; margin:0 auto; padding:20px; }
    h1 { margin:0 0 18px; font-size:28px; }
    .grid { display:grid; grid-template-columns:repeat(auto-fit,minmax(220px,1fr)); gap:14px; }
    .card { background:var(--panel); border-radius:14px; padding:16px; border:1px solid var(--stroke); }
    .label { color:var(--muted); font-size:11px; text-transform:uppercase; letter-spacing:.08em; }
    .value { font-size:22px; font-weight:700; margin-top:8px; }
    .wide { margin-top:16px; }
    pre { white-space:pre-wrap; word-break:break-word; margin:0; font-size:13px; }
    table { width:100%; border-collapse:collapse; }
    th, td { text-align:left; padding:10px 6px; border-bottom:1px solid var(--stroke); font-size:13px; color:var(--text); }
    .toolbar { display:flex; justify-content:space-between; align-items:center; gap:12px; margin-bottom:14px; flex-wrap:wrap; }
    .toolbar-group { display:flex; gap:12px; align-items:center; flex-wrap:wrap; }
    .toolbar label { font-size:11px; color:var(--muted); text-transform:uppercase; letter-spacing:.08em; }
    select { border:1px solid var(--stroke); border-radius:10px; padding:8px 10px; background:var(--panel-2); color:var(--text); min-width:120px; }
    .chart-shell { background:#111318; border-radius:16px; padding:12px; border:1px solid var(--stroke); }
    .chart-head { display:flex; justify-content:space-between; align-items:flex-start; gap:16px; margin-bottom:10px; flex-wrap:wrap; }
    .chart-title { display:flex; flex-direction:column; gap:4px; }
    .chart-symbol-line { font-size:15px; font-weight:700; }
    .chart-ohlc { display:flex; gap:14px; flex-wrap:wrap; font-size:13px; color:var(--muted); }
    .chart-ohlc strong { color:var(--text); font-weight:600; }
    .chart-actions { display:flex; align-items:center; gap:10px; }
    .chart-hint { color:var(--muted); font-size:12px; }
    button { border:1px solid var(--stroke); border-radius:10px; padding:8px 12px; background:var(--panel-2); color:var(--text); cursor:pointer; }
    #chart-root { width:100%; height:620px; }
    .legend-row { display:flex; gap:18px; flex-wrap:wrap; margin-top:10px; color:var(--muted); font-size:13px; }
    .legend-dot { display:inline-block; width:10px; height:10px; border-radius:999px; margin-right:6px; }
    .chart-empty { min-height:480px; display:flex; align-items:center; justify-content:center; color:var(--muted); }
  </style>
</head>
<body>
  <div class="wrap">
    <h1>Trading Bot V5 Dashboard</h1>
    <div class="grid" id="cards"></div>
    <div class="card wide">
      <div class="toolbar">
        <div>
          <div class="label">Price Chart</div>
        </div>
        <div class="toolbar-group">
          <label for="chart-market">Market</label>
          <select id="chart-market">
            <option value="spot">Spot</option>
            <option value="future">Future</option>
          </select>
          <label for="chart-symbol">Symbol</label>
          <select id="chart-symbol"></select>
          <label for="chart-timeframe">Timeframe</label>
          <select id="chart-timeframe">
            <option value="1m">1m</option>
            <option value="5m">5m</option>
            <option value="15m">15m</option>
            <option value="1h">1h</option>
            <option value="4h">4h</option>
            <option value="1d">1d</option>
            <option value="1w">1w</option>
          </select>
          <div class="chart-actions">
            <button id="chart-reset" type="button">Reset View</button>
            <span class="chart-hint">TradingView-style zoom and pan are enabled</span>
          </div>
        </div>
      </div>
      <div class="chart-shell">
        <div class="chart-head">
          <div class="chart-title">
            <div id="chart-symbol-line" class="chart-symbol-line">Loading chart...</div>
            <div id="chart-ohlc" class="chart-ohlc"></div>
          </div>
          <div id="chart-legend" class="legend-row"></div>
        </div>
        <div id="chart-root"></div>
      </div>
    </div>
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
    let chartApi = null;
    let candleSeries = null;
    let maSeries = null;
    let volumeSeries = null;
    let currentChartData = null;

    function formatNumber(value) {
      return Number(value || 0).toLocaleString(undefined, { maximumFractionDigits: 4 });
    }

    function formatPrice(value) {
      return Number(value || 0).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 });
    }

    function syncSymbolOptions(symbols) {
      const select = document.getElementById('chart-symbol');
      const current = select.value;
      select.innerHTML = '';
      (symbols || []).forEach(symbol => {
        const option = document.createElement('option');
        option.value = symbol;
        option.textContent = symbol;
        select.appendChild(option);
      });
      if (!select.options.length) {
        return;
      }
      const fallback = (symbols || [])[0];
      select.value = (symbols || []).includes(current) ? current : fallback;
    }

    function ensureChart() {
      const root = document.getElementById('chart-root');
      if (chartApi) {
        return;
      }
      root.innerHTML = '';
      chartApi = LightweightCharts.createChart(root, {
        width: root.clientWidth,
        height: 620,
        layout: {
          background: { color: '#111318' },
          textColor: '#c6cad4',
        },
        grid: {
          vertLines: { color: '#232733' },
          horzLines: { color: '#232733' },
        },
        crosshair: { mode: LightweightCharts.CrosshairMode.Normal },
        timeScale: {
          borderColor: '#2a2e39',
          timeVisible: true,
          secondsVisible: false,
        },
        rightPriceScale: {
          borderColor: '#2a2e39',
        },
      });
      candleSeries = chartApi.addCandlestickSeries({
        upColor: '#22c55e',
        downColor: '#ef4444',
        borderVisible: false,
        wickUpColor: '#22c55e',
        wickDownColor: '#ef4444',
        priceLineVisible: true,
      });
      maSeries = chartApi.addLineSeries({
        color: '#4ade80',
        lineWidth: 1,
        priceLineVisible: false,
      });
      volumeSeries = chartApi.addHistogramSeries({
        color: '#3b82f6',
        priceFormat: { type: 'volume' },
        priceScaleId: '',
      });
      volumeSeries.priceScale().applyOptions({
        scaleMargins: {
          top: 0.78,
          bottom: 0,
        },
      });
      chartApi.subscribeCrosshairMove(param => {
        if (!currentChartData || !currentChartData.candles.length) {
          return;
        }
        const candle = param.time
          ? currentChartData.candleMap.get(param.time) || currentChartData.candles[currentChartData.candles.length - 1]
          : currentChartData.candles[currentChartData.candles.length - 1];
        updateHeader(currentChartData, candle);
      });
      window.addEventListener('resize', () => {
        if (chartApi) {
          chartApi.applyOptions({ width: root.clientWidth });
        }
      });
    }

    function sma(values, period) {
      const result = [];
      let sum = 0;
      for (let i = 0; i < values.length; i += 1) {
        sum += values[i];
        if (i >= period) {
          sum -= values[i - period];
        }
        if (i >= period - 1) {
          result.push(sum / period);
        } else {
          result.push(null);
        }
      }
      return result;
    }

    function volumeSma(volumes, period) {
      return sma(volumes, period);
    }

    function updateHeader(chart, candle) {
      document.getElementById('chart-symbol-line').textContent = chart.symbol + ' · ' + chart.timeframe + ' · ' + chart.market_kind.toUpperCase();
      const change = candle.close - candle.open;
      const pct = candle.open ? (change / candle.open) * 100 : 0;
      const changeColor = change >= 0 ? '#22c55e' : '#ef4444';
      document.getElementById('chart-ohlc').innerHTML = [
        'O <strong>' + formatPrice(candle.open) + '</strong>',
        'H <strong>' + formatPrice(candle.high) + '</strong>',
        'L <strong>' + formatPrice(candle.low) + '</strong>',
        'C <strong>' + formatPrice(candle.close) + '</strong>',
        '<strong style="color:' + changeColor + '">' + formatPrice(change) + ' (' + pct.toFixed(2) + '%)</strong>',
      ].join(' ');
    }

    function renderLegend(chart, maLast, volumeSmaLast) {
      document.getElementById('chart-legend').innerHTML = [
        '<span><span class="legend-dot" style="background:#f59e0b"></span>' + chart.symbol + ', ' + chart.exchange + '</span>',
        '<span><span class="legend-dot" style="background:#4ade80"></span>EMA 100 ' + (maLast ? formatPrice(maLast) : '-') + '</span>',
        '<span><span class="legend-dot" style="background:#3b82f6"></span>Volume SMA 9 ' + (volumeSmaLast ? formatNumber(volumeSmaLast) : '-') + '</span>',
      ].join('');
    }

    function renderChart(chart) {
      const root = document.getElementById('chart-root');
      if (!chart || !(chart.candles || []).length) {
        root.className = 'chart-empty';
        root.textContent = chart && chart.error ? chart.error : 'No chart data';
        document.getElementById('chart-symbol-line').textContent = 'No chart data';
        document.getElementById('chart-ohlc').innerHTML = '';
        document.getElementById('chart-legend').innerHTML = '';
        return;
      }
      root.className = '';
      ensureChart();

      const candles = chart.candles.map(item => ({
        time: Math.floor(item.ts / 1000),
        open: Number(item.open),
        high: Number(item.high),
        low: Number(item.low),
        close: Number(item.close),
      }));
      const volumes = chart.candles.map(item => Number(item.volume || 0));
      const ema100 = sma(candles.map(item => item.close), 100).map((value, index) => (
        value == null ? null : { time: candles[index].time, value: value }
      )).filter(Boolean);
      const volumeSma9 = volumeSma(volumes, 9);
      const volumeData = chart.candles.map((item, index) => ({
        time: Math.floor(item.ts / 1000),
        value: Number(item.volume || 0),
        color: Number(item.close) >= Number(item.open) ? 'rgba(34,197,94,0.45)' : 'rgba(239,68,68,0.45)',
      }));

      candleSeries.setData(candles);
      maSeries.setData(ema100);
      volumeSeries.setData(volumeData);
      chartApi.timeScale().fitContent();

      const candleMap = new Map(candles.map((item, index) => [item.time, {
        open: item.open,
        high: item.high,
        low: item.low,
        close: item.close,
        volume: volumes[index],
      }]));
      currentChartData = {
        candles,
        candleMap,
      };
      updateHeader(chart, currentChartData.candles[currentChartData.candles.length - 1]);
      renderLegend(chart, ema100.length ? ema100[ema100.length - 1].value : null, volumeSma9.length ? volumeSma9[volumeSma9.length - 1] : null);
    }

    async function refreshChart() {
      const marketKind = document.getElementById('chart-market').value;
      const select = document.getElementById('chart-symbol');
      const timeframe = document.getElementById('chart-timeframe').value;
      if (!select.value) {
        return;
      }
      const params = new URLSearchParams({
        symbol: select.value,
        timeframe: timeframe,
        market_kind: marketKind,
      });
      const res = await fetch('/api/chart?' + params.toString());
      const data = await res.json();
      data.exchange = latestStatus ? latestStatus.exchange : '-';
      renderChart(data);
    }

    let latestStatus = null;

    async function refresh() {
      const res = await fetch('/api/status');
      const data = await res.json();
      latestStatus = data;
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
      syncSymbolOptions(data.symbols || []);
      document.querySelector('#positions tbody').innerHTML = (data.positions || []).map(p => `<tr><td>${p.symbol}</td><td>${p.quantity}</td><td>${p.entry_price}</td><td>${p.stop_loss ?? ''}</td><td>${p.take_profit ?? ''}</td><td>${p.trailing_stop_pct ?? ''}</td><td>${p.source ?? ''}</td></tr>`).join('');
      document.querySelector('#orders tbody').innerHTML = (data.pending_orders_detail || []).map(o => `<tr><td>${o.order_id}</td><td>${o.symbol}</td><td>${o.side}</td><td>${o.order_type}</td><td>${o.quantity}</td><td>${o.price}</td><td>${o.status}</td></tr>`).join('');
      document.getElementById('raw').textContent = JSON.stringify(data, null, 2);
      await refreshChart();
    }
    document.getElementById('chart-market').addEventListener('change', refreshChart);
    document.getElementById('chart-symbol').addEventListener('change', refreshChart);
    document.getElementById('chart-timeframe').addEventListener('change', refreshChart);
    document.getElementById('chart-reset').addEventListener('click', () => {
      if (chartApi) {
        chartApi.timeScale().fitContent();
      }
    });
    refresh();
    setInterval(refresh, 3000);
  </script>
</body>
</html>"""


def build_dashboard_server(control_service, exchange_getter, timeframe: str, host: str, port: int) -> ThreadingHTTPServer:
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
            parsed = urlparse(self.path)
            if parsed.path == "/api/status":
                status = control_service.get_status()
                payload = {
                    **status,
                    "positions": [vars(pos) for pos in control_service.state.open_positions.values()],
                    "pending_orders_detail": [vars(order) for order in control_service.state.pending_orders.values()],
                }
                self._send_json(payload)
                return
            if parsed.path == "/api/chart":
                query = parse_qs(parsed.query)
                symbol = query.get("symbol", [""])[0]
                timeframe_value = query.get("timeframe", [timeframe])[0]
                market_kind = query.get("market_kind", ["spot"])[0].lower()
                if not symbol:
                    self.send_response(400)
                    self.end_headers()
                    return
                try:
                    payload = _chart_payload(exchange_getter(), symbol, timeframe_value, market_kind=market_kind)
                except Exception as exc:
                    payload = {"symbol": symbol, "timeframe": timeframe_value, "market_kind": market_kind, "candles": [], "error": str(exc)}
                self._send_json(payload)
                return
            if parsed.path in {"/", "/index.html"}:
                self._send_html(_html())
                return
            self.send_response(404)
            self.end_headers()

        def log_message(self, format: str, *args) -> None:  # noqa: A003
            return

    return ThreadingHTTPServer((host, port), DashboardHandler)


def start_dashboard(control_service, exchange_getter, timeframe: str, host: str, port: int) -> ThreadingHTTPServer:
    server = build_dashboard_server(control_service, exchange_getter, timeframe, host, port)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server
