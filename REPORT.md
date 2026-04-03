# REPORT - Trading Bot V4

## 1. Mục tiêu của V4
Bản V4 mở rộng bot đa sàn trước đó theo hướng gần production hơn: có rule về precision/min order, quản lý stop loss/take profit, và thêm control Telegram để đổi sàn và symbol trực tiếp.

## 2. Kiến trúc mới
- Strategy layer: MA crossover
- Risk layer: fixed fractional + normalize quantity theo `step_size`
- Exchange layer: paper + CCXT adapters
- State store: SQLite
- Telegram control: command + inline keyboard
- Protection layer: kiểm tra stop loss / take profit trước khi xử lý tín hiệu mới

## 3. Tính năng nổi bật
- hot-swap exchange trong runtime
- precision/min qty/min notional checks
- stop loss và take profit trong paper mode
- quản lý danh sách symbol qua Telegram

## 4. Các điểm cần phát triển tiếp
- sync positions thật từ live exchange thay vì cache nội bộ
- websocket stream
- trailing stop
- order retry / reconnect / circuit breaker
- dashboard và Prometheus metrics

## 5. Kết luận
V4 là nền tảng tốt để tiến tới bản live an toàn hơn: đã có lớp risk thực dụng hơn, command điều khiển tốt hơn và khả năng mở rộng tiếp sang bot đa chiến lược.
