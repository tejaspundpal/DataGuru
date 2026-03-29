# SQL Indexing — SOP & Best Practices

## Overview
This document defines our team's standards for creating, maintaining, and dropping indexes on DWH and operational database tables.

---

## When to Create an Index

Create an index when:
1. A column appears frequently in `WHERE`, `JOIN ON`, or `ORDER BY` clauses
2. A query doing a full table scan on a large table (>1M rows) using that column
3. A column used in GROUP BY on fact tables with millions of rows
4. A column used as a lookup key in Informatica or dbt transformations

**Do NOT create an index when:**
- Table has fewer than 10,000 rows (full scan is faster due to overhead)
- Column has very low cardinality (e.g., a STATUS column with only 3 distinct values — unless combined index)
- Table has very high INSERT/UPDATE/DELETE rate (indexes slow down DML operations)

---

## Index Types — When to Use What

### 1. Clustered Index (SQL Server) / Primary Index (Oracle)
- Only ONE per table
- Physically orders the data on disk
- **Use on:** Primary key columns or the most common query filter column (e.g., `order_date` on fact table if you mostly query by date range)

```sql
-- SQL Server: Create clustered index on order_date
CREATE CLUSTERED INDEX ix_fact_orders_date ON dbo.FACT_ORDERS (ORDER_DATE);
```

### 2. Non-Clustered Index
- Multiple allowed per table
- Separate structure that points back to the row
- **Use on:** Columns used in WHERE/JOIN but not the PK

```sql
CREATE NONCLUSTERED INDEX ix_fact_orders_customer ON dbo.FACT_ORDERS (CUSTOMER_ID);
```

### 3. Covering Index (Include Columns)
- Non-clustered index that includes all columns needed by a specific query
- Eliminates the need for a "key lookup" back to the base table
- **Use when:** A specific query fetches both a filter column and a few output columns

```sql
-- Query: SELECT order_id, order_amount FROM fact_orders WHERE customer_id = ?
-- Covering index that avoids table lookup:
CREATE NONCLUSTERED INDEX ix_cov_customer_orders
ON dbo.FACT_ORDERS (CUSTOMER_ID)
INCLUDE (ORDER_ID, ORDER_AMOUNT);
```

### 4. Composite Index
- Index on multiple columns
- **Column order matters** — put the most selective column first
- Matches queries that filter on leading columns

```sql
-- Useful for: WHERE region = 'WEST' AND order_date = '2024-01-01'
CREATE INDEX ix_fact_orders_region_date ON FACT_ORDERS (REGION, ORDER_DATE);
```

### 5. Bitmap Index (Oracle)
- Extremely efficient for low-cardinality columns (STATUS, GENDER, REGION with few values)
- Never use on OLTP tables with concurrent DML — causes lock contention
- **Ideal for DWH read-only fact tables**

```sql
CREATE BITMAP INDEX bx_fact_orders_status ON FACT_ORDERS (STATUS);
```

---

## Index Maintenance SOP

### Fragmentation Thresholds (SQL Server)

| Fragmentation % | Action |
|---|---|
| < 10% | No action needed |
| 10% – 30% | `REORGANIZE` index (online, low impact) |
| > 30% | `REBUILD` index (more resource-intensive, can be done offline or online) |

```sql
-- Check fragmentation
SELECT
    OBJECT_NAME(ips.object_id) AS table_name,
    i.name AS index_name,
    ips.avg_fragmentation_in_percent
FROM sys.dm_db_index_physical_stats(DB_ID(), NULL, NULL, NULL, 'SAMPLED') ips
JOIN sys.indexes i ON ips.object_id = i.object_id AND ips.index_id = i.index_id
WHERE ips.avg_fragmentation_in_percent > 10
ORDER BY ips.avg_fragmentation_in_percent DESC;

-- Reorganize (online, no lock)
ALTER INDEX ix_fact_orders_customer ON dbo.FACT_ORDERS REORGANIZE;

-- Rebuild (locks table briefly by default)
ALTER INDEX ix_fact_orders_customer ON dbo.FACT_ORDERS REBUILD;

-- Rebuild ONLINE (SQL Server Enterprise only)
ALTER INDEX ix_fact_orders_customer ON dbo.FACT_ORDERS REBUILD WITH (ONLINE = ON);
```

### Oracle Index Rebuild SOP
```sql
-- Check index status
SELECT INDEX_NAME, STATUS, BLEVEL, LEAF_BLOCKS
FROM DBA_INDEXES
WHERE TABLE_NAME = 'FACT_ORDERS';

-- Rebuild index
ALTER INDEX FACT_ORDERS_CUSTOMER_IDX REBUILD ONLINE;

-- Coalesce (less CPU, online, for fragmented segments)
ALTER INDEX FACT_ORDERS_CUSTOMER_IDX COALESCE;
```

### Scheduled Maintenance
- Run fragmentation check every Sunday 01:00 AM (cron job: `sql_index_maintenance.sh`)
- Rebuild all indexes with >30% fragmentation after large monthly data loads
- Update statistics after any rebuild: `UPDATE STATISTICS dbo.FACT_ORDERS`

---

## Dropping Unused Indexes

Run this monthly to find indexes with 0 or very low usage (SQL Server):
```sql
SELECT
    OBJECT_NAME(i.object_id) AS table_name,
    i.name AS index_name,
    us.user_seeks,
    us.user_scans,
    us.user_lookups,
    us.user_updates
FROM sys.indexes i
LEFT JOIN sys.dm_db_index_usage_stats us
    ON i.object_id = us.object_id AND i.index_id = us.index_id AND us.database_id = DB_ID()
WHERE OBJECT_NAME(i.object_id) NOT LIKE 'sys%'
  AND i.type_desc <> 'HEAP'
  AND ISNULL(us.user_seeks, 0) + ISNULL(us.user_scans, 0) + ISNULL(us.user_lookups, 0) = 0
ORDER BY us.user_updates DESC;
```

**Always backup index DDL before dropping.** Never drop primary key or unique constraint indexes.
