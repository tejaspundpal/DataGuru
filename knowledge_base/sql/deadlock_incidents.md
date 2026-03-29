# SQL Deadlock Incidents — Incident Reports & Resolutions

## Overview
This document contains historical deadlock incidents, root cause analyses, and resolutions for reference by the data engineering and DBA teams.

---

## Incident INC-2024-0112 — Deadlock During Orders ETL (SQL Server)

**Date:** January 12, 2024
**Reported By:** Automated Monitor Alert / Tejas
**Severity:** P2 (Pipeline delayed by 3 hours)
**Ticket:** JIRA-DE-1892

**Environment:** SQL Server 2019, `DWH_PROD` database

### Symptom
The nightly `wf_fact_orders_load` workflow failed at 02:14 AM. Session log showed:
```
WRT_8333 [Database Error: Deadlock found when trying to get lock;
try restarting transaction. Error Code: 1205]
```
Target table: `dbo.FACT_ORDERS`

### Root Cause Analysis
The Informatica session was performing a bulk INSERT into `FACT_ORDERS` while a reporting query (SSRS report triggered at 02:00 AM) was running a long `SELECT` with `NOLOCK` hint NOT applied. SQL Server deadlock graph showed:
- Process A (ETL): Page lock on clustered index — waiting for Process B's shared lock to release
- Process B (SSRS Report): Shared lock on same page — waiting for Process A's insert lock

### Resolution
1. Immediately: Killed the SSRS report connection from SQL Server Activity Monitor
2. Re-ran the Informatica workflow manually at 02:45 AM — succeeded
3. Short-term: Added `WITH (NOLOCK)` to all SSRS reports reading FACT_ORDERS during ETL window
4. Long-term: Shifted ETL run window from 02:00 AM to 00:00 AM to avoid overlap with automated reports

### Learnings
- Define ETL blackout windows — no report queries during batch load hours
- Add `SET DEADLOCK_PRIORITY LOW` to non-critical sessions so ETL always wins in deadlock resolution
- Enable SQL Server deadlock trace flag 1222 for better graph output

---

## Incident INC-2024-0318 — Deadlock on Customer Dimension Update (Oracle)

**Date:** March 18, 2024
**Reported By:** Priya (Pipeline Monitoring)
**Severity:** P1 (Customer data not updated, downstream reports impacted)
**Ticket:** JIRA-DE-2105

**Environment:** Oracle 19c, `DWH_PROD` schema

### Symptom
`wf_dim_customer_scd2` workflow ran for 4.5 hours (usual: 45 minutes) then aborted with:
```
ORA-00060: Deadlock detected while waiting for resource
```
Target table: `DIM_CUSTOMER`

### Root Cause Analysis
Two Informatica sessions were running concurrently against `DIM_CUSTOMER`:
- Session A: SCD Type 2 UPDATE (closing expired records — updating `EFFECTIVE_END_DATE`)
- Session B: New record INSERT (from a different workflow triggered by mistake)

Session B was inserting rows while Session A was updating the same partition, causing a row-level lock deadlock.

The duplicate trigger was caused by a developer manually triggering the `wf_dim_customer_new` workflow while the nightly batch was still running.

### Resolution
1. Re-ran only the SCD2 session with a recovery flag set
2. Removed manual trigger permissions from non-admin users in Workflow Monitor
3. Added `sequence_check` step at workflow start to abort if another instance is running:
   ```sql
   SELECT COUNT(*) FROM BATCH_CONTROL
   WHERE WORKFLOW_NAME = 'wf_dim_customer_scd2' AND STATUS = 'RUNNING';
   ```
4. Implemented row-level locking strategy: `SELECT ... FOR UPDATE SKIP LOCKED` in Oracle

### Corrective Action
- Documented concurrent workflow prevention SOP
- Set "Allow Concurrent Runs" = OFF in both dimension workflows

---

## Incident INC-2024-0607 — Frequent Deadlocks on FACT_SALES (Snowflake)

**Date:** June 7, 2024
**Reported By:** Automated Slack Alert
**Severity:** P3 (Non-blocking, but retries causing data duplication risk)

### Symptom
Multiple dbt jobs running in parallel reported `TRANSACTION ABORTED` errors intermittently on `FACT_SALES` table.

### Root Cause
Snowflake uses optimistic concurrency. Multiple dbt models were writing to the same target table simultaneously (parallel job execution in dbt). Snowflake transaction collision occurred when two writes happened to the same micro-partition.

### Resolution
1. Added `+post-hook` in dbt to run models sequentially on the FACT_SALES dependency chain
2. Used `incremental` materialization with `unique_key` to allow safe merge operations
3. Increased dbt `threads` only for read-heavy models, not write models: `threads: 2` in profiles.yml

---

## Deadlock Prevention Checklist

| Scenario | Prevention |
|---|---|
| ETL + Reports overlap | Define ETL blackout windows |
| Concurrent ETL workflows | Disable concurrent run, add batch lock |
| Long-running transactions | Reduce commit interval, use smaller batches |
| Index contention | Use ROWLOCK hints, check index fragmentation |
| Snowflake parallel writes | Use sequential deps in dbt, avoid parallel writes to same table |
