-- Run this SQL in your Snowflake web interface to create demo data
-- Go to: https://app.snowflake.com/skrzcxp/djb84539/#/homepage
-- Click "Worksheets" → "+" → Paste this code → Click "Run"

-- Create a simple table with fake users
CREATE TABLE IF NOT EXISTS demo_users (
    id INTEGER,
    name STRING,
    join_date DATE,
    status STRING,
    region STRING,
    revenue NUMBER(10,2)
);

-- Insert fake data (5 users)
INSERT INTO demo_users VALUES
    (1, 'Alice Smith', '2024-03-15', 'active', 'East', 15000.50),
    (2, 'Bob Jones', '2025-01-20', 'active', 'West', 22000.00),
    (3, 'Carol White', '2025-06-10', 'inactive', 'East', 0.00),
    (4, 'David Brown', '2024-11-05', 'active', 'West', 18500.75),
    (5, 'Eve Davis', '2025-02-28', 'pending', 'South', 5000.00);

-- Test it works
SELECT * FROM demo_users;

-- You should see 5 rows of fake user data
