import pytest

from app.schemas import parse_book_ticker


def test_parse_book_ticker_success():
    payload = {
        "s": "BTCUSDT",
        "b": "62000.10",
        "B": "0.5",
        "a": "62000.30",
        "A": "0.8",
        "E": 1710000000000,
    }

    event = parse_book_ticker(payload)

    assert event.symbol == "BTCUSDT"
    assert event.bid == 62000.10
    assert event.ask == 62000.30
    assert event.bid_qty == 0.5
    assert event.ask_qty == 0.8
    assert event.mid == (62000.10 + 62000.30) / 2
    assert event.event_time == 1710000000000


def test_parse_book_ticker_invalid_bid_ask():
    payload = {
        "s": "BTCUSDT",
        "b": "62001.00",
        "B": "0.5",
        "a": "62000.00",
        "A": "0.8",
    }

    with pytest.raises(ValueError):
        parse_book_ticker(payload)