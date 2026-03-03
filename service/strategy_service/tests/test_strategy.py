import pytest

from app.strategy import MACrossoverStrategy


def test_no_signal_before_window_fills():
    strategy = MACrossoverStrategy(short_window=3, long_window=5)
    for price in [100.0, 101.0, 102.0, 103.0]:
        assert strategy.evaluate(price) is None


def test_no_signal_on_first_full_window():
    # First full window has no previous side to compare against, so no crossover
    strategy = MACrossoverStrategy(short_window=3, long_window=5)
    for price in [100.0, 101.0, 102.0, 103.0]:
        strategy.evaluate(price)
    assert strategy.evaluate(104.0) is None


def test_buy_signal_on_crossover():
    strategy = MACrossoverStrategy(short_window=3, long_window=5)
    # Establish SELL state: descending prices → short MA < long MA
    for price in [105.0, 104.0, 103.0, 102.0, 101.0]:
        strategy.evaluate(price)
    # Feed a spike to flip short MA above long MA
    result = strategy.evaluate(110.0)
    assert result is not None
    assert result.side == "BUY"
    assert result.short_ma > result.long_ma


def test_sell_signal_on_crossover():
    strategy = MACrossoverStrategy(short_window=3, long_window=5)
    # Establish BUY state: ascending prices → short MA > long MA
    for price in [100.0, 101.0, 102.0, 103.0, 104.0]:
        strategy.evaluate(price)
    # Feed a drop to flip short MA below long MA
    result = strategy.evaluate(90.0)
    assert result is not None
    assert result.side == "SELL"
    assert result.short_ma < result.long_ma


def test_no_duplicate_signals():
    strategy = MACrossoverStrategy(short_window=3, long_window=5)
    # Establish and confirm BUY state
    for price in [100.0, 101.0, 102.0, 103.0, 104.0]:
        strategy.evaluate(price)
    # Continue rising — should not re-emit BUY
    assert strategy.evaluate(105.0) is None
    assert strategy.evaluate(106.0) is None


def test_no_signal_when_mas_are_equal():
    strategy = MACrossoverStrategy(short_window=3, long_window=5)
    # All same price → short_ma == long_ma, should never emit
    for price in [100.0, 100.0, 100.0, 100.0, 100.0]:
        assert strategy.evaluate(price) is None


def test_invalid_windows():
    with pytest.raises(ValueError):
        MACrossoverStrategy(short_window=25, long_window=7)
