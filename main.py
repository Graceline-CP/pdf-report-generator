import sqlite3
from datetime import datetime
from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from playwright.sync_api import sync_playwright

from report_data import getReportData

app = FastAPI(title="PDF Report Generator")

DB_NAME = "report.db"
REPORTS_DIR = Path("reports")
CHROME_PATH = r"C:\Program Files\Google\Chrome\Application\chrome.exe"


def init_reports_table():
    conn = sqlite3.connect(DB_NAME)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS reports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            path TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
    """)

    conn.commit()
    conn.close()


init_reports_table()


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


def generate_report(report_id):
    data = getReportData()

    html = build_html(data)

    REPORTS_DIR.mkdir(exist_ok=True)

    output_path = REPORTS_DIR / f"{report_id}.pdf"

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(
            executable_path=CHROME_PATH
        )

        page = browser.new_page()
        page.set_content(html)

        page.pdf(
            path=str(output_path),
            format="A4",
            print_background=True
        )

        browser.close()

    return output_path


@app.post("/reports", status_code=201)
def create_report():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO reports (path, created_at)
        VALUES (?, ?)
    """, ("", datetime.now().isoformat()))

    report_id = cursor.lastrowid

    output_path = generate_report(report_id)

    cursor.execute("""
        UPDATE reports
        SET path = ?
        WHERE id = ?
    """, (str(output_path), report_id))

    conn.commit()
    conn.close()

    return {
        "id": report_id,
        "file": f"/reports/{report_id}/file"
    }


@app.get("/reports/{report_id}")
def get_report(report_id: int):
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row

    report = conn.execute("""
        SELECT id, path, created_at
        FROM reports
        WHERE id = ?
    """, (report_id,)).fetchone()

    conn.close()

    if not report:
        raise HTTPException(status_code=404, detail="Report not found")

    return {
        "id": report["id"],
        "path": report["path"],
        "created_at": report["created_at"],
        "file": f"/reports/{report_id}/file"
    }


@app.get("/reports/{report_id}/file")
def download_report(report_id: int):
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row

    report = conn.execute("""
        SELECT path
        FROM reports
        WHERE id = ?
    """, (report_id,)).fetchone()

    conn.close()

    if not report:
        raise HTTPException(status_code=404, detail="Report not found")

    file_path = Path(report["path"])

    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Report file not found")

    return FileResponse(
        path=file_path,
        media_type="application/pdf",
        filename=f"report-{report_id}.pdf"
    )


@app.get("/health")
def health():
    return {"status": "ok"}
