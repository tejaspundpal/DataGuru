# SQL Query Optimization — Team Guide

## Overview
This guide covers SQL performance optimization techniques used by our data engineering team for Oracle, SQL Server, and Snowflake environments.

---

## 1. Reading Execution Plans

Before optimizing any query, always check the execution plan first.

**Oracle:**
```sql
EXPLAIN PLAN FOR
SELECT * FROM fact_orders fo JOIN dim_customer dc ON fo.customer_id = dc.customer_id;

SELECT * FROM TABLE(DBMS_XPLAN.DISPLAY);
```

**SQL Server:**
```sql
SET STATISTICS IO ON;
SET STATISTICS TIME ON;
-- Run your query here
```

**Snowflake:**
```sql
-- After running the query, use Query Profile in Snowflake UI
-- or check QUERY_HISTORY view
SELECT * FROM TABLE(INFORMATION_SCHEMA.QUERY_HISTORY()) LIMIT 10;
```

**Key things to look for in execution plan:**
- Full Table Scan (`TABLE ACCESS FULL`) on large tables — often indicates missing index
- Nested Loop on large datasets — should be Hash Join for large tables
- High cost/cardinality estimate mismatch — indicates stale statistics
- Sort operations — check if ORDER BY is necessary or if index can eliminate it

---

## 2. Common Query Anti-Patterns and Fixes

### Anti-Pattern 1: SELECT *
**Problem:** Fetches all columns, increases I/O, breaks when table schema changes
```sql
-- BAD
SELECT * FROM fact_orders;

-- GOOD
SELECT order_id, customer_id, order_amount, order_date FROM fact_orders;
```

### Anti-Pattern 2: Function on Indexed Column in WHERE Clause
**Problem:** Applying a function to an indexed column prevents index usage
```sql
-- BAD (index on order_date is not used)
SELECT * FROM fact_orders WHERE YEAR(order_date) = 2024;

-- GOOD (index on order_date is used)
SELECT * FROM fact_orders WHERE order_date BETWEEN '2024-01-01' AND '2024-12-31';
```

### Anti-Pattern 3: Implicit Type Conversion
**Problem:** Comparing VARCHAR column to integer causes full scan
```sql
-- BAD (customer_id is VARCHAR, this causes implicit cast on every row)
SELECT * FROM dim_customer WHERE customer_id = 12345;

-- GOOD
SELECT * FROM dim_customer WHERE customer_id = '12345';
```

### Anti-Pattern 4: Correlated Subqueries
**Problem:** Executes once per row — extremely slow on large tables
```sql
-- BAD (runs subquery for each row in orders)
SELECT order_id,
       (SELECT customer_name FROM dim_customer dc WHERE dc.customer_id = fo.customer_id) AS name
FROM fact_orders fo;

-- GOOD (single join instead)
SELECT fo.order_id, dc.customer_name
FROM fact_orders fo
JOIN dim_customer dc ON fo.customer_id = dc.customer_id;
```

---

## 3. CTE vs Subquery vs Temp Table

| Option | Use When | Performance Notes |
|---|---|---|
| **CTE** | Readability, recursive queries | May be inlined by optimizer (not always materialized) |
| **Subquery** | Simple one-time use | Same as CTE, optimizer may rewrite |
| **Temp Table** | Result used multiple times, large intermediate result | Materialized — better for complex multi-step logic |
| **Indexed Temp Table** | Temp table joined multiple times | Add index after insert for join performance |

**Temp table example (SQL Server):**
```sql
-- Step 1: Materialize intermediate result
SELECT customer_id, SUM(order_amount) AS total_revenue
INTO #customer_revenue
FROM fact_orders
WHERE order_date >= '2024-01-01'
GROUP BY customer_id;

-- Add index to optimize subsequent join
CREATE INDEX ix_cust_rev ON #customer_revenue (customer_id);

-- Step 2: Join (now uses index)
SELECT dc.customer_name, cr.total_revenue
FROM dim_customer dc
JOIN #customer_revenue cr ON dc.customer_id = cr.customer_id;
```

---

## 4. Partition Pruning

When querying partitioned tables, always filter on the partition key to avoid full scans.

**Example (Oracle Range Partition on order_date):**
```sql
-- GOOD — partition pruning kicks in (only scans relevant month partition)
SELECT * FROM fact_orders PARTITION (P_2024_01)
WHERE order_date BETWEEN '2024-01-01' AND '2024-01-31';

-- BAD — scans all partitions
SELECT * FROM fact_orders WHERE TO_CHAR(order_date, 'YYYY') = '2024';
```

---

## 5. Statistics and Stale Data

**Oracle:**
```sql
-- Gather table statistics
EXEC DBMS_STATS.GATHER_TABLE_STATS('SCHEMA_NAME', 'FACT_ORDERS');
-- Gather schema statistics
EXEC DBMS_STATS.GATHER_SCHEMA_STATS('SCHEMA_NAME');
```

**SQL Server:**
```sql
UPDATE STATISTICS dbo.fact_orders;
-- Or rebuild all stats on database
EXEC sp_updatestats;
```

Stale statistics are the #1 cause of bad execution plans. Always update after large data loads (>10% of rows changed).

---

## 6. Snowflake-Specific Optimization

- Use **Clustering Keys** on frequently filtered columns in large tables (>500GB)
- Prefer **RESULT_CACHE** for repeated identical queries
- Use **COPY INTO** instead of INSERT for bulk loading
- Avoid `SELECT COUNT(DISTINCT col)` on large tables — use `APPROX_COUNT_DISTINCT` for estimates
- Use **Multi-cluster warehouses** for concurrent workloads, not a single large warehouse
