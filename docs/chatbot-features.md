# Chatbot Features

Tài liệu này mô tả các tính năng Telegram chatbot của Trading Bot V5.

## Mục tiêu

Chatbot dùng để:

- xem nhanh trạng thái giao dịch
- điều khiển bot từ xa
- đổi cấu hình vận hành cơ bản mà không cần sửa file
- nhận thông báo trade và lỗi

## Kiểm soát truy cập

- Bot chỉ chấp nhận người dùng có `Telegram user id` nằm trong `TELEGRAM_ALLOWED_USER_IDS`
- Nếu không có quyền, bot trả về thông báo từ chối

## Command hỗ trợ

- `/start`
  Hiện thông báo chào và keyboard thao tác nhanh

- `/help`
  Hiện hướng dẫn sử dụng bot theo ngôn ngữ hiện tại

- `/status`
  Hiện:
  `bot_running`, `auto_trading`, `mode`, `exchange`, `language`, `symbols`, `balance_quote`, `open_positions`, `daily_pnl`, `last_signal`, `last_trade`, `last_error`

- `/health`
  Kiểm tra heartbeat của engine để biết bot còn chạy đúng vòng lặp không

- `/symbols`
  Hiện danh sách symbol đang theo dõi

- `/exchange <paper|binance|bybit|mexc>`
  Đổi exchange hiện tại

- `/addsymbol BTC/USDT`
  Thêm symbol vào watchlist

- `/remsymbol BTC/USDT`
  Xóa symbol khỏi watchlist

- `/language <vi|en>`
  Đổi ngôn ngữ chatbot

- `/lang <vi|en>`
  Alias rút gọn của `/language`

- `/resetconfig`
  Reset các cấu hình runtime về mặc định lúc khởi động bot:
  `bot_running`, `auto_trading`, `mode`, `exchange`, `language`, `symbols`

## Inline keyboard

- `Status`
  Hiện trạng thái bot

- `Health`
  Hiện heartbeat và trạng thái engine

- `Auto ON`
  Bật auto trading

- `Auto OFF`
  Tắt auto trading

- `Pause`
  Tạm dừng bot

- `Resume`
  Tiếp tục bot

- `Mode: Paper`
  Chuyển sang chế độ paper

- `Mode: Live`
  Chuyển sang chế độ live

- `Tiếng Việt`
  Chuyển chatbot sang tiếng Việt

- `English`
  Chuyển chatbot sang tiếng Anh

- `Close All`
  Đóng toàn bộ vị thế hiện tại bằng market order qua adapter đang dùng

## Ý nghĩa `paper` và `live`

- `paper`: bot mô phỏng giao dịch qua `PaperExchange`, không gửi lệnh thật lên sàn
- `live`: bot dùng CCXT adapter để gửi lệnh thật lên sàn đang chọn
- Nếu `DRY_RUN=true`, bot vẫn dùng `PaperExchange` ngay cả khi chuyển sang `live`

## `/status` gồm những gì

Lệnh `/status` đang hiển thị:

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

Lưu ý: danh sách `pending_orders` hiện có trong state và dashboard JSON, nhưng chưa được render trong text của `/status`.

## Đa ngôn ngữ

- Hỗ trợ `vi` và `en`
- Ngôn ngữ hiện tại được lưu trong state của bot
- Sau khi restart bot, ngôn ngữ vẫn được giữ lại

## Persistence của runtime config

- Các thay đổi runtime như `exchange`, `mode`, `language`, `symbols`, `bot_running`, `auto_trading` được persist riêng với engine state
- Mục tiêu là tránh việc vòng lặp engine ghi đè lại config runtime khi bot đang chạy
- Sau restart, bot ưu tiên load lại runtime config đã lưu gần nhất

## Hành vi chống lỗi lặp callback

Khi người dùng bấm lặp cùng một nút như `Resume` nhiều lần liên tiếp, bot không còn văng lỗi `Message is not modified`. Trường hợp text và keyboard không đổi, callback được bỏ qua an toàn.

## Giới hạn hiện tại

- Chatbot hiện chủ yếu phục vụ điều khiển vận hành, chưa hỗ trợ sửa sâu các tham số strategy từ chat
- Dashboard web hiện là read-only, chưa có nút điều khiển từ giao diện web
- `Close All` dùng exchange object hiện tại trong bộ nhớ ứng dụng; sau thao tác, trạng thái chi tiết sẽ được đồng bộ lại ở vòng engine kế tiếp
