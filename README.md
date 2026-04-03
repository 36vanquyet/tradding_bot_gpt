# Trading Bot V4 - Python + Telegram + CCXT

## Điểm mới ở V4
- thêm rule `min_qty`, `step_size`, `min_notional`
- chuẩn hoá khối lượng vào lệnh theo precision của symbol
- thêm stop loss / take profit cho paper mode
- thêm Telegram command để đổi sàn và quản lý symbol trực tiếp
- engine có thể hot-swap exchange khi đổi mode hoặc đổi sàn

## Telegram commands
- `/start`
- `/status`
- `/health`
- `/symbols`
- `/exchange paper`
- `/exchange binance`
- `/addsymbol BTC/USDT`
- `/remsymbol BTC/USDT`

## Cài đặt
```bash
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
```

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

## Ghi chú
- Mặc định vẫn nên chạy `paper` mode.
- Khi chuyển sang `live`, hãy dùng API key chỉ có quyền trade và tắt quyền rút tiền.
- CCXT adapter trong project là khung mở rộng thực tế, nhưng bạn vẫn nên test trên testnet trước.
