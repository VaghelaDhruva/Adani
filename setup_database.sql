-- Setup script for SQLite database with sample data
-- Run this to create tables and populate with test data

-- Create orders table
CREATE TABLE IF NOT EXISTS orders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    amount DECIMAL(10,2) NOT NULL,
    order_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR(20) DEFAULT 'completed'
);

-- Create users table
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username VARCHAR(50) NOT NULL,
    email VARCHAR(100) NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Create visits table (optional - for conversion rate calculation)
CREATE TABLE IF NOT EXISTS visits (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    visit_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    page_url VARCHAR(200),
    session_id VARCHAR(100)
);

-- Create KPI summary table (optional - for pre-aggregated data)
CREATE TABLE IF NOT EXISTS kpi_summary (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    total_revenue_today DECIMAL(12,2) DEFAULT 0,
    total_orders_today INTEGER DEFAULT 0,
    active_users_today INTEGER DEFAULT 0,
    conversion_rate_today DECIMAL(5,2) DEFAULT 0,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Insert sample users
INSERT OR IGNORE INTO users (id, username, email) VALUES
(1, 'john_doe', 'john@example.com'),
(2, 'jane_smith', 'jane@example.com'),
(3, 'bob_wilson', 'bob@example.com'),
(4, 'alice_brown', 'alice@example.com'),
(5, 'charlie_davis', 'charlie@example.com'),
(6, 'diana_miller', 'diana@example.com'),
(7, 'frank_garcia', 'frank@example.com'),
(8, 'grace_martinez', 'grace@example.com'),
(9, 'henry_lopez', 'henry@example.com'),
(10, 'ivy_anderson', 'ivy@example.com');

-- Insert sample orders for the past 30 days
INSERT OR IGNORE INTO orders (user_id, amount, order_date) VALUES
-- Today's orders
(1, 129.99, datetime('now', 'localtime')),
(2, 89.50, datetime('now', 'localtime')),
(3, 199.99, datetime('now', 'localtime')),
(4, 45.00, datetime('now', 'localtime')),
(5, 299.99, datetime('now', 'localtime')),

-- Yesterday's orders
(2, 159.99, datetime('now', 'localtime', '-1 day')),
(6, 79.99, datetime('now', 'localtime', '-1 day')),
(7, 249.99, datetime('now', 'localtime', '-1 day')),
(1, 99.99, datetime('now', 'localtime', '-1 day')),

-- 2 days ago
(8, 189.99, datetime('now', 'localtime', '-2 days')),
(9, 119.99, datetime('now', 'localtime', '-2 days')),
(10, 69.99, datetime('now', 'localtime', '-2 days')),
(3, 299.99, datetime('now', 'localtime', '-2 days')),

-- 3 days ago
(4, 149.99, datetime('now', 'localtime', '-3 days')),
(5, 199.99, datetime('now', 'localtime', '-3 days')),
(6, 89.99, datetime('now', 'localtime', '-3 days')),

-- 4 days ago
(7, 259.99, datetime('now', 'localtime', '-4 days')),
(8, 179.99, datetime('now', 'localtime', '-4 days')),
(1, 99.99, datetime('now', 'localtime', '-4 days')),

-- 5 days ago
(9, 219.99, datetime('now', 'localtime', '-5 days')),
(10, 139.99, datetime('now', 'localtime', '-5 days')),
(2, 169.99, datetime('now', 'localtime', '-5 days')),

-- 6 days ago
(3, 289.99, datetime('now', 'localtime', '-6 days')),
(4, 119.99, datetime('now', 'localtime', '-6 days')),

-- 7 days ago (1 week ago)
(5, 199.99, datetime('now', 'localtime', '-7 days')),
(6, 149.99, datetime('now', 'localtime', '-7 days')),
(7, 229.99, datetime('now', 'localtime', '-7 days')),
(8, 99.99, datetime('now', 'localtime', '-7 days')),

-- Additional historical data (past 2-4 weeks)
(1, 179.99, datetime('now', 'localtime', '-10 days')),
(2, 259.99, datetime('now', 'localtime', '-10 days')),
(3, 89.99, datetime('now', 'localtime', '-12 days')),
(4, 199.99, datetime('now', 'localtime', '-12 days')),
(5, 149.99, datetime('now', 'localtime', '-15 days')),
(6, 299.99, datetime('now', 'localtime', '-15 days')),
(7, 119.99, datetime('now', 'localtime', '-18 days')),
(8, 189.99, datetime('now', 'localtime', '-18 days')),
(9, 229.99, datetime('now', 'localtime', '-20 days')),
(10, 169.99, datetime('now', 'localtime', '-20 days')),
(1, 99.99, datetime('now', 'localtime', '-25 days')),
(2, 279.99, datetime('now', 'localtime', '-25 days')),
(3, 159.99, datetime('now', 'localtime', '-28 days')),
(4, 219.99, datetime('now', 'localtime', '-28 days'));

-- Insert sample visits (for conversion rate calculation)
INSERT OR IGNORE INTO visits (user_id, visit_date, page_url, session_id) VALUES
-- Today's visits
(1, datetime('now', 'localtime'), '/home', 'sess_001'),
(2, datetime('now', 'localtime'), '/products', 'sess_002'),
(3, datetime('now', 'localtime'), '/home', 'sess_003'),
(4, datetime('now', 'localtime'), '/products', 'sess_004'),
(5, datetime('now', 'localtime'), '/checkout', 'sess_005'),
(11, datetime('now', 'localtime'), '/home', 'sess_006'), -- visitor who didn't order
(12, datetime('now', 'localtime'), '/products', 'sess_007'), -- visitor who didn't order

-- Yesterday's visits
(2, datetime('now', 'localtime', '-1 day'), '/home', 'sess_008'),
(6, datetime('now', 'localtime', '-1 day'), '/products', 'sess_009'),
(7, datetime('now', 'localtime', '-1 day'), '/checkout', 'sess_010'),
(1, datetime('now', 'localtime', '-1 day'), '/home', 'sess_011'),
(13, datetime('now', 'localtime', '-1 day'), '/home', 'sess_012'), -- visitor who didn't order
(14, datetime('now', 'localtime', '-1 day'), '/products', 'sess_013'); -- visitor who didn't order

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_orders_date ON orders(order_date);
CREATE INDEX IF NOT EXISTS idx_orders_user_id ON orders(user_id);
CREATE INDEX IF NOT EXISTS idx_visits_date ON visits(visit_date);
CREATE INDEX IF NOT EXISTS idx_visits_user_id ON visits(user_id);
CREATE INDEX IF NOT EXISTS idx_kpi_summary_date ON kpi_summary(updated_at);