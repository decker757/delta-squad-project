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
        self._connect_args = dict(
            host=host,
            port=port,
            user=user,
            password=password,
            dbname=dbname,
            sslmode="require",
        )
        self._conn = psycopg2.connect(**self._connect_args)

    def _reconnect(self) -> None:
        self.logger.warning("DB connection lost — reconnecting...")
        try:
            self._conn.close()
        except Exception:
            pass
        self._conn = psycopg2.connect(**self._connect_args)
        self.logger.info("DB reconnected.")

    def insert_event(self, event: EventLog) -> None:
        try:
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
        except psycopg2.OperationalError:
            self._conn.rollback()
            self._reconnect()
            raise
        except Exception:
            self._conn.rollback()
            raise

    def close(self) -> None:
        self._conn.close()
