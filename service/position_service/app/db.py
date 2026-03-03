import logging

import psycopg2

from .position import Position
from .schemas import ExecutionResult


class PositionDB:
    def __init__(
        self,
        host: str,
        port: int,
        user: str,
        password: str,
        dbname: str,
        logger: logging.Logger,
    ):
        self.logger = logger
        self._conn = psycopg2.connect(
            host=host,
            port=port,
            user=user,
            password=password,
            dbname=dbname,
            sslmode="require",
        )

    def load_position(self, symbol: str) -> Position | None:
        with self._conn.cursor() as cur:
            cur.execute(
                """
                SELECT net_qty, avg_entry_price, realized_pnl, unrealized_pnl
                FROM positions
                WHERE symbol = %s
                """,
                (symbol,),
            )
            row = cur.fetchone()

        if row is None:
            return None

        return Position(
            symbol=symbol,
            net_qty=float(row[0]),
            avg_entry_price=float(row[1]),
            realized_pnl=float(row[2]),
            unrealized_pnl=float(row[3]),
        )

    def upsert_position_and_insert_trade(self, position: Position, fill: ExecutionResult, realized_pnl: float) -> None:
        with self._conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO positions (symbol, net_qty, avg_entry_price, realized_pnl, unrealized_pnl, updated_at)
                VALUES (%s, %s, %s, %s, %s, NOW())
                ON CONFLICT (symbol) DO UPDATE SET
                    net_qty         = EXCLUDED.net_qty,
                    avg_entry_price = EXCLUDED.avg_entry_price,
                    realized_pnl    = EXCLUDED.realized_pnl,
                    unrealized_pnl  = EXCLUDED.unrealized_pnl,
                    updated_at      = NOW()
                """,
                (
                    position.symbol,
                    position.net_qty,
                    position.avg_entry_price,
                    position.realized_pnl,
                    position.unrealized_pnl,
                ),
            )
            cur.execute(
                """
                INSERT INTO trades (order_id, symbol, side, quantity, fill_price, realized_pnl, filled_at)
                VALUES (%s, %s, %s, %s, %s, %s, to_timestamp(%s))
                """,
                (
                    fill.order_id,
                    fill.symbol,
                    fill.side,
                    fill.quantity,
                    fill.fill_price,
                    realized_pnl,
                    fill.timestamp,
                ),
            )
        self._conn.commit()

    def update_unrealized_pnl(self, symbol: str, unrealized_pnl: float) -> None:
        with self._conn.cursor() as cur:
            cur.execute(
                """
                UPDATE positions
                SET unrealized_pnl = %s, updated_at = NOW()
                WHERE symbol = %s
                """,
                (unrealized_pnl, symbol),
            )
        self._conn.commit()

    def close(self) -> None:
        self._conn.close()
