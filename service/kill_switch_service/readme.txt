The Kill-Switch Service is a critical component of the trading pipeline that ensures trade signals are validated before execution. It acts as a safeguard by enforcing cooldown periods, risk limits, and optional volume-based checks to prevent overtrading or exceeding exposure limits.

The service consumes trade signals from a Kafka topic, evaluates them, and decides whether to approve or block each trade.

Features

Signal Consumption: Reads trade signals (BUY/SELL) from Kafka topics.

Cooldown Enforcement: Prevents rapid successive trades for the same symbol.

Risk Validation: Optionally checks position limits to ensure safe exposure.

Volume Checks: Can be extended to consider recent market volume.

Trade Decision: Emits approved or blocked trade messages.

Detailed Logging: Logs each trade signal, the decision, and the reason for blocking (cooldown/risk).

Configuration

Kafka broker: Ensure bootstrap_servers='kafka:9092' matches your Docker Compose setup.

Cooldown period: Configurable inside main.py (default: 2–3 seconds for testing).

Risk checks & volume logic: Can be extended inside check_risk() function.