CREATE TABLE audit_log (
    id            TEXT PRIMARY KEY,
    actor         TEXT NOT NULL,
    action        TEXT NOT NULL,
    target_slug   TEXT NOT NULL,
    old_value     TEXT,
    new_value     TEXT,
    reason        TEXT,
    ip_address    TEXT,
    timestamp     TEXT NOT NULL
);

CREATE INDEX idx_audit_target_time ON audit_log(target_slug, timestamp);
CREATE INDEX idx_audit_time        ON audit_log(timestamp);
