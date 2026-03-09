CREATE TABLE IF NOT EXISTS event_log (
    id              SERIAL          PRIMARY KEY,
    event_type      VARCHAR(50)     NOT NULL,
    symbol          VARCHAR(20)     NOT NULL,
    payload         JSONB           NOT NULL,
    received_at     TIMESTAMPTZ     NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_event_log_event_type ON event_log (event_type);
CREATE INDEX IF NOT EXISTS idx_event_log_symbol ON event_log (symbol);
CREATE INDEX IF NOT EXISTS idx_event_log_received_at ON event_log (received_at);
