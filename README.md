

An event-driven algorithmic trading pipeline that ingests real-time market data, runs it through a Moving Average Crossover strategy, and executes orders automatically on Binance.

---

## Architecture
![Untitled-2026-03-03-1208 (1)](https://github.com/user-attachments/assets/913a7e30-b47f-4ece-962d-1d5770f5ba94)


Each service communicates exclusively via Kafka topics — no direct service-to-service calls. This means any service can be scaled, restarted, or swapped independently.

### Services

| Service | Consumes | Produces | Description |
|---|---|---|---|
| Market Data | Binance WebSocket | `market_data` | Streams real-time L1 book ticker data |
| Strategy | `market_data` | `trade_signal` | Runs MA Crossover strategy |
| Kill Switch | `trade_signal` | `approved_order`, `blocked_order` | Validates signals against risk rules |
| Execution | `approved_order` | `execution_result` | Places orders on Binance |
| Position | `execution_result` | — | Tracks current position and PnL |
| Trader Logger | all topics | DB | Audit trail of every event |
| Notifier | `execution_result`, `blocked_order` | Telegram | Alerts on fills, blocks, errors |

---

## Setup

### Prerequisites
- Docker + Docker Compose
- Binance API key and secret (for execution)

### Running the pipeline

```bash
# Clone the repo
git clone https://github.com/your-org/delta-squad-project.git
cd delta-squad-project

# Configure environment
cp .env.example .env
# Fill in BINANCE_API_KEY and BINANCE_API_SECRET in .env

# Start everything
cd infra
docker compose up --build
```

### Verifying data flow

Check market data is streaming:
```bash
docker exec -it kafka /opt/kafka/bin/kafka-console-consumer.sh \
  --bootstrap-server localhost:9092 --topic market_data
```

Check trade signals are firing:
```bash
docker exec -it kafka /opt/kafka/bin/kafka-console-consumer.sh \
  --bootstrap-server localhost:9092 --topic trade_signal
```

### Running tests

Each service has its own test suite:
```bash
cd service/market_data_service
python -m pytest tests/ -v

cd service/strategy_service
python -m pytest tests/ -v
```

---

## Strategy

**Moving Average (MA) Crossover**

The strategy maintains a rolling window of mid prices (`(bid + ask) / 2`) and computes two moving averages:

- **Short MA** — average of the last `SHORT_WINDOW` prices (default: 7)
- **Long MA** — average of the last `LONG_WINDOW` prices (default: 25)

Signal logic:
```
short_ma > long_ma  →  BUY   (recent prices trending above longer-term average)
short_ma < long_ma  →  SELL  (recent prices trending below longer-term average)
short_ma == long_ma →  no signal
```

Signals are only emitted on **crossover** — when the relationship between the two MAs flips. This prevents the strategy from re-emitting the same signal on every tick.

The windows are configurable via environment variables (`SHORT_WINDOW`, `LONG_WINDOW`) with no code changes required.

---

## Risk Management

The Kill Switch service runs the following checks on every `trade_signal` before allowing it through:

| Check | Description |
|---|---|
| Kill switch flag | If `KILL_SWITCH_ACTIVE=true`, all signals are blocked immediately |
| Position limit | Blocks if current position exceeds `MAX_POSITION` |
| Cooldown | Blocks if last trade was within `COOLDOWN_SECONDS` |
| Same-side repeat | Blocks if signal matches the current position direction |

Blocked signals are published to `blocked_order` for logging and Telegram notification.

### Emergency stop

To halt all trading instantly without restarting the pipeline:
```bash
# In infra/docker-compose.yml, set:
KILL_SWITCH_ACTIVE: "true"

# Then restart just the kill switch service:
docker compose up -d kill-switch-service
```

---

## Configuration

All services are configured via environment variables in `infra/docker-compose.yml`.

| Variable | Service | Default | Description |
|---|---|---|---|
| `SYMBOL` | market-data, strategy | `BTCUSDT` | Trading pair |
| `SHORT_WINDOW` | strategy | `7` | Short MA window |
| `LONG_WINDOW` | strategy | `25` | Long MA window |
| `KILL_SWITCH_ACTIVE` | kill-switch | `false` | Emergency stop flag |
| `MAX_POSITION` | kill-switch | `0.01` | Max BTC position size |
| `COOLDOWN_SECONDS` | kill-switch | `60` | Min seconds between trades |
| `BINANCE_API_KEY` | execution | — | Binance API key |
| `BINANCE_API_SECRET` | execution | — | Binance API secret |
