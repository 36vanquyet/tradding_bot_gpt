# Sequence Diagrams

## 1. Startup Sequence

```plantuml
@startuml
participant "main.py" as Main
participant Settings
participant SQLiteStateStore as Store
participant ControlService as Control
participant ExchangeFactory as Factory
participant TradingEngine as Engine
participant Dashboard
participant TelegramApp as Tg

Main -> Settings: load_settings()
Main -> Store: create(db_path)
Main -> Store: load_state(initial_state)
Store --> Main: BotState
Main -> Control: create(state, store)
Control -> Store: save_state(initial)
Main -> Factory: build_exchange(mode, exchange)
Factory --> Main: ExchangeAdapter
Main -> Engine: create(settings, control, exchange, strategy, risk)
opt dashboard enabled
  Main -> Dashboard: start_dashboard(control)
end
opt telegram token configured
  Main -> Tg: build_telegram_app(...)
end
Main -> Engine: start thread(run_forever)
opt telegram enabled
  Main -> Tg: run_polling()
end
@enduml
```

## 2. Trading Polling Sequence

```plantuml
@startuml
participant TradingEngine as Loop
participant ControlService as Control
participant ExchangeAdapter as Exchange
participant "MA Cross" as Strategy
participant "Risk Layer" as Risk
participant SQLiteStateStore as Store
participant TelegramNotifier as Notify

Loop -> Control: get_status()
alt bot paused
  Loop --> Loop: return
else bot running
  Loop -> Control: set_heartbeat()
  Control -> Store: save_engine_state()
  Loop -> Exchange: sync(symbols)
  Loop -> Exchange: fetch_positions()
  Loop -> Exchange: fetch_open_orders()
  Loop -> Control: persist_engine_state()
  Control -> Store: save_engine_state()
  Loop -> Exchange: fetch_balance_quote()
  Loop -> Control: persist_engine_state()
  Control -> Store: save_engine_state()
  Loop -> Loop: protect_positions()
  alt stop loss or take profit hit
    Loop -> Exchange: create_market_sell()
    Loop -> Control: update daily_pnl / last_trade
    Loop -> Notify: send(alert)
  end
  alt auto_trading disabled
    Loop --> Loop: return
  else auto_trading enabled
    loop each symbol
      Loop -> Exchange: fetch_ohlcv(symbol)
      Loop -> Strategy: generate_signal(closes)
      Strategy --> Loop: BUY / SELL / HOLD
      alt BUY and no open position
        Loop -> Exchange: fetch_symbol_rule(symbol)
        Loop -> Risk: sized_quantity(balance, price, rule)
        alt valid quantity
          Loop -> Exchange: create_market_buy() or create_limit_buy()
          Loop -> Notify: send(last_trade)
        end
      else SELL and has open position
        Loop -> Exchange: create_market_sell()
        Loop -> Notify: send(last_trade)
      end
      Loop -> Exchange: sync()
      Loop -> Exchange: fetch_positions()
      Loop -> Exchange: fetch_open_orders()
      Loop -> Control: persist_engine_state()
      Control -> Store: save_engine_state()
    end
  end
end
@enduml
```

## 3. Telegram Control Sequence

```plantuml
@startuml
actor Operator as User
participant "Telegram Handler" as Tg
participant ControlService as Control
participant ExchangeFactory as Factory
participant TradingEngine as Engine
participant SQLiteStateStore as Store

User -> Tg: /exchange bybit
Tg -> Tg: authorize user
Tg -> Factory: build_exchange(settings, mode, "bybit")
Factory --> Tg: ExchangeAdapter
Tg -> Engine: set_exchange(new_exchange)
Tg -> Control: set_exchange("bybit")
Control -> Store: save_runtime_config()
Tg --> User: exchange changed
@enduml
```

## 4. Dashboard Read Sequence

```plantuml
@startuml
participant Browser
participant DashboardHandler as Dash
participant ControlService as Control

Browser -> Dash: GET /api/status
Dash -> Control: get_status()
Dash -> Control: read state.open_positions
Dash -> Control: read state.pending_orders
Dash --> Browser: JSON status payload
note over Browser
  Client refresh mỗi 3 giây
end note
@enduml
```

## 5. Close-All Sequence

```plantuml
@startuml
actor Operator as User
participant "Telegram Button Handler" as Tg
participant ExchangeAdapter as Exchange
participant ControlService as Control

User -> Tg: click "Close All"
Tg -> Tg: authorize user
Tg -> Exchange: close_all()
Exchange --> Tg: list[Trade]
Tg -> Control: update last_trade
Tg -> Control: persist_engine_state()
Tg --> User: confirm closed positions
@enduml
```

## Ghi chú

- `mode` hoặc `exchange` đổi qua Telegram sẽ hot-swap adapter bên trong engine.
- Dashboard là read-only trong version hiện tại.
- Engine loop hiện là polling tuần tự, chưa song song theo symbol.
