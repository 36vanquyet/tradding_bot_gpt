# REPORT - Trading Bot V5

## 1. Mục tiêu của V5

V5 nâng bot từ bản paper-trading có control Telegram thành một nền tảng gần thực chiến hơn: có đồng bộ trạng thái runtime tốt hơn, hỗ trợ pending orders, trailing stop, dashboard web nội bộ và reset cấu hình runtime.

## 2. Kiến trúc hiện tại

- Strategy layer: `MovingAverageCrossStrategy`
- Risk layer: `FixedFractionalRisk`
- Exchange layer: `PaperExchange` và CCXT adapters
- State store: SQLite
- Telegram control: command + inline keyboard
- Dashboard layer: HTTP server nội bộ
- Protection layer: stop loss, take profit, trailing stop

## 3. Tính năng nổi bật

- hot-swap exchange khi đổi mode hoặc đổi sàn
- chuẩn hóa quantity theo `min_qty`, `step_size`, `min_notional`
- stop loss, take profit và trailing stop do engine quản lý
- quản lý symbol, mode, ngôn ngữ qua Telegram
- reset runtime config bằng `/resetconfig`
- dashboard hiển thị status, positions và pending orders

## 4. Trạng thái kỹ thuật

- `BotState` hiện lưu cả `open_positions`, `pending_orders` và các giá trị mặc định runtime
- Engine đồng bộ positions/open orders từ exchange vào state
- Runtime config và engine state đã được tách luồng persist để tránh ghi đè cấu hình khi restart
- Dashboard cung cấp giao diện HTML và endpoint `/api/status`
- Telegram bot hỗ trợ `vi` và `en`

## 5. Các điểm cần phát triển tiếp

- websocket stream để giảm độ trễ và giảm polling
- đồng bộ sâu hơn với nhiều loại order của từng sàn
- circuit breaker và recovery policy rõ ràng hơn khi exchange lỗi kéo dài
- metrics/observability tốt hơn như Prometheus hoặc structured event stream
- command an toàn hơn cho các thao tác live như confirm trước khi `Close All`

## 6. Kết luận

V5 đã tiến thêm một bước rõ rệt về khả năng vận hành: có dashboard, runtime controls tốt hơn, và state giàu hơn để quan sát bot trong cả paper lẫn live. Phần còn thiếu chủ yếu nằm ở độ cứng vận hành production và monitoring sâu hơn.
