import pytest

from app.schemas import parse_event_log, EventLog


def _make_payload(event_type="market_data", symbol="BTCUSDT", **extra):
    base = {
        "event_type": event_type,
        "symbol": symbol,
    }
    base.update(extra)
    return base


def test_parse_market_data_event():
    payload = _make_payload("market_data", bid=68000, ask=68001, mid=68000.5)
    event = parse_event_log(payload)
    assert isinstance(event, EventLog)
    assert event.event_type == "market_data"
    assert event.symbol == "BTCUSDT"
    assert event.payload == payload
    assert event.received_at > 0


def test_parse_trade_signal_event():
    payload = _make_payload("trade_signal", signal_type="MA_CROSSOVER", side="BUY")
    event = parse_event_log(payload)
    assert event.event_type == "trade_signal"


def test_parse_execution_result_event():
    payload = _make_payload("execution_result", order_id="o1", side="BUY", quantity=0.001)
    event = parse_event_log(payload)
    assert event.event_type == "execution_result"


def test_parse_blocked_order_event():
    payload = _make_payload("blocked_order", reason="cooldown")
    event = parse_event_log(payload)
    assert event.event_type == "blocked_order"


def test_parse_approved_order_event():
    payload = _make_payload("approved_order", order_id="o2")
    event = parse_event_log(payload)
    assert event.event_type == "approved_order"


def test_parse_missing_event_type():
    with pytest.raises(ValueError, match="Missing event_type"):
        parse_event_log({"symbol": "BTCUSDT"})


def test_parse_missing_symbol_raises():
    with pytest.raises(ValueError, match="Missing required field: symbol"):
        parse_event_log({"event_type": "market_data"})


def test_to_dict():
    payload = _make_payload("trade_signal")
    event = parse_event_log(payload)
    d = event.to_dict()
    assert d["event_type"] == "trade_signal"
    assert d["symbol"] == "BTCUSDT"
    assert d["payload"] == payload
