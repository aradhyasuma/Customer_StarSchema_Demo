# SQL Server deployment option

The supplied runnable web application uses SQLite so students can run it without a SQL Server driver or server configuration. The equivalent SQL Server Star Schema is supplied in `sqlserver/01_create_star_schema.sql`.

To deploy that schema:
1. Open SSMS and connect to a SQL Server instance.
2. Open and execute `01_create_star_schema.sql`.
3. Inspect `CustomerSource`, `DimCustomer`, `DimRegion`, `DimChannel`, `DimMembership`, `DimDate`, and `FactCustomerSpending`.
4. The script creates `vw_CustomerStarMining` as a flattened application/mining view.

The included Python web app currently connects to its bundled SQLite database. SQL Server deployment script is a parallel schema implementation; it is not an active SQL Server connection adapter. A SQL Server-connected deployment requires selecting and configuring a driver (for example, `pyodbc`) and credentials appropriate to the lab environment. Keep credentials outside source code.
