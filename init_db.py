import sqlite3
import pandas as pd

def init_db():
    conn = sqlite3.connect('data.db')
    cursor = conn.cursor()

    # Create Products table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS products (
        id INTEGER PRIMARY KEY,
        name TEXT NOT NULL,
        category TEXT,
        price REAL
    )
    ''')

    # Create Sales table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS sales (
        id INTEGER PRIMARY KEY,
        product_id INTEGER,
        quantity INTEGER,
        sale_date DATE,
        FOREIGN KEY (product_id) REFERENCES products (id)
    )
    ''')

    # Insert sample data for products
    products_data = [
        (1, 'Laptop', 'Electronics', 1200.0),
        (2, 'Smartphone', 'Electronics', 800.0),
        (3, 'Coffee Maker', 'Appliances', 150.0),
        (4, 'Desk Chair', 'Furniture', 200.0),
        (5, 'Monitor', 'Electronics', 300.0)
    ]
    cursor.executemany('INSERT OR REPLACE INTO products VALUES (?, ?, ?, ?)', products_data)

    # Insert sample data for sales
    sales_data = [
        (1, 1, 5, '2023-01-10'),
        (2, 2, 10, '2023-01-12'),
        (3, 3, 2, '2023-01-15'),
        (4, 1, 3, '2023-02-01'),
        (5, 4, 7, '2023-02-05'),
        (6, 5, 4, '2023-02-10'),
        (7, 2, 8, '2023-03-01')
    ]
    cursor.executemany('INSERT OR REPLACE INTO sales VALUES (?, ?, ?, ?)', sales_data)

    conn.commit()
    conn.close()
    print("Sample database 'data.db' initialized successfully.")

if __name__ == "__main__":
    init_db()
