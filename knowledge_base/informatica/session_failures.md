# Informatica Session Failures — Runbook & Resolution Guide

## Overview
This document covers common Informatica PowerCenter session failure errors encountered in our pipelines, their root causes, and resolution steps.

---

## Error: CMN_1022 — Unable to Connect to Database

**Error Message:**
```
CMN_1022 [Database driver error... Function Name: Database Open Connection
Failed to connect to database: ORA-12541 TNS:no listener]
```

**Root Cause:**
- Database listener is down or not reachable from the Informatica server
- Incorrect TNS entry in tnsnames.ora
- Firewall blocking port 1521 (Oracle) or 1433 (SQL Server)

**Resolution Steps:**
1. Test the DB connection from the Informatica server using `sqlplus` or `isql`
2. Verify TNS entry: `tnsping <db_alias>`
3. Check that the correct ODBC/native driver is configured in the Informatica connection object
4. Confirm with the DBA that the listener is running: `lsnrctl status`
5. Update the connection object in Workflow Manager → Connections → Relational

**Prevention:**
- Always use service-level DB accounts (not personal) for Informatica connections
- Store connection credentials in parameter files, never hardcoded in mappings

---

## Error: CMN_1076 — Reader or Writer Failed to Initialize

**Error Message:**
```
CMN_1076 [Session task instance [s_m_CUSTOMER_LOAD]: Execution failed]
BLKR_16004 [ERROR: Unexpected condition in block reader]
```

**Root Cause:**
- Source file is missing or path is incorrect (for flat file sources)
- Source table does not exist or user lacks SELECT permission
- Schema mismatch between mapping source and actual table

**Resolution Steps:**
1. For flat file sources: verify the file path and filename match the session configuration
2. For relational sources: confirm the table exists and the Informatica user has SELECT access
3. Check the source qualifier SQL override — ensure the query is valid
4. Look at the session log for the specific line number where initialization failed

---

## Error: WRT_8229 — Session Rejected Rows Exceeded Error Threshold

**Error Message:**
```
WRT_8229 [Session [s_m_ORDER_FACT_LOAD] failed because the number
of rejected rows exceeded the error threshold [0].]
```

**Root Cause:**
- Data quality issues in source — nulls in NOT NULL columns, type mismatches
- Target table constraints being violated (PK, FK, UNIQUE, CHECK)
- Error threshold in session properties is set to 0 (fail on first error)

**Resolution Steps:**
1. Open the session log and search for `WRT_8229` or `rejected` to find the bad rows
2. Check the `bad_file` (reject file) created in the session configuration directory
3. Fix data quality issues at the source or add transformation logic in the mapping
4. As a workaround for development/testing: set error threshold to a higher value in session properties → Config Object → Error Threshold
5. For production, never increase threshold without understanding root cause

**Example Reject File Location:**
```
/etl/informatica/pmserver/infa_shared/SessLogs/bad_<session_name>.txt
```

---

## Error: DTM_1243 — Transformation Error / Null Input

**Error Message:**
```
DTM_1243 [Error invoking transformation function [IIF] with input [NULL]:
Division by zero or invalid operation]
```

**Root Cause:**
- Expression transformation receiving NULL values not handled properly
- Division by zero or ISNULL not checked before computation

**Resolution Steps:**
1. Add NULL checks in expression transformations: `IIF(ISNULL(col), 0, col)`
2. Add `IIF(divisor = 0, NULL, numerator/divisor)` for any division operations
3. Set the transformation tracing level to VERBOSE for detailed row-level debugging

---

## Error: Session Hangs / Deadlocks on Target

**Symptom:**
Session runs indefinitely, no rows loaded after several hours. Target is Oracle or SQL Server.

**Root Cause:**
- Another process has locked the target table (e.g., concurrent DML, long-running MERGE)
- Commit interval is too high, holding transaction locks for too long

**Resolution Steps:**
1. Kill the Informatica session from Workflow Monitor
2. Check DB for blocking sessions:
   - Oracle: `SELECT * FROM v$session WHERE blocking_session IS NOT NULL;`
   - SQL Server: `SELECT * FROM sys.dm_exec_requests WHERE blocking_session_id <> 0;`
3. Reduce the commit interval in session properties (e.g., from 50000 to 10000 rows)
4. Schedule Informatica sessions when target tables have minimal DML contention

---

## Session Log Location

Default path (Linux):
```
/etl/informatica/pmserver/infa_shared/SessLogs/<session_name>_<timestamp>.log
```

Always check the session log first before escalating. The last 50 lines usually contain the root cause.
