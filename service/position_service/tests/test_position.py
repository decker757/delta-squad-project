from app.position import Position


def test_buy_from_flat():
    p = Position(symbol="BTCUSDT")
    p.apply_fill(side="BUY", qty=0.001, fill_price=68000)
    assert p.net_qty == 0.001
    assert p.avg_entry_price == 68000


def test_buy_adds_to_long():
    p = Position(symbol="BTCUSDT")
    p.apply_fill(side="BUY", qty=0.001, fill_price=68000)
    p.apply_fill(side="BUY", qty=0.001, fill_price=70000)
    assert p.net_qty == 0.002
    assert p.avg_entry_price == 69000.0


def test_sell_closes_long_realized_pnl():
    p = Position(symbol="BTCUSDT")
    p.apply_fill(side="BUY", qty=0.001, fill_price=68000)
    realized = p.apply_fill(side="SELL", qty=0.001, fill_price=70000)
    assert p.net_qty == 0.0
    assert p.avg_entry_price == 0.0
    assert realized == (70000 - 68000) * 0.001
    assert p.realized_pnl == realized


def test_sell_partially_closes_long():
    p = Position(symbol="BTCUSDT")
    p.apply_fill(side="BUY", qty=0.002, fill_price=68000)
    realized = p.apply_fill(side="SELL", qty=0.001, fill_price=70000)
    assert p.net_qty == 0.001
    assert p.avg_entry_price == 68000
    assert realized == (70000 - 68000) * 0.001


def test_buy_returns_zero_realized():
    p = Position(symbol="BTCUSDT")
    realized = p.apply_fill(side="BUY", qty=0.001, fill_price=68000)
    assert realized == 0.0


def test_unrealized_pnl_long():
    p = Position(symbol="BTCUSDT")
    p.apply_fill(side="BUY", qty=0.001, fill_price=68000)
    assert p.get_unrealized_pnl(current_mid=70000) == (70000 - 68000) * 0.001


def test_unrealized_pnl_flat():
    p = Position(symbol="BTCUSDT")
    assert p.get_unrealized_pnl(current_mid=70000) == 0.0


def test_sell_from_flat_opens_short():
    p = Position(symbol="BTCUSDT")
    p.apply_fill(side="SELL", qty=0.001, fill_price=70000)
    assert p.net_qty == -0.001
    assert p.avg_entry_price == 70000


def test_sell_adds_to_short():
    p = Position(symbol="BTCUSDT")
    p.apply_fill(side="SELL", qty=0.001, fill_price=70000)
    p.apply_fill(side="SELL", qty=0.001, fill_price=68000)
    assert p.net_qty == -0.002
    assert p.avg_entry_price == 69000.0


def test_buy_covers_short_realized_pnl():
    p = Position(symbol="BTCUSDT")
    p.apply_fill(side="SELL", qty=0.001, fill_price=70000)
    realized = p.apply_fill(side="BUY", qty=0.001, fill_price=68000)
    assert p.net_qty == 0.0
    assert p.avg_entry_price == 0.0
    assert realized == (70000 - 68000) * 0.001
    assert p.realized_pnl == realized


def test_buy_partially_covers_short():
    p = Position(symbol="BTCUSDT")
    p.apply_fill(side="SELL", qty=0.002, fill_price=70000)
    realized = p.apply_fill(side="BUY", qty=0.001, fill_price=68000)
    assert p.net_qty == -0.001
    assert p.avg_entry_price == 70000
    assert realized == (70000 - 68000) * 0.001


def test_unrealized_pnl_short():
    p = Position(symbol="BTCUSDT")
    p.apply_fill(side="SELL", qty=0.001, fill_price=70000)
    # price drops — short is profitable
    assert p.get_unrealized_pnl(current_mid=68000) == (68000 - 70000) * (-0.001)
