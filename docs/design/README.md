# Design Docs

Bộ tài liệu này mô tả thiết kế hiện tại của Trading Bot V5 theo đúng implementation đang có trong source.

## Danh mục

- [architecture.md](architecture.md): tổng quan component, boundary và trách nhiệm từng phần
- [use-cases.md](use-cases.md): actor, use case chính và user-case diagram
- [sequences.md](sequences.md): các sequence diagram quan trọng của hệ thống
- [timing-and-state.md](timing-and-state.md): chu kỳ polling, heartbeat, persistence và đồng bộ state

Hiện trạng đáng chú ý:

- Telegram layer đã hỗ trợ manual order cho `spot` và `future`, gồm `market`, `limit`, `cross|isolated`, leverage và quote-notional như `100usdt`
- Dashboard layer đã có chart nến dark-theme với chọn `spot/future`, timeframe tới `1w`, MA line và volume
- Engine có cơ chế suppress lặp lại cho dust positions không thể đóng do nhỏ hơn `min_qty` của sàn

## Phạm vi

Các tài liệu trong thư mục này bám theo implementation hiện tại ở các module:

- `app/main.py`
- `app/core/engine.py`
- `app/core/control_service.py`
- `app/core/state_store.py`
- `app/exchange/factory.py`
- `app/exchange/paper.py`
- `app/telegram/`
- `app/web/dashboard.py`

## Lưu ý

- Đây là design-as-built, không phải target architecture dài hạn.
- Khi code thay đổi ở engine, dashboard, Telegram hoặc persistence thì nên cập nhật lại sơ đồ tương ứng.
