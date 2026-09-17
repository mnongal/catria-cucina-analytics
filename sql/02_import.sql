-- Start the mysql client from the repository root. CSV files use UTF-8 and LF.
-- Both client and server must permit LOCAL INFILE. See docs/SETUP.md.
-- Load into empty tables only. Inspect every warning; LOCAL can downgrade errors.
USE restaurant_analytics;
LOAD DATA LOCAL INFILE 'data/raw/servers.csv' INTO TABLE servers
CHARACTER SET utf8mb4 FIELDS TERMINATED BY ',' OPTIONALLY ENCLOSED BY '"'
LINES TERMINATED BY '\n' IGNORE 1 LINES (server_id,server_name);
SHOW WARNINGS;

LOAD DATA LOCAL INFILE 'data/raw/menu_items.csv' INTO TABLE menu_items
CHARACTER SET utf8mb4 FIELDS TERMINATED BY ',' OPTIONALLY ENCLOSED BY '"'
LINES TERMINATED BY '\n' IGNORE 1 LINES (item_id,item_name,category,selling_price,unit_cost);
SHOW WARNINGS;

LOAD DATA LOCAL INFILE 'data/raw/orders.csv' INTO TABLE orders
CHARACTER SET utf8mb4 FIELDS TERMINATED BY ',' OPTIONALLY ENCLOSED BY '"'
LINES TERMINATED BY '\n' IGNORE 1 LINES
(order_id,order_date,order_time,server_id,@table_number,@party_size,channel,status,
 discount_percent,payment_method,@service_minutes,@check_duration_minutes)
SET table_number=NULLIF(@table_number,''), party_size=NULLIF(@party_size,''),
    service_minutes=NULLIF(@service_minutes,''),
    check_duration_minutes=NULLIF(@check_duration_minutes,'');
SHOW WARNINGS;

LOAD DATA LOCAL INFILE 'data/raw/order_items.csv' INTO TABLE order_items
CHARACTER SET utf8mb4 FIELDS TERMINATED BY ',' OPTIONALLY ENCLOSED BY '"'
LINES TERMINATED BY '\n' IGNORE 1 LINES
(order_item_id,order_id,item_id,quantity,unit_price,unit_cost);
SHOW WARNINGS;
