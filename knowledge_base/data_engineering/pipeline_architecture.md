# Data Engineering — Pipeline Architecture Guide

## Overview
This document describes our team's standard pipeline architectures, data flow patterns, and technology choices used across production data engineering workloads.

---

## 1. Medallion Architecture (Bronze → Silver → Gold)

Our data warehouse follows the Medallion architecture pattern:

### Bronze Layer (Raw / Landing)
- **Purpose:** Store raw data exactly as received from source systems
- **Storage:** S3 / ADLS in Parquet or CSV format
- **Schema:** Matches source system exactly — no transformations
- **Retention:** 90 days minimum for reprocessing
- **Tool:** Informatica / SFTP / API ingestion scripts

```
Sources → [Informatica / Python Scripts / APIs] → Bronze (S3/ADLS)
- Customer data from Oracle HRMS
- Order data from SQL Server OLTP
- Product catalogs from REST API
- Clickstream from Kafka
```

### Silver Layer (Cleansed / Conformed)
- **Purpose:** Cleansed, deduplicated, conformed data with business logic applied
- **Storage:** Delta Lake / Parquet on S3 / ADLS
- **Transformations:** Data type standardization, deduplication, null handling, SCD2 dimensions
- **Tool:** PySpark / dbt

```
Bronze → [PySpark / dbt Models] → Silver
- Standardize date formats (ISO 8601)
- Remove duplicates on business key
- Apply SCD Type 2 for dimensions
- Handle NULL values per column-level rules
```

### Gold Layer (Business / Analytics-Ready)
- **Purpose:** Aggregated, business-ready datasets for reporting and analytics
- **Storage:** Snowflake / Redshift / Delta Lake
- **Transformations:** Aggregations, KPI calculations, denormalized star schema
- **Consumers:** BI tools (Tableau, Power BI), Data Science, APIs

```
Silver → [dbt / Spark] → Gold
- fact_daily_sales  (grain: date × store × product)
- dim_customer      (SCD2, current flag)
- agg_monthly_revenue (pre-aggregated for dashboards)
```

---

## 2. Batch Pipeline Pattern (Nightly ETL)

### Architecture
```
02:00 AM — Batch Trigger (Cron / Airflow / Control-M)
    ↓
[Extract] — Informatica reads from Oracle OLTP source
    ↓
[Stage] — Land raw data in Bronze (S3 Parquet)
    ↓
[Transform] — PySpark job reads Bronze, applies business logic
    ↓
[Load] — Write to Silver (Delta Lake)
    ↓
[Aggregate] — dbt runs Gold models
    ↓
[Validate] — Data quality checks (Great Expectations / custom SQL)
    ↓
[Notify] — Success/failure Slack + Email alert
```

### Key Design Principles
- **Idempotent:** Re-running the pipeline produces the same result (use MERGE/upsert, not INSERT)
- **Partitioned:** All tables partitioned by date for efficient incremental loads
- **Watermarked:** Track last successful load timestamp in `batch_control` table
- **Observable:** Every step logs start time, end time, row counts, and error counts

### Watermark Pattern for Incremental Loads
```sql
-- Before extract: get last watermark
SELECT MAX(last_loaded_ts) FROM batch_control WHERE pipeline = 'orders_daily';
-- Returns: 2024-01-14 02:00:00

-- Extract only new/changed rows
SELECT * FROM source.orders WHERE modified_date > '2024-01-14 02:00:00';

-- After load: update watermark
UPDATE batch_control
SET last_loaded_ts = CURRENT_TIMESTAMP, status = 'SUCCESS', row_count = 45230
WHERE pipeline = 'orders_daily';
```

---

## 3. Data Warehouse Schema Design

### Star Schema (Team Standard)

```
                    ┌──────────────┐
                    │ dim_date     │
                    │ date_key (PK)│
                    └──────┬───────┘
                           │
┌──────────────┐    ┌──────┴───────┐    ┌──────────────┐
│ dim_customer │    │ fact_orders  │    │ dim_product  │
│ cust_key (PK)│────│ cust_key(FK) │────│ prod_key (PK)│
└──────────────┘    │ prod_key(FK) │    └──────────────┘
                    │ date_key(FK) │
                    │ store_key(FK)│
                    │ order_amount │
                    │ quantity     │
                    └──────┬───────┘
                           │
                    ┌──────┴───────┐
                    │ dim_store    │
                    │ store_key(PK)│
                    └──────────────┘
```

### Surrogate Keys
- All dimensions use auto-generated surrogate keys (integer)
- Natural/business key is stored alongside for traceability
- Fact tables reference surrogate keys as foreign keys

### SCD Type 2 Implementation (dim_customer)
```sql
-- Columns for tracking history
customer_key     INT (surrogate PK, auto-increment)
customer_id      VARCHAR (natural key from source)
customer_name    VARCHAR
address          VARCHAR
effective_start  DATE
effective_end    DATE (NULL if current)
is_current       BOOLEAN (TRUE if current record)
```

---

## 4. Error Handling & Recovery

### Pipeline Failure Categories

| Category | Example | Recovery Action |
|---|---|---|
| Source unavailable | Oracle DB down | Retry 3 times with 10-min intervals, then alert |
| Data quality failure | 50% NULL in required column | Halt pipeline, alert, do not load |
| Infrastructure failure | Spark executor OOM | Increase resources, re-run from failed step |
| Target lock | Deadlock on fact table | Kill blocking session, re-run |
| Schema drift | New column added to source | Alert, update mapping, re-run |

### Checkpoint/Restart Pattern
```python
# Save checkpoint after each major step
def save_checkpoint(pipeline_name, step, status):
    db.execute("""
        INSERT INTO pipeline_checkpoints (pipeline, step, status, ts)
        VALUES (?, ?, ?, CURRENT_TIMESTAMP)
    """, (pipeline_name, step, status))

# On restart, resume from last successful checkpoint
def get_last_checkpoint(pipeline_name):
    return db.query("""
        SELECT step FROM pipeline_checkpoints
        WHERE pipeline = ? AND status = 'SUCCESS'
        ORDER BY ts DESC LIMIT 1
    """, (pipeline_name,))
```

---

## 5. Technology Stack Summary

| Layer | Tool | Purpose |
|---|---|---|
| Orchestration | Apache Airflow / Control-M / Cron | Schedule and monitor pipelines |
| Extract | Informatica PowerCenter | RDBMS extraction, CDC |
| Extract | Python + Requests / SFTP | API and file-based extraction |
| Transform (Batch) | PySpark on Databricks | Heavy transformations (>100M rows) |
| Transform (SQL) | dbt | SQL-based transformations, testing |
| Storage | S3 / ADLS + Delta Lake | Data lake storage (Bronze/Silver) |
| Data Warehouse | Snowflake / Redshift | Gold layer, analytics serving |
| Data Quality | Great Expectations / custom SQL | Validation checks |
| Monitoring | Slack + PagerDuty + Airflow alerts | Pipeline health monitoring |
