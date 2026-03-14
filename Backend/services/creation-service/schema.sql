CREATE TABLE IF NOT EXISTS url_mappings (
    short_code VARCHAR(32) PRIMARY KEY,
    original_url TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
