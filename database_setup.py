"""
Database Setup Script
Creates SQLite database with sample data for testing the KPI dashboard.
"""

import sqlite3
import os
from datetime import datetime, timedelta
import random

DATABASE_PATH = "test.db"

def create_database():
    """Create database and tables with sample data."""
    
    # Remove existing database if it exists
    if os.path.exists(DATABASE_PATH):
        os.remove(DATABASE_PATH)
        print(f"Removed existing database: {DATABASE_PATH}")
    
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    try:
        # Read and execute SQL setup script
        with open('setup_database.sql', 'r') as f:
            sql_script = f.read()
        
        # Execute the SQL script
        cursor.executescript(sql_script)
        
        # Generate additional realistic sample data
        generate_additional_sample_data(cursor)
        
        conn.commit()
        print(f"✅ Database created successfully: {DATABASE_PATH}")
        
        # Show summary
        show_database_summary(cursor)
        
    except Exception as e:
        print(f"❌ Error creating database: {e}")
        conn.rollback()
    finally:
        conn.close()

def generate_additional_sample_data(cursor):
    """Generate additional realistic sample data."""
    
    # Generate more orders for the past 30 days
    base_date = datetime.now()
    user_ids = list(range(1, 11))  # Users 1-10
    
    for days_back in range(30):
        order_date = base_date - timedelta(days=days_back)
        
        # Random number of orders per day (0-8)
        num_orders = random.randint(0, 8)
        
        for _ in range(num_orders):
            user_id = random.choice(user_ids)
            amount = round(random.uniform(29.99, 399.99), 2)
            
            cursor.execute("""
                INSERT INTO orders (user_id, amount, order_date)
                VALUES (?, ?, ?)
            """, (user_id, amount, order_date.strftime('%Y-%m-%d %H:%M:%S')))
        
        # Generate visits (more visits than orders for realistic conversion rate)
        num_visits = random.randint(num_orders, num_orders + 10)
        
        for _ in range(num_visits):
            # Mix of existing users and new visitor IDs
            user_id = random.choice(user_ids + list(range(11, 21)))
            pages = ['/home', '/products', '/category', '/search', '/checkout']
            page = random.choice(pages)
            session_id = f"sess_{random.randint(1000, 9999)}"
            
            cursor.execute("""
                INSERT INTO visits (user_id, visit_date, page_url, session_id)
                VALUES (?, ?, ?, ?)
            """, (user_id, order_date.strftime('%Y-%m-%d %H:%M:%S'), page, session_id))

def show_database_summary(cursor):
    """Show summary of created database."""
    print("\n📊 Database Summary:")
    print("-" * 40)
    
    # Count records in each table
    tables = ['orders', 'users', 'visits', 'kpi_summary']
    
    for table in tables:
        try:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            print(f"{table.capitalize()}: {count} records")
        except:
            print(f"{table.capitalize()}: Table not found")
    
    # Show today's data
    print("\n📅 Today's Data:")
    print("-" * 40)
    
    cursor.execute("""
        SELECT 
            COUNT(*) as orders,
            COALESCE(SUM(amount), 0) as revenue,
            COUNT(DISTINCT user_id) as users
        FROM orders 
        WHERE date(order_date) = date('now', 'localtime')
    """)
    
    today_data = cursor.fetchone()
    print(f"Orders today: {today_data[0]}")
    print(f"Revenue today: ${today_data[1]:.2f}")
    print(f"Active users today: {today_data[2]}")
    
    # Show date range
    cursor.execute("""
        SELECT 
            MIN(date(order_date)) as first_order,
            MAX(date(order_date)) as last_order
        FROM orders
    """)
    
    date_range = cursor.fetchone()
    print(f"Data range: {date_range[0]} to {date_range[1]}")

if __name__ == "__main__":
    create_database()