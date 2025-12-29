"""
KPI Aggregation Job
Runs every 1-5 minutes to pre-calculate KPIs and store in kpi_summary table.
This improves dashboard performance by avoiding real-time calculations.
"""

import sqlite3
from datetime import datetime
import logging
import schedule
import time

# Configuration
DATABASE_PATH = "test.db"
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def calculate_and_store_kpis():
    """Calculate today's KPIs and store in kpi_summary table."""
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        # Calculate today's KPIs
        today_revenue_query = """
            SELECT COALESCE(SUM(amount), 0) as total_revenue
            FROM orders 
            WHERE date(order_date) = date('now', 'localtime')
        """
        
        today_orders_query = """
            SELECT COUNT(*) as total_orders
            FROM orders 
            WHERE date(order_date) = date('now', 'localtime')
        """
        
        today_users_query = """
            SELECT COUNT(DISTINCT user_id) as active_users
            FROM orders 
            WHERE date(order_date) = date('now', 'localtime')
        """
        
        # Conversion rate calculation
        conversion_query = """
            SELECT 
                CASE 
                    WHEN v.total_visits > 0 
                    THEN ROUND((o.total_orders * 100.0 / v.total_visits), 2)
                    ELSE 0 
                END as conversion_rate
            FROM 
                (SELECT COUNT(*) as total_orders FROM orders 
                 WHERE date(order_date) = date('now', 'localtime')) o,
                (SELECT COUNT(DISTINCT user_id) as total_visits FROM visits 
                 WHERE date(visit_date) = date('now', 'localtime')) v
        """
        
        # Execute queries
        total_revenue = cursor.execute(today_revenue_query).fetchone()[0]
        total_orders = cursor.execute(today_orders_query).fetchone()[0]
        active_users = cursor.execute(today_users_query).fetchone()[0]
        
        try:
            conversion_rate = cursor.execute(conversion_query).fetchone()[0]
        except:
            # Fallback if visits table doesn't exist
            conversion_rate = (total_orders / max(active_users, 1)) * 100 if active_users > 0 else 0
        
        # Insert or update today's KPI summary
        upsert_query = """
            INSERT OR REPLACE INTO kpi_summary 
            (id, total_revenue_today, total_orders_today, active_users_today, conversion_rate_today, updated_at)
            VALUES (
                (SELECT id FROM kpi_summary WHERE date(updated_at) = date('now', 'localtime') LIMIT 1),
                ?, ?, ?, ?, datetime('now', 'localtime')
            )
        """
        
        cursor.execute(upsert_query, (total_revenue, total_orders, active_users, conversion_rate))
        conn.commit()
        
        logger.info(f"KPIs updated: Revenue=${total_revenue:.2f}, Orders={total_orders}, Users={active_users}, Conversion={conversion_rate:.2f}%")
        
    except Exception as e:
        logger.error(f"Error calculating KPIs: {e}")
    finally:
        if conn:
            conn.close()

def cleanup_old_kpi_records():
    """Clean up KPI summary records older than 30 days."""
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        cleanup_query = """
            DELETE FROM kpi_summary 
            WHERE updated_at < datetime('now', 'localtime', '-30 days')
        """
        
        cursor.execute(cleanup_query)
        deleted_count = cursor.rowcount
        conn.commit()
        
        if deleted_count > 0:
            logger.info(f"Cleaned up {deleted_count} old KPI records")
            
    except Exception as e:
        logger.error(f"Error cleaning up old KPI records: {e}")
    finally:
        if conn:
            conn.close()

def run_scheduler():
    """Run the KPI aggregation scheduler."""
    logger.info("Starting KPI aggregation scheduler...")
    
    # Schedule KPI calculation every 1 minute
    schedule.every(1).minutes.do(calculate_and_store_kpis)
    
    # Schedule cleanup every day at 2 AM
    schedule.every().day.at("02:00").do(cleanup_old_kpi_records)
    
    # Run initial calculation
    calculate_and_store_kpis()
    
    # Keep running
    while True:
        schedule.run_pending()
        time.sleep(30)  # Check every 30 seconds

if __name__ == "__main__":
    run_scheduler()