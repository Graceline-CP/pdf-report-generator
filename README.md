# PDF Report Generator

A FastAPI application that queries order data from SQLite, aggregates it with SQL, generates a multi-page PDF report using Playwright and Chrome, stores the generated PDF on disk, and serves it through an API download link.

## Dataset

This project uses the **little shop** dataset required by the assignment.

The SQLite database contains an `orders` table with:

- `id`
- `customer`
- `product`
- `amount`
- `created_at`

The seed script generates 200 random orders using six products and dates from the last 30 days.

## Project Structure

```text
pdf-report-generator/
├── main.py
├── report_data.py
├── generate_pdf.py
├── seed.py
├── report.db
├── reports/
├── pdf-report-screenshot.png
├── requirements.txt
└── .gitignore

report.db and generated PDFs are excluded from Git because they are generated artifacts.
Setup
Install the Python dependencies:
py -m pip install -r requirements.txt

Playwright is used for PDF rendering.
The application uses the Chrome installation already available on the system:
C:\Program Files\Google\Chrome\Application\chrome.exe

Seed the Database
Run:
py seed.py

The seed script clears existing orders before inserting 200 new orders.
Running it twice still leaves exactly 200 orders.
Check the Data
Run:
py report_data.py

The report data contains:
1. Total number of orders
2. Total revenue
3. Top 5 products by revenue
4. Orders per day for the last 7 days
Aggregation SQL
Total orders
SELECT COUNT(*) AS total_orders
FROM orders;

Total revenue
SELECT ROUND(SUM(amount), 2) AS total_revenue
FROM orders;

Top 5 products by revenue
SELECT
    product,
    COUNT(*) AS order_count,
    ROUND(SUM(amount), 2) AS revenue
FROM orders
GROUP BY product
ORDER BY revenue DESC
LIMIT 5;

Orders per day for the last 7 days
SELECT
    created_at,
    COUNT(*) AS order_count
FROM orders
WHERE created_at >= date('now', '-6 days')
GROUP BY created_at
ORDER BY created_at;

Generate a PDF Directly
Run:
py generate_pdf.py

This creates:
reports/test.pdf

The report contains the summary, top 5 products, and all 200 orders.
Run the API
Start FastAPI:
py -m uvicorn main:app --reload

Health check:
Invoke-RestMethod -Uri "http://localhost:8000/health"

Expected:
{"status":"ok"}

Generate a Report Through the API
Send:
$report = Invoke-WebRequest `
    -Method Post `
    -Uri "http://localhost:8000/reports" `
    -UseBasicParsing

$report.StatusCode
$report.Content

The first generation returns a report ID and file link.
Example:
{
    "id": 3,
    "file": "/reports/3/file"
}

Download the PDF
Use the returned report ID:
Invoke-WebRequest `
    -Uri "http://localhost:8000/reports/3/file" `
    -OutFile "downloaded-report.pdf" `
    -UseBasicParsing

The downloaded file is a real PDF that can be opened in a PDF viewer.
Get Report Information
Invoke-RestMethod `
    -Uri "http://localhost:8000/reports/3"

Unknown report IDs return 404.
Idempotency
The POST /reports endpoint checks whether a report has already been generated on the current day.
If a report already exists, another normal request returns the existing report instead of generating another PDF.
Therefore:
First request  → 201 → new report
Second request → 200 → same report

This protects against duplicate report generation caused by repeated clicks or requests.
For example, two normal requests produced the same report ID during testing.
Using:
POST /reports?force=true

bypasses the idempotency check and generates a new report with a new ID.
Stage 4 Note
The report-generation pipeline currently runs directly inside the API request:
SQL query
    ↓
Build HTML
    ↓
Playwright
    ↓
PDF
    ↓
Save to disk
    ↓
Database record
    ↓
Return file link

For a larger report or many simultaneous users, the PDF generation step would be a good candidate for moving to a background job.
Report Screenshot
pdf-report-screenshot.png
The generated PDF report is shown below:
 
Run Everything
From a fresh project setup:
py seed.py
py report_data.py
py -m uvicorn main:app --reload

Then generate a report through:
POST /reports

and download it through:
GET /reports/{id}/file

Technologies
- Python
- FastAPI
- SQLite
- SQL
- Playwright
- Google Chrome
- Git / GitHub
Assignment
FlyRank Internship — Backend Track — Week 4 — Assignment A8
Stages completed:
- Stage 0: Setup
- Stage 1: Seeded report database
- Stage 2: SQL aggregation
- Stage 3: HTML to PDF
- Stage 4: Generate and serve reports
- Stage 5: Idempotent report generation
- Stage 6: Publishing and documentation