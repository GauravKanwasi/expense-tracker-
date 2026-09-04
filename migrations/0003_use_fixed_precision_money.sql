-- Store money exactly: 29 whole-number digits and 2 decimal places.
ALTER TABLE transactions
    ALTER COLUMN amount TYPE NUMERIC(31, 2)
    USING amount::NUMERIC(31, 2),
    ALTER COLUMN interest_amount TYPE NUMERIC(31, 2)
    USING interest_amount::NUMERIC(31, 2);

ALTER TABLE budgets
    ALTER COLUMN amount TYPE NUMERIC(31, 2)
    USING amount::NUMERIC(31, 2);
