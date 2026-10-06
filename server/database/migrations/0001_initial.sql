CREATE TABLE clients (
    id                TEXT PRIMARY KEY,
    slug              TEXT NOT NULL UNIQUE,
    business_name     TEXT NOT NULL,
    contact_name      TEXT,
    contact_phone     TEXT,
    token_hash        TEXT NOT NULL UNIQUE,
    tier              TEXT NOT NULL CHECK (tier IN ('core','growth','advanced')),
    status            TEXT NOT NULL CHECK (status IN ('active','suspended','offboarded')),
    app_version       TEXT,
    last_sync_at      TEXT,
    last_update_at    TEXT,
    payment_status    TEXT NOT NULL CHECK (payment_status IN ('paid','pending','overdue')),
    contract_start    TEXT,
    offboarded_at     TEXT,
    created_at        TEXT NOT NULL,
    updated_at        TEXT NOT NULL
);

CREATE UNIQUE INDEX idx_clients_token_hash ON clients(token_hash);
CREATE UNIQUE INDEX idx_clients_slug       ON clients(slug);
CREATE INDEX        idx_clients_status     ON clients(status);
CREATE INDEX        idx_clients_last_sync  ON clients(last_sync_at);
CREATE INDEX        idx_clients_offboarded ON clients(offboarded_at);
