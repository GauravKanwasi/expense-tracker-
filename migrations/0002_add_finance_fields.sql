BEGIN;

ALTER TABLE transactions
    ADD COLUMN IF NOT EXISTS debt_direction VARCHAR(20);

ALTER TABLE transactions
    ADD COLUMN IF NOT EXISTS interest_amount DOUBLE PRECISION;

ALTER TABLE transactions
    ADD COLUMN IF NOT EXISTS investment_action VARCHAR(20);

COMMIT;
