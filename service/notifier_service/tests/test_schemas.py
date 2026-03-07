import pytest

from app.schemas import (
    parse_execution_result,
    parse_blocked_order,
    ExecutionResult,
    BlockedOrder,
)


def _make_execution_payload(**overrides):
    base = {
        "order_id": "order-001",
        "symbol": "BTCUSDT",
        "side": "BUY",
        "quantity": 0.001,
        "fill_price": 68000.0,
        "status": "FILLED",
        "timestamp": 1700000000.0,
        "event_type": "execution_result",
    }
    base.update(overrides)
    return base


def _make_blocked_payload(**overrides):
    base = {
        "order_id": "order-002",
        "symbol": "BTCUSDT",
        "side": "SELL",
        "quantity": 0.001,
        "reason": "position_limit_exceeded",
        "timestamp": 1700000000.0,
        "event_type": "blocked_order",
    }
    base.update(overrides)
    return base


# --- ExecutionResult parsing ---

def test_parse_execution_result_valid():
    result = parse_execution_result(_make_execution_payload())
    assert isinstance(result, ExecutionResult)
    assert result.order_id == "order-001"
    assert result.symbol == "BTCUSDT"
    assert result.side == "BUY"
    assert result.quantity == 0.001
    assert result.fill_price == 68000.0
    assert result.status == "FILLED"


def test_parse_execution_result_sell():
    result = parse_execution_result(_make_execution_payload(side="SELL"))
    assert result.side == "SELL"


def test_parse_execution_result_invalid_side():
    with pytest.raises(ValueError, match="Invalid side"):
        parse_execution_result(_make_execution_payload(side="SHORT"))


def test_parse_execution_result_zero_quantity():
    with pytest.raises(ValueError, match="positive"):
        parse_execution_result(_make_execution_payload(quantity=0))


def test_parse_execution_result_negative_price():
    with pytest.raises(ValueError, match="positive"):
        parse_execution_result(_make_execution_payload(fill_price=-1))


def test_parse_execution_result_missing_field():
    payload = _make_execution_payload()
    del payload["order_id"]
    with pytest.raises(KeyError):
        parse_execution_result(payload)


# --- BlockedOrder parsing ---

def test_parse_blocked_order_valid():
    result = parse_blocked_order(_make_blocked_payload())
    assert isinstance(result, BlockedOrder)
    assert result.order_id == "order-002"
    assert result.symbol == "BTCUSDT"
    assert result.side == "SELL"
    assert result.quantity == 0.001
    assert result.reason == "position_limit_exceeded"


def test_parse_blocked_order_invalid_side():
    with pytest.raises(ValueError, match="Invalid side"):
        parse_blocked_order(_make_blocked_payload(side="LONG"))


def test_parse_blocked_order_zero_quantity():
    with pytest.raises(ValueError, match="positive"):
        parse_blocked_order(_make_blocked_payload(quantity=0))


def test_parse_blocked_order_missing_field():
    payload = _make_blocked_payload()
    del payload["reason"]
    with pytest.raises(KeyError):
        parse_blocked_order(payload)


# --- to_dict ---

def test_execution_result_to_dict():
    result = parse_execution_result(_make_execution_payload())
    d = result.to_dict()
    assert d["order_id"] == "order-001"
    assert d["event_type"] == "execution_result"


def test_blocked_order_to_dict():
    result = parse_blocked_order(_make_blocked_payload())
    d = result.to_dict()
    assert d["reason"] == "position_limit_exceeded"
    assert d["event_type"] == "blocked_order"
