CREATE DATABASE IF NOT EXISTS data_warehouse;
USE data_warehouse;
CREATE TABLE transactions (
    transaction_id VARCHAR(50) PRIMARY KEY,
    user_id VARCHAR(50),
    user_name VARCHAR(100),
    product_id VARCHAR(50),
    amount DECIMAL(10, 2),
    currency VARCHAR(10),
    transaction_type VARCHAR(50),
    status VARCHAR(50),
    city VARCHAR(100),
    country VARCHAR(100),
    payment_method VARCHAR(50),
    product_category VARCHAR(50),
    quantity INT,
    street VARCHAR(100),
    zip VARCHAR(10),
    customer_rating INT,
    discount_code VARCHAR(50),
    tax_amount DECIMAL(10, 2),
    thread INT,
    message_number INT,
    timestamp_of_reception_log VARCHAR(50),
    timestamp DATETIME
);

CREATE TABLE TRANSACTION_PAR_TYPE(
    transaction_type VARCHAR(50),
    total_amount 
)

