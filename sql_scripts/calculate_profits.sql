

SELECT t.id, datetime, price, tt.type, quantity, quantity_left, ticker, u.id FROM transactions AS t
JOIN stocks AS s ON t.stocks_id = s.id
JOIN users AS u ON u.id = t.users_id
LEFT JOIN portfolio AS p ON p.transactions_id = t.id
JOIN transaction_types AS tt ON tt.id = t.type
WHERE ticker = 'AMD'
AND u.id = 2
AND (quantity_left IN (0, NULL) OR tt.type IS 'sell')
ORDER BY t.datetime ASC
;
-- output:
-- +-----+------------+--------+------+----------+---------------+--------+----+
-- | id  |  datetime  | price  | type | quantity | quantity_left | ticker | id |
-- +-----+------------+--------+------+----------+---------------+--------+----+
-- | 11  | 1728416372 | 133.59 | buy  | 2        | 0             | AMD    | 2  |
-- | 12  | 1728416505 | 134.33 | buy  | 1        | 0             | AMD    | 2  |
-- | 13  | 1728416614 | 133.08 | buy  | 1        | 0             | AMD    | 2  |
-- | 14  | 1728416704 | 134.05 | buy  | 1        | 0             | AMD    | 2  |
-- | 15  | 1728416717 | 133.11 | buy  | 2        | 0             | AMD    | 2  |
-- | 18  | 1728417773 | 134.06 | buy  | 1        | 0             | AMD    | 2  |
-- | 19  | 1728430911 | 133.64 | sell | 1        | NULL          | AMD    | 2  |
-- | 22  | 1728431586 | 134.46 | sell | 1        | NULL          | AMD    | 2  |
-- | 24  | 1728432070 | 134.82 | sell | 1        | NULL          | AMD    | 2  |
-- | 32  | 1728432992 | 134.33 | buy  | 2        | 0             | AMD    | 2  |
-- | 33  | 1728432995 | 134.75 | buy  | 3        | 0             | AMD    | 2  |
-- | 34  | 1728432998 | 134.16 | buy  | 1        | 0             | AMD    | 2  |
-- | 35  | 1728433002 | 133.93 | buy  | 5        | 0             | AMD    | 2  |
-- | 43  | 1728433476 | 134.91 | buy  | 1        | 0             | AMD    | 2  |
-- | 44  | 1728433557 | 134.97 | buy  | 1        | 0             | AMD    | 2  |
-- | 45  | 1728433688 | 133.96 | buy  | 1        | 0             | AMD    | 2  |
-- | 49  | 1728434079 | 134.88 | buy  | 20       | 0             | AMD    | 2  |
-- | 50  | 1728434112 | 134.3  | sell | 20       | NULL          | AMD    | 2  |
-- | 52  | 1728436406 | 134.07 | buy  | 20       | 0             | AMD    | 2  |
-- | 58  | 1728437006 | 134.18 | buy  | 1        | 0             | AMD    | 2  |
-- | 59  | 1728437647 | 134.16 | buy  | 2        | 0             | AMD    | 2  |
-- | 60  | 1728437656 | 135.19 | buy  | 2        | 0             | AMD    | 2  |
-- | 63  | 1728437757 | 134.38 | sell | 39       | NULL          | AMD    | 2  |
-- | 65  | 1728437853 | 135.1  | buy  | 1        | 0             | AMD    | 2  |
-- | 66  | 1728489258 | 133.84 | buy  | 2        | 0             | AMD    | 2  |
-- | 67  | 1728489321 | 133.72 | buy  | 2        | 0             | AMD    | 2  |
-- | 120 | 1728931981 | 133.28 | sell | 5        | NULL          | AMD    | 2  |
-- +-----+------------+--------+------+----------+---------------+--------+----+


-- Same query as above, but without the unnecessary columns
SELECT datetime, price, tt.type, quantity FROM transactions AS t
JOIN stocks AS s ON t.stocks_id = s.id
JOIN users AS u ON u.id = t.users_id
LEFT JOIN portfolio AS p ON p.transactions_id = t.id
JOIN transaction_types AS tt ON tt.id = t.type
WHERE ticker = 'AMD'
AND u.id = 2
AND (quantity_left IN (0, NULL) OR tt.type IS 'sell')
ORDER BY t.datetime ASC
;
-- output:
-- +------------+--------+------+----------+
-- |  datetime  | price  | type | quantity |
-- +------------+--------+------+----------+
-- | 1728416372 | 133.59 | buy  | 2        |
-- | 1728416505 | 134.33 | buy  | 1        |
-- | 1728416614 | 133.08 | buy  | 1        |
-- | 1728416704 | 134.05 | buy  | 1        |
-- | 1728416717 | 133.11 | buy  | 2        |
-- | 1728417773 | 134.06 | buy  | 1        |
-- | 1728430911 | 133.64 | sell | 1        |
-- | 1728431586 | 134.46 | sell | 1        |
-- | 1728432070 | 134.82 | sell | 1        |
-- | 1728432992 | 134.33 | buy  | 2        |
-- | 1728432995 | 134.75 | buy  | 3        |
-- | 1728432998 | 134.16 | buy  | 1        |
-- | 1728433002 | 133.93 | buy  | 5        |
-- | 1728433476 | 134.91 | buy  | 1        |
-- | 1728433557 | 134.97 | buy  | 1        |
-- | 1728433688 | 133.96 | buy  | 1        |
-- | 1728434079 | 134.88 | buy  | 20       |
-- | 1728434112 | 134.3  | sell | 20       |
-- | 1728436406 | 134.07 | buy  | 20       |
-- | 1728437006 | 134.18 | buy  | 1        |
-- | 1728437647 | 134.16 | buy  | 2        |
-- | 1728437656 | 135.19 | buy  | 2        |
-- | 1728437757 | 134.38 | sell | 39       |
-- | 1728437853 | 135.1  | buy  | 1        |
-- | 1728489258 | 133.84 | buy  | 2        |
-- | 1728489321 | 133.72 | buy  | 2        |
-- | 1728931981 | 133.28 | sell | 5        |
-- +------------+--------+------+----------+