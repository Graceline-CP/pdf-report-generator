import sqlite3
from datetime import datetime
from pathlib import Path
from playwright.sync_api import sync_playwright

DB_NAME = "report.db"
OUTPUT = Path("reports/test.pdf")


def get_report_data():
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
        "all_orders": all_orders
    }


def build_html(data):
    today = datetime.now().strftime("%d %B %Y")

    top_product_rows = ""

    for product in data["top_products"]:
        top_product_rows += f"""
        <tr>
            <td>{product["product"]}</td>
            <td>{product["order_count"]}</td>
            <td>?{product["revenue"]:.2f}</td>
        </tr>
        """

    order_rows = ""

    for order in data["all_orders"]:
        order_rows += f"""
        <tr>
            <td>{order["id"]}</td>
            <td>{order["customer"]}</td>
            <td>{order["product"]}</td>
            <td>?{order["amount"]:.2f}</td>
            <td>{order["created_at"]}</td>
        </tr>
        """

    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">

        <style>
            @page {{
                size: A4;
                margin: 18mm;
            }}

            body {{
                font-family: Arial, sans-serif;
                color: #222;
                font-size: 11px;
            }}

            h1 {{
                margin-bottom: 5px;
            }}

            h2 {{
                margin-top: 25px;
                margin-bottom: 10px;
            }}

            .date {{
                color: #666;
                margin-bottom: 20px;
            }}

            .summary {{
                display: flex;
                gap: 20px;
                margin-bottom: 25px;
            }}

            .card {{
                border: 1px solid #ccc;
                padding: 15px;
                width: 45%;
            }}

            .value {{
                font-size: 20px;
                font-weight: bold;
            }}

            table {{
                width: 100%;
                border-collapse: collapse;
                margin-bottom: 20px;
            }}

            th,
            td {{
                border: 1px solid #ccc;
                padding: 7px;
                text-align: left;
            }}

            th {{
                background: #eee;
            }}

            thead {{
                display: table-header-group;
            }}

            tr {{
                break-inside: avoid;
                page-break-inside: avoid;
            }}
        </style>
    </head>

    <body>

        <h1>Shop Order Report</h1>
        <div class="date">Generated on {today}</div>

        <div class="summary">
            <div class="card">
                <div>Total Orders</div>
                <div class="value">{data["total_orders"]}</div>
            </div>

            <div class="card">
                <div>Total Revenue</div>
                <div class="value">?{data["total_revenue"]:.2f}</div>
            </div>
        </div>

        <h2>Top 5 Products by Revenue</h2>

        <table>
            <thead>
                <tr>
                    <th>Product</th>
                    <th>Orders</th>
                    <th>Revenue</th>
                </tr>
            </thead>

            <tbody>
                {top_product_rows}
            </tbody>
        </table>

        <h2>All Orders</h2>

        <table>
            <thead>
                <tr>
                    <th>ID</th>
                    <th>Customer</th>
                    <th>Product</th>
                    <th>Amount</th>
                    <th>Date</th>
                </tr>
            </thead>

            <tbody>
                {order_rows}
            </tbody>
        </table>

    </body>
    </html>
    """


def generate_pdf():
    data = get_report_data()
    html = build_html(data)

    OUTPUT.parent.mkdir(exist_ok=True)

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(executable_path=r"C:\Program Files\Google\Chrome\Application\chrome.exe")
        page = browser.new_page()

        page.set_content(html)

        page.pdf(
            path=str(OUTPUT),
            format="A4",
            print_background=True
        )

        browser.close()

    print(f"PDF generated: {OUTPUT}")
    print(f"Orders included: {len(data['all_orders'])}")


if __name__ == "__main__":
    generate_pdf()
