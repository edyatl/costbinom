BEGIN TRANSACTION;
CREATE TABLE binom (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    date       DATETIME,
    source     TEXT,
    binom_id   INTEGER,
    date_s     TEXT,
    date_e     TEXT,
    timezone   NUMERIC,
    token_val  NUMERIC,
    cost       REAL
);
COMMIT;
