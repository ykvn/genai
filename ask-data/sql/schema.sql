-- Create Database
CREATE DATABASE IF NOT EXISTS bank_abc_analytics;
USE bank_abc_analytics;

-- 1. Customers Table
CREATE TABLE IF NOT EXISTS customers (
    customer_id INT AUTO_INCREMENT PRIMARY KEY,
    first_name VARCHAR(50),
    last_name VARCHAR(50),
    email VARCHAR(100),
    birth_date DATE,
    bank_name VARCHAR(50) DEFAULT 'ABC', -- Supports queries like "BNI customers"
    join_date DATE
);

-- 2. Savings Accounts Table
CREATE TABLE IF NOT EXISTS savings (
    savings_id INT AUTO_INCREMENT PRIMARY KEY,
    customer_id INT,
    account_number VARCHAR(20) UNIQUE,
    balance DECIMAL(15, 2),
    interest_rate DECIMAL(4, 2),
    status VARCHAR(20),
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
);

-- 3. Time Deposits Table
CREATE TABLE IF NOT EXISTS deposits (
    deposit_id INT AUTO_INCREMENT PRIMARY KEY,
    customer_id INT,
    account_number VARCHAR(20) UNIQUE,
    principal_amount DECIMAL(15, 2),
    maturity_date DATE,
    interest_rate DECIMAL(4, 2),
    status VARCHAR(20),
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
);

-- 4. Loans Table
CREATE TABLE IF NOT EXISTS loans (
    loan_id INT AUTO_INCREMENT PRIMARY KEY,
    customer_id INT,
    loan_type VARCHAR(30), -- Home, Auto, Personal
    principal_amount DECIMAL(15, 2),
    outstanding_balance DECIMAL(15, 2),
    maturity_date DATE,
    status VARCHAR(20),
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
);

-- 5. Credit Cards Table
CREATE TABLE IF NOT EXISTS credit_cards (
    card_id INT AUTO_INCREMENT PRIMARY KEY,
    customer_id INT,
    card_number VARCHAR(20) UNIQUE,
    credit_limit DECIMAL(15, 2),
    current_balance DECIMAL(15, 2),
    expiry_date DATE,
    status VARCHAR(20),
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
);

-- 6. Transactions Table
CREATE TABLE IF NOT EXISTS transactions (
    transaction_id INT AUTO_INCREMENT PRIMARY KEY,
    account_number VARCHAR(20),
    amount DECIMAL(15, 2),
    transaction_type VARCHAR(10), -- DEBIT, CREDIT
    transaction_timestamp DATETIME,
    description VARCHAR(255)
);

-- 7. Branch Metrics/Dashboards metadata (For dashboard context RAG queries)
CREATE TABLE IF NOT EXISTS branch_performance (
    branch_id INT AUTO_INCREMENT PRIMARY KEY,
    branch_name VARCHAR(50),
    region VARCHAR(50),
    total_active_customers INT,
    monthly_target_achieved DECIMAL(5,2)
);

-- =====================================================================
-- SEED DUMMY DATA WITH DYNAMIC DATE LOGIC
-- =====================================================================

INSERT INTO customers (first_name, last_name, email, birth_date, bank_name, join_date) VALUES
-- Customers celebrating birthdays this week (Dynamic)
('Ahmad', 'Fauzi', 'ahmad.f@bni.co.id', DATE_SUB(DATE_ADD(CURDATE(), INTERVAL 2 DAY), INTERVAL 30 YEAR), 'BNI', '2020-01-15'),
('Siti', 'Aminah', 'siti.a@bni.co.id', DATE_SUB(DATE_ADD(CURDATE(), INTERVAL 4 DAY), INTERVAL(25) YEAR), 'BNI', '2021-03-22'),
('Budi', 'Santoso', 'budi.s@abc.com', DATE_SUB(DATE_ADD(CURDATE(), INTERVAL 1 DAY), INTERVAL 45 YEAR), 'ABC', '2019-11-02'),
-- General Customers
('John', 'Doe', 'john.doe@abc.com', '1988-05-12', 'ABC', '2022-06-18'),
('Jane', 'Smith', 'jane.smith@bni.co.id', '1992-09-25', 'BNI', '2023-02-10');

INSERT INTO savings (customer_id, account_number, balance, interest_rate, status) VALUES
(1, 'SAV-BNI-001', 25000000.00, 2.50, 'ACTIVE'),
(2, 'SAV-BNI-002', 75000000.00, 2.75, 'ACTIVE'),
(3, 'SAV-ABC-003', 120000000.00, 3.00, 'ACTIVE'),
(4, 'SAV-ABC-004', 5000000.00, 1.50, 'DORMANT');

INSERT INTO deposits (customer_id, account_number, principal_amount, maturity_date, interest_rate, status) VALUES
-- Approaching maturity date within 7 days
(1, 'DEP-BNI-101', 100000000.00, DATE_ADD(CURDATE(), INTERVAL 3 DAY), 5.25, 'ACTIVE'),
(3, 'DEP-ABC-102', 500000000.00, DATE_ADD(CURDATE(), INTERVAL 6 DAY), 5.50, 'ACTIVE'),
-- Distant maturity
(4, 'DEP-ABC-103', 50000000.00, DATE_ADD(CURDATE(), INTERVAL 180 DAY), 4.75, 'ACTIVE');

INSERT INTO loans (customer_id, loan_type, principal_amount, outstanding_balance, maturity_date, status) VALUES
-- Loan approaching maturity date
(2, 'Personal', 50000000.00, 4500000.00, DATE_ADD(CURDATE(), INTERVAL 5 DAY), 'ACTIVE'),
(3, 'Mortgage', 1200000000.00, 980000000.00, DATE_ADD(CURDATE(), INTERVAL 10 YEAR), 'ACTIVE');

INSERT INTO credit_cards (customer_id, card_number, credit_limit, current_balance, expiry_date, status) VALUES
(1, '4560-1234-8888-1111', 50000000.00, 12500000.00, DATE_ADD(CURDATE(), INTERVAL 2 YEAR), 'ACTIVE'),
(4, '4560-1234-8888-2222', 20000000.00, 19500000.00, DATE_ADD(CURDATE(), INTERVAL 1 MONTH), 'WARNING');

INSERT INTO transactions (account_number, amount, transaction_type, transaction_timestamp, description) VALUES
('SAV-BNI-001', 500000.00, 'DEBIT', DATE_SUB(NOW(), INTERVAL 2 HOUR), 'ATM Withdrawal'),
('SAV-ABC-003', 1500000.00, 'CREDIT', DATE_SUB(NOW(), INTERVAL 1 DAY), 'Payroll Transfer');

INSERT INTO branch_performance (branch_name, region, total_active_customers, monthly_target_achieved) VALUES
('Jakarta Main Branch', 'DKI Jakarta', 12500, 104.50),
('Surabaya Cluster', 'East Java', 8400, 92.10);