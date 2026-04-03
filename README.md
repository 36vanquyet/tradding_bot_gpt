# Trading Bot V5

Trading bot Python dùng `Telegram`, `CCXT` và dashboard web nội bộ. Bot hỗ trợ `paper mode` để mô phỏng và `live mode` để kết nối sàn thật.

## Tính năng chính

- Đồng bộ position thật và open orders từ sàn qua CCXT
- Market order và limit order cho lệnh vào
- Stop loss, take profit và trailing stop do engine quản lý
- Retry khi gặp lỗi API tạm thời
- Telegram bot để theo dõi và điều khiển nhanh
- Dashboard web nội bộ để xem trạng thái bot
- Hỗ trợ 2 ngôn ngữ chatbot: `vi`, `en`

## Tính năng chatbot

- Kiểm soát quyền truy cập theo `TELEGRAM_ALLOWED_USER_IDS`
- Xem trạng thái bot qua `/status`
- Kiểm tra heartbeat qua `/health`
- Đổi exchange qua `/exchange`
- Quản lý danh sách symbol qua `/addsymbol`, `/remsymbol`, `/symbols`
- Đổi ngôn ngữ qua `/language` hoặc `/lang`
- Điều khiển nhanh bằng inline keyboard:
  `Status`, `Health`, `Auto ON/OFF`, `Pause/Resume`, `Mode: Paper/Live`, `Tiếng Việt/English`, `Close All`

Tài liệu chi tiết chatbot: [docs/chatbot-features.md](docs/chatbot-features.md)

## Chế độ chạy

- `paper mode`: dùng `PaperExchange`, không gửi lệnh thật lên sàn
- `live mode`: dùng adapter CCXT để giao dịch thật
- Nếu `DRY_RUN=true`, bot vẫn dùng `PaperExchange` ngay cả khi chọn `live`

Khuyến nghị: luôn test ổn định ở `paper mode` trước khi dùng `live mode`.

## Cài đặt

```bash
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
```

## Cấu hình đáng chú ý

```env
DRY_RUN=true
DEFAULT_EXCHANGE=binance
DEFAULT_SYMBOLS=BTC/USDT,ETH/USDT
ENTRY_ORDER_TYPE=market
TRAILING_STOP_PCT=0.01
API_RETRY_ATTEMPTS=3
API_RETRY_DELAY_SECONDS=1.0
DASHBOARD_ENABLED=true
DASHBOARD_HOST=127.0.0.1
DASHBOARD_PORT=8080
```

Biến môi trường mẫu đầy đủ nằm ở [`.env.example`](.env.example).

## Chạy test

```bash
pytest -q
```

## Chạy sample

```bash
python run_sample.py
```

## Chạy app chính

```bash
python -m app.main
```

## Dashboard

- Mặc định chạy tại `http://127.0.0.1:8080`
- JSON status tại `http://127.0.0.1:8080/api/status`
- Có thể tắt bằng `DASHBOARD_ENABLED=false`

## Tài liệu

- [docs/README.md](docs/README.md)
- [docs/chatbot-features.md](docs/chatbot-features.md)
- [docs/release-notes/v5.0.0.md](docs/release-notes/v5.0.0.md)

## Ghi chú vận hành

- Dùng API key chỉ có quyền trade, không cấp quyền rút tiền
- Test trên testnet trước khi bật `live mode`
- Trailing stop hiện do bot quản lý ở tầng ứng dụng, không phải native trailing order của sàn
