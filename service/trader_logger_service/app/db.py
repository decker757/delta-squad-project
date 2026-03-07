import json
import logging

import psycopg2

from .schemas import EventLog


class LoggerDB:
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

    def insert_event(self, event: EventLog) -> None:
        with self._conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO event_log (event_type, symbol, payload, received_at)
                VALUES (%s, %s, %s, to_timestamp(%s))
                """,
                (
                    event.event_type,
                    event.symbol,
                    json.dumps(event.payload),
                    event.received_at,
                ),
            )
        self._conn.commit()

    def close(self) -> None:
        self._conn.close()
