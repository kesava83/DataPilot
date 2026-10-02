import os
import sqlite3
import random
from datetime import datetime, timedelta

SAMPLE_DB_PATH = "sample_ecommerce.db"


def init_sample_database(force_recreate: bool = False):
    """
    Initializes a rich sample eCommerce database for testing natural language queries
    before user connects their real PostgreSQL database.
    """
    if os.path.exists(SAMPLE_DB_PATH) and not force_recreate:
        return SAMPLE_DB_PATH

    conn = sqlite3.connect(SAMPLE_DB_PATH)
    cursor = conn.cursor()

    cursor.executescript("""
    DROP TABLE IF EXISTS reviews;
    DROP TABLE IF EXISTS order_items;
    DROP TABLE IF EXISTS orders;
    DROP TABLE IF EXISTS products;
    DROP TABLE IF EXISTS customers;

    CREATE TABLE customers (
        customer_id INTEGER PRIMARY KEY AUTOINCREMENT,
        first_name TEXT NOT NULL,
        last_name TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        country TEXT NOT NULL,
        city TEXT NOT NULL,
        signup_date DATE NOT NULL,
        customer_tier TEXT NOT NULL -- 'Bronze', 'Silver', 'Gold', 'Platinum'
    );

    CREATE TABLE products (
        product_id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        category TEXT NOT NULL, -- 'Electronics', 'Audio', 'Accessories', 'Office', 'Wearables'
        price DECIMAL(10, 2) NOT NULL,
        cost DECIMAL(10, 2) NOT NULL,
        stock_quantity INTEGER NOT NULL,
        rating DECIMAL(3, 2) NOT NULL
    );

    CREATE TABLE orders (
        order_id INTEGER PRIMARY KEY AUTOINCREMENT,
        customer_id INTEGER NOT NULL,
        order_date TIMESTAMP NOT NULL,
        status TEXT NOT NULL, -- 'Completed', 'Processing', 'Shipped', 'Cancelled'
        total_amount DECIMAL(10, 2) NOT NULL,
        payment_method TEXT NOT NULL, -- 'Credit Card', 'PayPal', 'Apple Pay', 'Bank Transfer'
        shipping_city TEXT NOT NULL,
        FOREIGN KEY (customer_id) REFERENCES customers (customer_id)
    );

    CREATE TABLE order_items (
        item_id INTEGER PRIMARY KEY AUTOINCREMENT,
        order_id INTEGER NOT NULL,
        product_id INTEGER NOT NULL,
        quantity INTEGER NOT NULL,
        unit_price DECIMAL(10, 2) NOT NULL,
        discount DECIMAL(4, 2) DEFAULT 0.00,
        FOREIGN KEY (order_id) REFERENCES orders (order_id),
        FOREIGN KEY (product_id) REFERENCES products (product_id)
    );

    CREATE TABLE reviews (
        review_id INTEGER PRIMARY KEY AUTOINCREMENT,
        product_id INTEGER NOT NULL,
        customer_id INTEGER NOT NULL,
        rating INTEGER NOT NULL CHECK (rating >= 1 AND rating <= 5),
        title TEXT,
        comment TEXT,
        review_date DATE NOT NULL,
        FOREIGN KEY (product_id) REFERENCES products (product_id),
        FOREIGN KEY (customer_id) REFERENCES customers (customer_id)
    );
    """)

    # Seed Customers
    customers_data = [
        ("Alice", "Johnson", "alice.j@example.com", "United States", "New York", "2023-01-15", "Platinum"),
        ("Bob", "Smith", "bob.smith@example.com", "United States", "San Francisco", "2023-02-10", "Gold"),
        ("Charlie", "Brown", "charlie.b@example.com", "Canada", "Toronto", "2023-03-05", "Silver"),
        ("Diana", "Prince", "diana.p@example.com", "United Kingdom", "London", "2023-01-28", "Platinum"),
        ("Evan", "Davis", "evan.d@example.com", "United States", "Austin", "2023-04-12", "Bronze"),
        ("Fiona", "Gallagher", "fiona.g@example.com", "United States", "Chicago", "2023-05-19", "Gold"),
        ("George", "Clark", "george.c@example.com", "Germany", "Berlin", "2023-02-22", "Silver"),
        ("Hannah", "Abbott", "hannah.a@example.com", "United Kingdom", "Manchester", "2023-06-01", "Bronze"),
        ("Ian", "Malcolm", "ian.m@example.com", "United States", "Seattle", "2023-03-18", "Gold"),
        ("Julia", "Roberts", "julia.r@example.com", "United States", "Los Angeles", "2023-01-09", "Platinum"),
        ("Kevin", "Bacon", "kevin.b@example.com", "Canada", "Vancouver", "2023-07-14", "Bronze"),
        ("Laura", "Croft", "laura.c@example.com", "United Kingdom", "Edinburgh", "2023-04-03", "Gold"),
        ("Michael", "Scott", "michael.s@example.com", "United States", "Scranton", "2023-08-20", "Silver"),
        ("Nina", "Simone", "nina.s@example.com", "France", "Paris", "2023-05-11", "Platinum"),
        ("Oscar", "Martinez", "oscar.m@example.com", "United States", "Miami", "2023-06-25", "Gold"),
        ("Pam", "Beesly", "pam.b@example.com", "United States", "Philadelphia", "2023-02-14", "Silver"),
        ("Quinn", "Fabray", "quinn.f@example.com", "United States", "Boston", "2023-09-02", "Bronze"),
        ("Rachel", "Green", "rachel.g@example.com", "United States", "New York", "2023-03-30", "Platinum"),
        ("Sam", "Winchester", "sam.w@example.com", "United States", "Denver", "2023-07-08", "Gold"),
        ("Tina", "Fey", "tina.f@example.com", "Canada", "Montreal", "2023-08-17", "Silver"),
    ]
    cursor.executemany(
        "INSERT INTO customers (first_name, last_name, email, country, city, signup_date, customer_tier) VALUES (?, ?, ?, ?, ?, ?, ?)",
        customers_data
    )

    # Seed Products
    products_data = [
        ("Noise-Canceling Wireless Headphones", "Audio", 299.99, 140.00, 85, 4.8),
        ("Ergonomic Mechanical Keyboard", "Accessories", 129.50, 60.00, 140, 4.6),
        ("Ultra-Wide 4K Gaming Monitor 34-inch", "Electronics", 649.00, 390.00, 32, 4.7),
        ("Smart Fitness Watch Pro", "Wearables", 199.95, 95.00, 110, 4.4),
        ("USB-C Multiport Docking Station", "Accessories", 79.99, 32.00, 220, 4.5),
        ("True Wireless Sport Earbuds", "Audio", 119.00, 48.00, 95, 4.2),
        ("Height Adjustable Standing Desk", "Office", 449.00, 240.00, 25, 4.9),
        ("Ergonomic Mesh Office Chair", "Office", 329.00, 160.00, 45, 4.7),
        ("Thunderbolt 4 External SSD 2TB", "Electronics", 219.00, 110.00, 75, 4.8),
        ("Precision Wireless Mouse", "Accessories", 69.90, 28.00, 180, 4.3),
        ("Studio Condenser USB Microphone", "Audio", 149.00, 65.00, 60, 4.6),
        ("Smart LED Desk Lamp with Qi Charger", "Office", 59.99, 22.00, 130, 4.1),
        ("MagSafe Wireless Power Bank 10000mAh", "Accessories", 49.99, 19.00, 250, 4.5),
        ("4K Ultra HD Streaming Webcam", "Electronics", 129.99, 58.00, 80, 4.4),
        ("Smart Water Bottle with Hydration Tracker", "Wearables", 64.50, 25.00, 90, 3.9),
    ]
    cursor.executemany(
        "INSERT INTO products (name, category, price, cost, stock_quantity, rating) VALUES (?, ?, ?, ?, ?, ?)",
        products_data
    )

    # Seed Orders and Order Items
    random.seed(42)
    start_date = datetime(2023, 6, 1)
    end_date = datetime(2024, 3, 31)
    days_range = (end_date - start_date).days

    orders = []
    order_items = []
    item_id_counter = 1

    payment_methods = ["Credit Card", "PayPal", "Apple Pay", "Bank Transfer"]
    statuses = ["Completed", "Completed", "Completed", "Shipped", "Processing", "Cancelled"]

    for order_id in range(1, 95):
        cust_id = random.randint(1, len(customers_data))
        random_days = random.randint(0, days_range)
        order_date = start_date + timedelta(days=random_days, hours=random.randint(8, 20), minutes=random.randint(0, 59))
        status = random.choice(statuses)
        payment_method = random.choice(payment_methods)
        city = customers_data[cust_id - 1][5]

        # Generate 1 to 4 items for this order
        num_items = random.randint(1, 3)
        selected_prods = random.sample(range(1, len(products_data) + 1), num_items)
        order_total = 0.0

        for prod_id in selected_prods:
            qty = random.randint(1, 2)
            unit_price = products_data[prod_id - 1][2]
            discount = random.choice([0.0, 0.0, 0.05, 0.10, 0.15])
            line_total = round(qty * unit_price * (1 - discount), 2)
            order_total += line_total

            order_items.append((
                item_id_counter,
                order_id,
                prod_id,
                qty,
                unit_price,
                discount
            ))
            item_id_counter += 1

        orders.append((
            order_id,
            cust_id,
            order_date.strftime("%Y-%m-%d %H:%M:%S"),
            status,
            round(order_total, 2),
            payment_method,
            city
        ))

    cursor.executemany(
        "INSERT INTO orders (order_id, customer_id, order_date, status, total_amount, payment_method, shipping_city) VALUES (?, ?, ?, ?, ?, ?, ?)",
        orders
    )

    cursor.executemany(
        "INSERT INTO order_items (item_id, order_id, product_id, quantity, unit_price, discount) VALUES (?, ?, ?, ?, ?, ?)",
        order_items
    )

    # Seed Reviews
    reviews_data = [
        (1, 1, 5, "Phenomenal sound and comfort!", "The active noise cancellation is the best I've experienced. Battery lasts multiple flights.", "2023-09-12"),
        (2, 2, 5, "Tactile perfection", "Crisp keys, great build quality. Typing for long coding sessions feels effortless.", "2023-10-05"),
        (3, 4, 5, "Game changer for productivity", "Having this 34-inch curved monitor replaced my dual screen setup. Spectacular colors.", "2023-11-20"),
        (4, 5, 4, "Reliable fitness tracker", "Tracks sleep and heart rate with high precision. Battery lasts ~5 days.", "2023-08-14"),
        (7, 10, 5, "My back thanks me!", "Solid motorized desk with presets. Sturdy even at full height.", "2023-09-28"),
        (8, 14, 5, "Top notch ergonomic support", "Worth every penny. The lumbar support relieves hours of tension.", "2023-12-01"),
        (9, 6, 4, "Blazing fast transfers", "Getting ~2800 MB/s read speeds on Thunderbolt 4. Compact and sturdy.", "2023-10-18"),
        (11, 9, 5, "Crystal clear voice audio", "Used for podcasting and conference calls. Zero background hiss.", "2023-11-04"),
        (14, 18, 4, "Sharp video quality in low light", "Autofocus is super snappy. The privacy shutter is a nice touch.", "2023-12-19"),
        (15, 7, 3, "Decent, but app needs polish", "Hydration alerts work fine, but syncing sometimes requires restarting Bluetooth.", "2024-01-08"),
    ]
    cursor.executemany(
        "INSERT INTO reviews (product_id, customer_id, rating, title, comment, review_date) VALUES (?, ?, ?, ?, ?, ?)",
        reviews_data
    )

    conn.commit()
    conn.close()
    return SAMPLE_DB_PATH
