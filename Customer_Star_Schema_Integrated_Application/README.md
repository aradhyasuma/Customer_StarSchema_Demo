# Customer Star Schema Integrated Application

## Purpose
A runnable local customer analytics application that demonstrates:
- relational source customer data
- Star Schema fact and dimensions
- ETL refresh from source table to the star schema
- web application integration
- dashboard filters, KPI cards, charts and CSV report export
- adding a customer from the UI

## Requirements
Python 3.9+; standard library only. No pip packages required.

## Run on Windows
1. Extract the ZIP file.
2. Open Command Prompt in the extracted `Customer_Star_Schema_Integrated_Application` folder.
3. Run:
   `python app/server.py`
4. Open `http://127.0.0.1:8000` in your browser.
5. Use Region and Membership filters, download the CSV report, or add a customer.
6. Click **Run ETL / Refresh** to refresh fact/dimension data.

Stop with Ctrl+C.

## Project flow
Customer Source → ETL refresh → Star Schema → Python web application → Dashboard / Report

## Database
The app initializes `customer_analytics.db` in the project root and seeds it from `data/customers.csv` on first run.
Fact grain: one customer spending snapshot per load date.
Dimensions: Customer, Region, Channel, Membership, Date.
The UI queries the star schema joins; it does not query the source CSV directly.

## SQL Server
`sqlserver/01_create_star_schema.sql` builds an equivalent SQL Server star schema in SSMS. The web app itself uses SQLite to remain dependency-free; see `docs/SQLSERVER_DEPLOYMENT.md` for the boundary and SQL Server deployment note.

## Teaching note
Sample data is synthetic. Spending behavior is generated from spending score; do not use spending_score as a predictor for spending_behavior in a predictive classification experiment because it leaks the target construction.
