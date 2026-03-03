import pytest

from app.schemas import parse_market_data_event


VALID_PAYLOAD = {
    "symbol": "BTCUSDT",
    "bid": 68016.25,
    "ask": 68016.26,
    "bid_qty": 0.5,
    "ask_qty": 0.8,
    "mid": 68016.255,
    "event_time": 1710000000000,
    "source": "binance",
    "event_type": "market_data",
}


def test_parse_valid_payload():
    event = parse_market_data_event(VALID_PAYLOAD)
    assert event.symbol == "BTCUSDT"
    assert event.bid == 68016.25
    assert event.ask == 68016.26
    assert event.mid == 68016.255
    assert event.event_time == 1710000000000


def test_rejects_non_positive_mid():
    payload = {**VALID_PAYLOAD, "mid": 0.0}
    with pytest.raises(ValueError):
        parse_market_data_event(payload)


def test_rejects_non_positive_bid():
    payload = {**VALID_PAYLOAD, "bid": -1.0}
    with pytest.raises(ValueError):
        parse_market_data_event(payload)


def test_rejects_bid_greater_than_ask():
    payload = {**VALID_PAYLOAD, "bid": 68016.26, "ask": 68016.25}
    with pytest.raises(ValueError):
        parse_market_data_event(payload)


def test_missing_required_field():
    payload = {k: v for k, v in VALID_PAYLOAD.items() if k != "bid"}
    with pytest.raises(KeyError):
        parse_market_data_event(payload)
