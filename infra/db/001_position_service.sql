CREATE TABLE IF NOT EXISTS positions (
    symbol              VARCHAR(20)     PRIMARY KEY,
    net_qty             DECIMAL(20, 8)  NOT NULL DEFAULT 0,
    avg_entry_price     DECIMAL(20, 8)  NOT NULL DEFAULT 0,
    realized_pnl        DECIMAL(20, 8)  NOT NULL DEFAULT 0,
    unrealized_pnl      DECIMAL(20, 8)  NOT NULL DEFAULT 0,
    updated_at          TIMESTAMPTZ     NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS trades (
    id                  SERIAL          PRIMARY KEY,
    order_id            VARCHAR(50)     NOT NULL,
    symbol              VARCHAR(20)     NOT NULL,
    side                VARCHAR(4)      NOT NULL,
    quantity            DECIMAL(20, 8)  NOT NULL,
    fill_price          DECIMAL(20, 8)  NOT NULL,
    realized_pnl        DECIMAL(20, 8)  NOT NULL DEFAULT 0,
    filled_at           TIMESTAMPTZ     NOT NULL
);
