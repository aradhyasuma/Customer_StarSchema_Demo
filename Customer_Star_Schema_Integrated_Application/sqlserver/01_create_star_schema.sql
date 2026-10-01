
-- Customer Star Schema — Microsoft SQL Server deployment script
IF DB_ID('CustomerStarLab') IS NULL CREATE DATABASE CustomerStarLab;
GO
USE CustomerStarLab;
GO
DROP VIEW IF EXISTS dbo.vw_CustomerStarMining;
DROP TABLE IF EXISTS dbo.FactCustomerSpending;
DROP TABLE IF EXISTS dbo.DimDate;
DROP TABLE IF EXISTS dbo.DimMembership;
DROP TABLE IF EXISTS dbo.DimChannel;
DROP TABLE IF EXISTS dbo.DimRegion;
DROP TABLE IF EXISTS dbo.DimCustomer;
DROP TABLE IF EXISTS dbo.CustomerSource;
GO
CREATE TABLE dbo.CustomerSource(
 customer_id VARCHAR(10) PRIMARY KEY, name VARCHAR(80) NOT NULL,
 age INT NOT NULL, annual_income DECIMAL(12,2) NULL,
 region VARCHAR(20) NOT NULL, channel VARCHAR(20) NOT NULL,
 membership VARCHAR(20) NOT NULL, tenure_years INT NOT NULL,
 spending_score DECIMAL(5,1) NOT NULL, annual_spend DECIMAL(12,2) NOT NULL,
 spending_behavior VARCHAR(10) NOT NULL
);
GO
INSERT INTO dbo.CustomerSource VALUES
('C0001','Customer 01','30','110752','West','Store','Basic','9','68.7','1228.5','Medium'),
('C0002','Customer 02','34','98638','North','Store','Basic','7','56.3','1061.5','Medium'),
('C0003','Customer 03','19','57115','South','Online','Gold','4','51.2','876.0','Medium'),
('C0004','Customer 04','64','93099','North','Online','Silver','7','44.8','730.0','Medium'),
('C0005','Customer 05','46','35023','East','Mobile','Silver','9','15.6','710.0','Low'),
('C0006','Customer 06','44','42777','South','Mobile','Gold','10','48.0','1144.0','Medium'),
('C0007','Customer 07','58','36118','West','Online','Gold','9','33.7','916.5','Low'),
('C0008','Customer 08','47','82040','West','Mobile','Basic','2','52.4','1102.0','Medium'),
('C0009','Customer 09','52','84939','South','Online','Gold','4','55.7','931.5','Medium'),
('C0010','Customer 10','46','25392','North','Mobile','Silver','12','24.4','750.0','Low'),
('C0011','Customer 11','36','56463','South','Store','Platinum','8','45.7','889.5','Medium'),
('C0012','Customer 12','20','62411','North','Online','Gold','5','53.0','1196.0','Medium'),
('C0013','Customer 13','46','120572','North','Online','Silver','7','68.2','1405.0','Medium'),
('C0014','Customer 14','26','58018','South','Store','Basic','5','38.3','863.5','Low'),
('C0015','Customer 15','61','131005','North','Store','Basic','11','64.8','1346.0','Medium'),
('C0016','Customer 16','42','42079','East','Mobile','Basic','1','16.1','582.5','Low'),
('C0017','Customer 17','50','93521','East','Online','Silver','1','67.3','1455.5','Medium'),
('C0018','Customer 18','31','58819','North','Online','Gold','5','48.3','1042.5','Medium'),
('C0019','Customer 19','50','83076','East','Mobile','Gold','12','67.8','1438.0','Medium'),
('C0020','Customer 20','59','118719','East','Mobile','Platinum','9','94.3','1755.5','High'),
('C0021','Customer 21','32','78262','South','Online','Gold','8','75.4','1617.0','High'),
('C0022','Customer 22','55','143902','North','Store','Basic','12','77.6','1453.0','High'),
('C0023','Customer 23','46','113212','East','Mobile','Silver','2','69.4','1416.0','Medium'),
('C0024','Customer 24','46','109515','West','Mobile','Gold','1','84.7','1766.5','High'),
('C0025','Customer 25','64','69427','East','Online','Basic','5','34.4','700.0','Low'),
('C0026','Customer 26','32','57949','West','Online','Basic','3','39.6','728.0','Low'),
('C0027','Customer 27','50','83590','North','Online','Gold','10','51.6','1047.0','Medium'),
('C0028','Customer 28','26','28113','East','Online','Gold','9','28.4','850.0','Low'),
('C0029','Customer 29','36','93498','North','Mobile','Gold','8','68.2','1138.0','Medium'),
('C0030','Customer 30','37','31461','West','Mobile','Gold','4','38.9','814.5','Low'),
('C0031','Customer 31','40','118845','West','Mobile','Gold','4','80.3','1538.5','High'),
('C0032','Customer 32','21','80649','West','Online','Platinum','4','62.3','1298.5','Medium'),
('C0033','Customer 33','40','30358','West','Online','Silver','9','21.9','595.5','Low'),
('C0034','Customer 34','60','25467','East','Mobile','Silver','4','28.4','528.0','Low'),
('C0035','Customer 35','32','125292','South','Store','Silver','3','71.5','1488.5','High'),
('C0036','Customer 36','35','101698','West','Store','Silver','10','57.4','943.0','Medium'),
('C0037','Customer 37','23','97715','East','Online','Gold','8','84.0','1393.0','High'),
('C0038','Customer 38','34','119154','West','Store','Silver','1','73.1','1217.5','High'),
('C0039','Customer 39','68','34464','West','Mobile','Basic','6','25.4','558.0','Low'),
('C0040','Customer 40','22','62454','East','Online','Basic','2','32.8','579.0','Low');
GO

CREATE TABLE dbo.DimCustomer(
 customer_key INT IDENTITY(1,1) PRIMARY KEY, customer_id VARCHAR(10) NOT NULL UNIQUE,
 name VARCHAR(80) NOT NULL, age INT NOT NULL, annual_income DECIMAL(12,2) NULL, tenure_years INT NOT NULL
);
CREATE TABLE dbo.DimRegion(region_key INT IDENTITY(1,1) PRIMARY KEY, region_name VARCHAR(20) NOT NULL UNIQUE);
CREATE TABLE dbo.DimChannel(channel_key INT IDENTITY(1,1) PRIMARY KEY, channel_name VARCHAR(20) NOT NULL UNIQUE);
CREATE TABLE dbo.DimMembership(membership_key INT IDENTITY(1,1) PRIMARY KEY, membership_name VARCHAR(20) NOT NULL UNIQUE);
CREATE TABLE dbo.DimDate(date_key INT PRIMARY KEY, full_date DATE NOT NULL, calendar_year INT NOT NULL, calendar_month INT NOT NULL);
CREATE TABLE dbo.FactCustomerSpending(
 fact_key BIGINT IDENTITY(1,1) PRIMARY KEY,
 customer_key INT NOT NULL REFERENCES dbo.DimCustomer(customer_key),
 region_key INT NOT NULL REFERENCES dbo.DimRegion(region_key),
 channel_key INT NOT NULL REFERENCES dbo.DimChannel(channel_key),
 membership_key INT NOT NULL REFERENCES dbo.DimMembership(membership_key),
 date_key INT NOT NULL REFERENCES dbo.DimDate(date_key),
 spending_score DECIMAL(5,1) NOT NULL, annual_spend DECIMAL(12,2) NOT NULL,
 spending_behavior VARCHAR(10) NOT NULL,
 CONSTRAINT UQ_FactCustomerDate UNIQUE(customer_key,date_key)
);
GO
INSERT dbo.DimCustomer(customer_id,name,age,annual_income,tenure_years)
SELECT customer_id,name,age,annual_income,tenure_years FROM dbo.CustomerSource;
INSERT dbo.DimRegion(region_name) SELECT DISTINCT region FROM dbo.CustomerSource;
INSERT dbo.DimChannel(channel_name) SELECT DISTINCT channel FROM dbo.CustomerSource;
INSERT dbo.DimMembership(membership_name) SELECT DISTINCT membership FROM dbo.CustomerSource;
INSERT dbo.DimDate VALUES(20260928,'2026-09-28',2026,9);
INSERT dbo.FactCustomerSpending(customer_key,region_key,channel_key,membership_key,date_key,spending_score,annual_spend,spending_behavior)
SELECT c.customer_key,r.region_key,ch.channel_key,m.membership_key,20260928,s.spending_score,s.annual_spend,s.spending_behavior
FROM dbo.CustomerSource s
JOIN dbo.DimCustomer c ON c.customer_id=s.customer_id
JOIN dbo.DimRegion r ON r.region_name=s.region
JOIN dbo.DimChannel ch ON ch.channel_name=s.channel
JOIN dbo.DimMembership m ON m.membership_name=s.membership;
GO
CREATE VIEW dbo.vw_CustomerStarMining AS
SELECT c.customer_id,c.age,c.annual_income,c.tenure_years,
 r.region_name,h.channel_name,m.membership_name,
 f.spending_score,f.annual_spend,f.spending_behavior,d.full_date
FROM dbo.FactCustomerSpending f
JOIN dbo.DimCustomer c ON f.customer_key=c.customer_key
JOIN dbo.DimRegion r ON f.region_key=r.region_key
JOIN dbo.DimChannel h ON f.channel_key=h.channel_key
JOIN dbo.DimMembership m ON f.membership_key=m.membership_key
JOIN dbo.DimDate d ON f.date_key=d.date_key;
GO
-- Application/report query examples
SELECT region_name,COUNT(*) customer_count,AVG(annual_spend) avg_annual_spend
FROM dbo.vw_CustomerStarMining GROUP BY region_name;
SELECT membership_name,COUNT(*) customer_count,AVG(spending_score) avg_score
FROM dbo.vw_CustomerStarMining GROUP BY membership_name;
