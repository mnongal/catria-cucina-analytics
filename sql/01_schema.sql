-- MySQL 8.0.16+ / 8.4. Non-destructive: fails on existing tables.
CREATE DATABASE IF NOT EXISTS restaurant_analytics CHARACTER SET utf8mb4;
USE restaurant_analytics;

CREATE TABLE servers (
  server_id INT PRIMARY KEY,
  server_name VARCHAR(50) NOT NULL
) ENGINE=InnoDB;

CREATE TABLE menu_items (
  item_id INT PRIMARY KEY,
  item_name VARCHAR(80) NOT NULL,
  category VARCHAR(20) NOT NULL,
  selling_price DECIMAL(10,2) NOT NULL CHECK (selling_price > 0),
  unit_cost DECIMAL(10,2) NOT NULL CHECK (unit_cost >= 0)
) ENGINE=InnoDB;

CREATE TABLE orders (
  order_id INT PRIMARY KEY,
  order_date DATE NOT NULL,
  order_time TIME NOT NULL,
  server_id INT NOT NULL,
  table_number INT NULL,
  party_size INT NULL,
  channel VARCHAR(12) NOT NULL CHECK (channel IN ('dine_in','takeaway')),
  status VARCHAR(12) NOT NULL CHECK (status IN ('completed','cancelled')),
  discount_percent INT NOT NULL CHECK (discount_percent BETWEEN 0 AND 100),
  payment_method VARCHAR(20) NOT NULL,
  service_minutes INT NULL,
  check_duration_minutes INT NULL,
  FOREIGN KEY (server_id) REFERENCES servers(server_id),
  CHECK ((channel='dine_in' AND table_number IS NOT NULL AND table_number BETWEEN 1 AND 24
          AND party_size IS NOT NULL AND party_size BETWEEN 1 AND 6)
         OR (channel='takeaway' AND table_number IS NULL AND party_size IS NULL)),
  CHECK ((status='completed' AND service_minutes IS NOT NULL AND service_minutes>0
          AND check_duration_minutes IS NOT NULL AND check_duration_minutes>=service_minutes)
         OR (status='cancelled' AND service_minutes IS NULL AND check_duration_minutes IS NULL)),
  INDEX idx_orders_date_status (order_date,status),
  INDEX idx_orders_channel (channel)
) ENGINE=InnoDB;

CREATE TABLE order_items (
  order_item_id INT PRIMARY KEY,
  order_id INT NOT NULL,
  item_id INT NOT NULL,
  quantity INT NOT NULL CHECK (quantity>0),
  unit_price DECIMAL(10,2) NOT NULL CHECK (unit_price>0),
  unit_cost DECIMAL(10,2) NOT NULL CHECK (unit_cost>=0),
  FOREIGN KEY (order_id) REFERENCES orders(order_id),
  FOREIGN KEY (item_id) REFERENCES menu_items(item_id),
  UNIQUE KEY uq_order_item (order_id,item_id)
) ENGINE=InnoDB;
