# Trading Bot V5

Trading bot Python dùng `Telegram`, `CCXT` và dashboard web nội bộ. Bot hỗ trợ `paper mode` để mô phỏng giao dịch và `live mode` để kết nối sàn thật.

## Tính năng chính

- MA crossover strategy mặc định
- Risk sizing theo `RISK_PER_TRADE`
- Chuẩn hóa khối lượng theo `min_qty`, `step_size`, `min_notional`
- Hỗ trợ `paper` và `live`
- Đồng bộ `open_positions` và `pending_orders` vào bot state
- Stop loss, take profit và trailing stop do engine quản lý
- Telegram bot để theo dõi và điều khiển nhanh
- Dashboard web nội bộ để xem trạng thái runtime
- Lưu state bằng SQLite để giữ trạng thái sau restart
- Tách riêng `runtime config` và `engine state` để tránh ghi đè config khi bot đang chạy

## Chế độ chạy

- `paper mode`: dùng `PaperExchange`, không gửi lệnh thật lên sàn. Phù hợp để test chiến lược, risk, stop loss, take profit và trailing stop.
- `live mode`: dùng adapter CCXT để giao dịch thật trên `binance`, `bybit` hoặc `mexc`.
- Nếu `DRY_RUN=true`, bot vẫn dùng `PaperExchange` ngay cả khi mode là `live`.

Khuyến nghị: luôn test ổn định ở `paper mode` trước khi dùng `live mode`.

## Tính năng chatbot Telegram

- Kiểm soát quyền truy cập theo `TELEGRAM_ALLOWED_USER_IDS`
- Xem trạng thái bot qua `/status`
- Kiểm tra heartbeat qua `/health`
- Đổi exchange qua `/exchange`
- Quản lý danh sách symbol qua `/addsymbol`, `/remsymbol`, `/symbols`
- Đổi ngôn ngữ qua `/language` hoặc `/lang`
- Reset runtime config về giá trị mặc định qua `/resetconfig`
- Điều khiển nhanh bằng inline keyboard:
  `Status`, `Health`, `Auto ON/OFF`, `Pause/Resume`, `Mode: Paper/Live`, `Tiếng Việt/English`, `Close All`

Tài liệu chi tiết chatbot: [docs/chatbot-features.md](docs/chatbot-features.md)

## Dashboard

- Bật bằng `DASHBOARD_ENABLED=true`
- Mặc định chạy tại `http://127.0.0.1:8080`
- Trang dashboard: `http://127.0.0.1:8080/`
- JSON status: `http://127.0.0.1:8080/api/status`

Dashboard hiển thị:

- Mode, exchange, language
- Balance, daily PnL
- Last signal, last trade, last error
- Open positions
- Pending orders
- Raw status JSON

## Cài đặt

```bash
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
```

## Cấu hình `.env`

Ví dụ cấu hình tối thiểu để chạy an toàn ở chế độ mô phỏng:

```env
DRY_RUN=true
DEFAULT_EXCHANGE=binance
DEFAULT_SYMBOLS=BTC/USDT,ETH/USDT
TELEGRAM_BOT_TOKEN=
TELEGRAM_ALLOWED_USER_IDS=123456789
DASHBOARD_ENABLED=true
```

Biến môi trường đáng chú ý:

- `DRY_RUN`: ép bot chạy qua `PaperExchange`
- `DEFAULT_EXCHANGE`: `paper`, `binance`, `bybit`, `mexc`
- `DEFAULT_SYMBOLS`: danh sách symbol, ngăn cách bằng dấu phẩy
- `FAST_MA`, `SLOW_MA`: tham số strategy
- `RISK_PER_TRADE`: phần vốn rủi ro cho mỗi lệnh
- `STOP_LOSS_PCT`, `TAKE_PROFIT_PCT`, `TRAILING_STOP_PCT`: tham số bảo vệ vị thế
- `ENTRY_ORDER_TYPE`: `market` hoặc `limit`
- `LIMIT_PRICE_OFFSET_PCT`: độ lệch giá limit buy so với giá hiện tại
- `POLL_INTERVAL_SECONDS`: chu kỳ engine
- `API_RETRY_ATTEMPTS`, `API_RETRY_DELAY_SECONDS`: retry cho lời gọi API
- `DASHBOARD_ENABLED`, `DASHBOARD_HOST`, `DASHBOARD_PORT`: cấu hình dashboard
- `TELEGRAM_BOT_TOKEN`, `TELEGRAM_ALLOWED_USER_IDS`, `TELEGRAM_CHAT_ID`: cấu hình Telegram
- `BINANCE_*`, `BYBIT_*`, `MEXC_*`: API key/secret và testnet theo từng sàn

Biến mẫu đầy đủ nằm ở [`.env.example`](.env.example).

## Cách chạy

Chạy test:

```bash
pytest -q
```

Chạy sample:

```bash
python run_sample.py
```

Chạy app chính:

```bash
python -m app.main
```

## Telegram commands

- `/start`
- `/help`
- `/status`
- `/health`
- `/symbols`
- `/exchange <paper|binance|bybit|mexc>`
- `/addsymbol BTC/USDT`
- `/remsymbol BTC/USDT`
- `/language <vi|en>`
- `/lang <vi|en>`
- `/resetconfig`

## `/status` hiển thị gì

- `bot_running`
- `auto_trading`
- `mode`
- `exchange`
- `language`
- `symbols`
- `balance_quote`
- `open_positions`
- `daily_pnl`
- `last_signal`
- `last_trade`
- `last_error`

## Kiến trúc ngắn gọn

- `app/main.py`: khởi động settings, state store, engine, Telegram bot và dashboard
- `app/core/engine.py`: vòng lặp giao dịch chính
- `app/exchange/`: paper exchange và CCXT adapters
- `app/strategy/ma_cross.py`: strategy mặc định
- `app/telegram/`: handlers, keyboard, notifier
- `app/web/dashboard.py`: dashboard HTTP nội bộ

## Tài liệu

- [docs/README.md](docs/README.md)
- [docs/chatbot-features.md](docs/chatbot-features.md)
- [docs/release-notes/v5.0.0.md](docs/release-notes/v5.0.0.md)

## Ghi chú vận hành

- Dùng API key chỉ có quyền trade, không cấp quyền rút tiền
- Test trên testnet trước khi bật `live mode`
- Trailing stop hiện do bot quản lý ở tầng ứng dụng, không phải native trailing order của sàn
- Nếu không cấu hình `TELEGRAM_BOT_TOKEN`, engine vẫn chạy nhưng không có chatbot Telegram
- `exchange`, `mode`, `language`, `symbols`, `bot_running`, `auto_trading` được lưu riêng dưới dạng runtime config nên sẽ được giữ lại sau restart
