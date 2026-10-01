
USE CustomerStarLab;
GO
-- KPI: total customers and average spend
SELECT COUNT(DISTINCT customer_id) AS total_customers,
       AVG(annual_spend) AS average_annual_spend,
       AVG(spending_score) AS average_spending_score
FROM dbo.vw_CustomerStarMining;
-- Average annual spend by region
SELECT region_name, COUNT(*) AS customers, AVG(annual_spend) AS avg_spend
FROM dbo.vw_CustomerStarMining GROUP BY region_name ORDER BY avg_spend DESC;
-- Average score by membership
SELECT membership_name, COUNT(*) AS customers, AVG(spending_score) AS avg_score
FROM dbo.vw_CustomerStarMining GROUP BY membership_name ORDER BY avg_score DESC;
-- Customer detail report
SELECT * FROM dbo.vw_CustomerStarMining ORDER BY annual_spend DESC;
GO
