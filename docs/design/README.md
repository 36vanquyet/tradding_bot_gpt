# Design Docs

Bộ tài liệu này mô tả thiết kế hiện tại của Trading Bot V5 theo đúng implementation đang có trong source.

## Danh mục

- [architecture.md](architecture.md): tổng quan component, boundary và trách nhiệm từng phần
- [use-cases.md](use-cases.md): actor, use case chính và user-case diagram
- [sequences.md](sequences.md): các sequence diagram quan trọng của hệ thống
- [timing-and-state.md](timing-and-state.md): chu kỳ polling, heartbeat, persistence và đồng bộ state

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
