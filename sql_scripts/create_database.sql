CREATE TABLE users (
    'id'    INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL, 
    'username' TEXT NOT NULL, 
    'hash'  TEXT    NOT NULL, 
    'cash'  NUMERIC NOT NULL DEFAULT 10000.00);
CREATE TABLE sqlite_sequence(name,seq);
CREATE UNIQUE INDEX username ON users (username);
CREATE TABLE stocks (
    'id'        INTEGER PRIMARY KEY AUTOINCREMENT,
    'ticker'    TEXT    UNIQUE      NOT NULL,
    'company_name'      TEXT
);
CREATE UNIQUE INDEX ticker ON stocks (ticker);
CREATE TABLE IF NOT EXISTS "transactions" (
    'id'        INTEGER     PRIMARY KEY AUTOINCREMENT,
    'datetime'  INTEGER     NOT NULL    DEFAULT (unixepoch(CURRENT_TIMESTAMP)),
    'price'     NUMERIC     NOT NULL,
    'type'      INTEGER     NOT NULL,
    'quantity'  INTEGER     NOT NULL,
    'stocks_id' INTEGER,
    'users_id'  INTEGER     NOT NULL,
    FOREIGN KEY (stocks_id) REFERENCES stocks(id),
    FOREIGN KEY (type) REFERENCES transaction_types(id),
    FOREIGN KEY (users_id) REFERENCES users(id)
);
CREATE TABLE portfolio (
    'id'                INTEGER     PRIMARY KEY AUTOINCREMENT,
    'transactions_id'   INTEGER     NOT NULL,
    'quantity_left'     INTEGER     NOT NULL,
    FOREIGN KEY (transactions_id) REFERENCES "transactions"(id)
);
CREATE INDEX portfolio_transactions_id_index ON portfolio(transactions_id);
CREATE TABLE transaction_types(
       'id'     INTEGER PRIMARY KEY AUTOINCREMENT,
       'type'   TEXT NOT NULL
);

INSERT INTO transaction_types (id, type)
VALUES
(1, 'buy'),
(2, 'sell'),
(3, 'cash add'),
(4, 'cash withdraw');