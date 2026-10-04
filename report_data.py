import sqlite3
import json

DB_NAME = "report.db"

def getReportData():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("""
        SELECT COUNT(*) AS total_orders
        FROM orders
    """)
    total_orders = cursor.fetchone()["total_orders"]

    cursor.execute("""
        SELECT ROUND(SUM(amount), 2) AS total_revenue
        FROM orders
    """)
    total_revenue = cursor.fetchone()["total_revenue"]

    cursor.execute("""
        SELECT
            product,
            COUNT(*) AS order_count,
            ROUND(SUM(amount), 2) AS revenue
        FROM orders
        GROUP BY product
        ORDER BY revenue DESC
        LIMIT 5
    """)
    top_products = [dict(row) for row in cursor.fetchall()]

    cursor.execute("""
        SELECT
            created_at,
            COUNT(*) AS order_count
        FROM orders
        WHERE created_at >= date('now', '-6 days')
        GROUP BY created_at
        ORDER BY created_at
    """)
    orders_per_day = [dict(row) for row in cursor.fetchall()]

    cursor.execute("""
        SELECT *
        FROM orders
        ORDER BY created_at DESC, id DESC
    """)
    all_orders = [dict(row) for row in cursor.fetchall()]

    conn.close()

    return {
        "total_orders": total_orders,
        "total_revenue": total_revenue,
        "top_products": top_products,
        "orders_per_day": orders_per_day,
        "all_orders": all_orders
    }


if __name__ == "__main__":
    report = getReportData()
    print(json.dumps(report, indent=2))
