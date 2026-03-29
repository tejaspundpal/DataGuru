# Data Engineering — Incident History & Root Cause Analysis Log

## Overview
This document maintains a timeline of production incidents in our data engineering pipelines with root cause, impact, and corrective actions taken.

---

## Incident Timeline (2024)

---

### INC-2024-001 — Complete Batch Failure Due to Oracle Source Outage

**Date:** January 8, 2024  |  **Severity:** P1  |  **Duration:** 6 hours  
**Ticket:** JIRA-DE-1801  |  **On-Call:** Tejas

**Impact:** All 12 nightly Informatica workflows failed. No data loaded into DWH. Morning dashboards showed stale data from previous day. Business users raised escalation.

**Root Cause:**
Oracle DBA team performed an unscheduled database migration on the OLTP source at 01:30 AM. TNS listener was down for 4 hours. Our Informatica sessions started at 02:00 AM and could not connect.

**Timeline:**
- 02:00 AM: Workflows triggered, all failed with CMN_1022 (TNS:no listener)
- 02:15 AM: Auto-retry kicked in (3 retries at 10-min intervals) — all failed
- 02:45 AM: PagerDuty alert fired to on-call
- 03:00 AM: On-call identified Oracle migration as cause, contacted DBA team
- 06:00 AM: Oracle listener restored
- 06:30 AM: All workflows re-triggered manually, completed by 08:15 AM

**Corrective Actions:**
1. Established change management communication between DBA and DE teams
2. Added pre-flight connectivity check in Airflow before triggering Informatica
3. Extended retry window from 30 minutes to 2 hours for source connectivity failures

---

### INC-2024-002 — Duplicate Records in dim_customer After SCD2 Bug

**Date:** February 22, 2024  |  **Severity:** P2  |  **Duration:** 2 days to fully fix  
**Ticket:** JIRA-DE-1856

**Impact:** 15,000 duplicate customer records created in `dim_customer`. Reports showed inflated customer counts. Finance team flagged discrepancy.

**Root Cause:**
A code change to `spark_scd2_customer.py` introduced a bug in the MERGE logic. The developer used `customer_name` instead of `customer_id` as the business key in the merge condition. Since multiple customers can share the same name, the SCD2 logic created duplicates.

**Bad Code:**
```python
# WRONG — customer_name is not unique
merge_condition = "target.customer_name = source.customer_name"
```

**Fixed Code:**
```python
# CORRECT — customer_id is the unique business key
merge_condition = "target.customer_id = source.customer_id"
```

**Corrective Actions:**
1. Fixed the merge key and re-ran SCD2 with full reload
2. Added automated DQ check: duplicate count on `customer_id WHERE is_current = TRUE` must be 0
3. Made code review mandatory for any changes to SCD logic
4. Added unit test for SCD2 merge with known test data

---

### INC-2024-003 — Spark OOM Crash on Daily Sales Aggregation

**Date:** February 5, 2024  |  **Severity:** P2  |  **Duration:** 4 hours  
**Ticket:** JIRA-DE-1934

**Impact:** Daily sales aggregation job failed. Gold layer `fact_daily_sales` not updated. Tableau dashboards showed missing current-day data.

**Root Cause:** Data volume increased from 500M to 800M rows after Black Friday event. Default 200 shuffle partitions created partitions too large for executor memory (16GB).

*Full details in: spark_pyspark/oom_incidents.md*

**Corrective Actions:**
1. Increased shuffle partitions to 2000
2. Enabled AQE (Adaptive Query Execution)
3. Added volume monitoring alert: if source row count > 150% of daily average, increase cluster resources automatically

---

### INC-2024-004 — Cron Job Silent Failure — No Logs, No Alerts

**Date:** April 3, 2024  |  **Severity:** P3  |  **Duration:** 3 days unnoticed  
**Ticket:** JIRA-DE-2070

**Impact:** The SFTP file arrival check script (`check_sftp_files.sh`) had been silently failing for 3 days. Upstream vendor files were not detected, causing delayed data loads.

**Root Cause:**
A server OS upgrade changed the Python path from `/usr/bin/python3` to `/usr/local/bin/python3`. The cron job used the old path. Since stdout/stderr were redirected to `/dev/null` (bad practice), no error was logged.

**Corrective Actions:**
1. Changed all cron scripts to log output to files (never `/dev/null`)
2. Added `|| echo "FAILED" | mail` fallback to all cron entries
3. Created monitoring cron that checks if expected log files were created today
4. Documented in cron SOP: always use full path and source `.bashrc`

*Full details in: unix/cron_job_sop.md*

---

### INC-2024-005 — SQL Deadlock During ETL + Report Overlap

**Date:** January 12, 2024  |  **Severity:** P2  |  **Duration:** 3 hours  
**Ticket:** JIRA-DE-1892

**Impact:** Nightly orders ETL delayed by 3 hours due to deadlock with an SSRS report query.

*Full details in: sql/deadlock_incidents.md*

---

### INC-2024-006 — Schema Drift — New Column Broke Informatica Mapping

**Date:** June 15, 2024  |  **Severity:** P2  |  **Duration:** 1 day  
**Ticket:** JIRA-DE-2267

**Impact:** The `wf_customer_load` workflow failed because the source Oracle table added a new column `LOYALTY_TIER VARCHAR2(20)`. Informatica mapping did not include this column, and the Source Qualifier `SELECT *` now returned an extra column causing port mismatch.

**Root Cause:**
- Application team added `LOYALTY_TIER` column without notifying the DE team
- Informatica mapping used `SELECT *` in Source Qualifier override — fragile to schema changes

**Corrective Actions:**
1. Changed all Source Qualifier SQL overrides to explicitly list columns (never `SELECT *`)
2. Added weekly schema drift detection script:
   ```sql
   -- Compare current table DDL vs last known DDL stored in metadata table
   SELECT column_name FROM ALL_TAB_COLUMNS WHERE table_name = 'CUSTOMERS'
   MINUS
   SELECT column_name FROM metadata.known_columns WHERE table_name = 'CUSTOMERS';
   ```
3. Established bi-weekly sync meeting with application team on schema changes

---

### INC-2024-007 — Data Quality Failure — 40% NULLs in customer_email

**Date:** August 20, 2024  |  **Severity:** P3  |  **Duration:** Same day  
**Ticket:** JIRA-DE-2401

**Impact:** Marketing team's email campaign targeted NULL email addresses, causing bounce rate spike.

**Root Cause:** Source system migration made `email` field optional. Previous system had it mandatory. No DQ check was in place for NULL percentage on `customer_email`.

**Corrective Actions:**
1. Added DQ rule: `NULL% on customer_email > 10% → WARNING, > 30% → FAIL`
2. Implemented email validation regex in Silver transformation
3. Added `email_valid` boolean flag column for downstream consumers

---

## Incident Summary Dashboard

| Quarter | P1 | P2 | P3 | Total | Most Common Cause |
|---|---|---|---|---|---|
| Q1 2024 | 1 | 3 | 1 | 5 | Source connectivity, schema issues |
| Q2 2024 | 0 | 2 | 2 | 4 | Cron/scheduling, permission issues |
| Q3 2024 | 0 | 1 | 2 | 3 | Data quality, volume spikes |
| Q4 2024 | 0 | 0 | 1 | 1 | Minor config drift |

**Trend:** P1 incidents reduced to 0 after Q1 due to pre-flight checks and change management process.
