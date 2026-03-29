# Data Quality — SOP & Validation Rules

## Overview
Data quality checks are mandatory before loading any data into the Silver or Gold layer. This SOP defines the standard checks, thresholds, and escalation process.

---

## 1. Validation Check Categories

### Category A: Row Count Checks
```sql
-- Check: Source vs Target row count difference
-- Threshold: Variance > 5% → FAIL

-- Source row count
SELECT COUNT(*) AS src_count FROM staging.orders_raw;

-- Target row count (after load)
SELECT COUNT(*) AS tgt_count FROM silver.fact_orders WHERE load_date = CURRENT_DATE;

-- Variance check
SELECT
    src.src_count,
    tgt.tgt_count,
    ABS(src.src_count - tgt.tgt_count) * 100.0 / NULLIF(src.src_count, 0) AS variance_pct,
    CASE
        WHEN ABS(src.src_count - tgt.tgt_count) * 100.0 / NULLIF(src.src_count, 0) > 5.0
        THEN 'FAIL'
        ELSE 'PASS'
    END AS check_result
FROM (SELECT COUNT(*) AS src_count FROM staging.orders_raw) src,
     (SELECT COUNT(*) AS tgt_count FROM silver.fact_orders WHERE load_date = CURRENT_DATE) tgt;
```

**Alert Action:** If variance > 5%, halt downstream processing and notify the team.

---

### Category B: Null Checks on Critical Columns
```sql
-- Check: NULL values in mandatory columns
-- Threshold: Any NULL in PK or critical columns → FAIL

SELECT
    'customer_id' AS column_name,
    COUNT(*) AS total_rows,
    SUM(CASE WHEN customer_id IS NULL THEN 1 ELSE 0 END) AS null_count,
    ROUND(SUM(CASE WHEN customer_id IS NULL THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) AS null_pct
FROM silver.dim_customer
WHERE is_current = TRUE;
```

**Mandatory NOT NULL columns per table:**

| Table | NOT NULL Columns |
|---|---|
| fact_orders | order_id, customer_id, order_date, order_amount |
| dim_customer | customer_id, customer_name, effective_start |
| dim_product | product_id, product_name, category |
| fact_daily_sales | date_key, store_key, product_key |

---

### Category C: Duplicate Checks
```sql
-- Check: Duplicates on business key
-- Threshold: Any duplicate → FAIL (for dimensions), WARNING (for facts with known reasons)

SELECT customer_id, COUNT(*) AS dup_count
FROM silver.dim_customer
WHERE is_current = TRUE
GROUP BY customer_id
HAVING COUNT(*) > 1;
```

---

### Category D: Referential Integrity Checks
```sql
-- Check: All FKs in fact table exist in dimension tables
-- Threshold: Orphan rows > 0.1% → WARNING, > 1% → FAIL

SELECT COUNT(*) AS orphan_orders
FROM silver.fact_orders fo
LEFT JOIN silver.dim_customer dc ON fo.customer_id = dc.customer_id AND dc.is_current = TRUE
WHERE dc.customer_id IS NULL;
```

---

### Category E: Freshness Check
```sql
-- Check: Data is from today's expected load (not stale)
-- Threshold: If MAX(load_date) is older than expected schedule → FAIL

SELECT
    MAX(load_date) AS latest_load,
    CASE
        WHEN MAX(load_date) < CURRENT_DATE THEN 'STALE — FAIL'
        ELSE 'FRESH — PASS'
    END AS check_result
FROM silver.fact_orders;
```

---

### Category F: Range / Business Rule Checks
```sql
-- Check: Business rule validations
-- order_amount must be positive
SELECT COUNT(*) AS negative_amounts
FROM silver.fact_orders
WHERE order_amount < 0;

-- order_date must not be in the future
SELECT COUNT(*) AS future_dates
FROM silver.fact_orders
WHERE order_date > CURRENT_DATE;

-- quantity must be between 1 and 10000
SELECT COUNT(*) AS invalid_qty
FROM silver.fact_orders
WHERE quantity <= 0 OR quantity > 10000;
```

---

## 2. Automated DQ Framework

Our team uses a Python-based DQ runner that executes all checks after each load:

```python
DQ_CHECKS = [
    {
        "name": "Row Count Variance",
        "category": "A",
        "query": "SELECT ABS(src - tgt) * 100.0 / NULLIF(src, 0) AS variance FROM ...",
        "threshold": 5.0,
        "severity": "CRITICAL",
    },
    {
        "name": "Null Check — customer_id",
        "category": "B",
        "query": "SELECT SUM(CASE WHEN customer_id IS NULL THEN 1 ELSE 0 END) FROM ...",
        "threshold": 0,
        "severity": "CRITICAL",
    },
    # ... more checks
]
```

Results are logged to `dq_results` table:
```sql
CREATE TABLE dq_results (
    check_id        INT IDENTITY PRIMARY KEY,
    check_name      VARCHAR(200),
    category        VARCHAR(10),
    table_name      VARCHAR(100),
    run_date        DATE,
    result          VARCHAR(10),   -- PASS / FAIL / WARNING
    metric_value    DECIMAL(10,4),
    threshold       DECIMAL(10,4),
    severity        VARCHAR(20)
);
```

---

## 3. Escalation Matrix

| Severity | Action | Notification | Example |
|---|---|---|---|
| CRITICAL | Halt pipeline, do NOT load downstream | Slack #de-alerts + PagerDuty | NULL PKs, >5% row variance |
| HIGH | Load with WARNING flag, investigate same day | Slack #de-alerts + Email | Orphan FK >0.1% |
| MEDIUM | Log warning, investigate within 48 hours | Email to pipeline owner | Unexpected data range |
| LOW | Log only, review in weekly DQ meeting | Dashboard only | Minor format inconsistencies |

---

## 4. Monthly DQ Review Process

1. Run full DQ report across all Silver/Gold tables
2. Review `dq_results` table for trends (increasing null %, new duplicates)
3. Identify systemic source data issues — escalate to source team
4. Update DQ rules based on new columns, tables, or business logic changes
5. Document exceptions in `dq_exceptions` table with owner and expiry date
