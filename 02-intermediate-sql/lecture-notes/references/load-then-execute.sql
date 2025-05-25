
-- https://www.pg4e.com/lectures/03-Techniques-Load.sql

-- Start fresh - Cascade deletes it all

-- Create table
CREATE TABLE accounts (
    id SERIAL,
    email VARCHAR(128) NOT NULL UNIQUE,
    balance NUMERIC(12, 2) NOT NULL,
    PRIMARY KEY(id)
);

-- Insert records
INSERT INTO accounts(email, balance) VALUES 
    ('ed@umich.edu', 100.00), 
    ('sue@umich.edu', 120.00), 
    ('sally@umich.edu', 150.00);

-- Show table content
SELECT * FROM accounts;

-- Reset table
DELETE FROM accounts;
ALTER SEQUENCE accounts_id_seq RESTART WITH 1;

-- Show table content
SELECT * FROM accounts;

-- Insert records
INSERT INTO accounts(email, balance) VALUES 
    ('ed@umich.edu', 120.00), 
    ('sue@umich.edu', 150.00), 
    ('sally@umich.edu', 180.00);

-- Show table content
SELECT * FROM accounts;