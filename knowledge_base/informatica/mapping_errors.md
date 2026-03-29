# Informatica Mapping Errors — Debugging Guide

## Overview
This document covers common mapping-level errors in Informatica PowerCenter: expression issues, datatype problems, lookup failures, and port misconfigurations.

---

## Error Type 1: Datatype Conversion Failures

**Symptom:**
Session fails with rows rejected due to conversion error. Seen frequently when source is a flat file.

**Common Error:**
```
DTM_1055 [Type conversion error converting [ABC123] to integer for column [CUSTOMER_ID]]
```

**Root Cause:**
- Source flat file has unexpected data type (e.g., alphanumeric in numeric column)
- Source qualifier port data type is set to Integer or Decimal, but source has dirty data

**Resolution Steps:**
1. Change the source qualifier port type to String for affected columns
2. Add Expression transformation after source to cast and validate:
   ```
   IIF(IS_INTEGER(CUSTOMER_ID_STR), TO_INTEGER(CUSTOMER_ID_STR), NULL)
   ```
3. Route invalid rows to a separate error target using Router transformation
4. Fix upstream data at source system and re-run

---

## Error Type 2: Expression Transformation — Syntax Errors

**Symptom:**
Mapping fails to validate or session fails immediately at startup.

**Common Error:**
```
CMN_1131 [Expression [IIF(AMOUNT > 0, AMOUNT, o_AMOUNT)] has an error:
Invalid datatype for comparison operation.]
```

**Cause:**
Port datatype mismatch in expression — comparing String port to Number literal.

**Resolution:**
- Cast explicitly before comparison: `IIF(TO_DECIMAL(AMOUNT) > 0, TO_DECIMAL(AMOUNT), 0)`
- Always match port datatypes before using relational operators
- Use `TRUNC()` for decimal comparisons to avoid floating point issues

---

## Error Type 3: Lookup Transformation — Cache Errors

**Common Error:**
```
LKP_1013 [Lookup caching error: insufficient memory to build cache for lookup [LKP_DIM_CUSTOMER]]
LKP_1020 [Lookup cache directory full.]
```

**Root Cause:**
- Lookup table is very large and exceeds cache memory allocated
- Cache directory disk space exhausted

**Resolution Steps:**
1. Increase lookup cache memory in session properties:
   - Session → Transformations → LKP → Lookup Caches → Data Cache / Index Cache
2. Use `Connected` vs `Unconnected` lookup strategically:
   - Connected: Use when you need output ports
   - Unconnected: More memory efficient for simple lookup checks
3. Change lookup to a regular SQL override JOIN if the table is very large (>10M rows)
4. Clear old cache files from cache directory: `/etl/informatica/pmserver/infa_shared/Cache/`

---

## Error Type 4: Router Transformation — All Groups Drop Rows

**Symptom:**
Expected rows not appearing in target, no error in session log.

**Root Cause:**
- Default group not connected to any target
- Condition logic in Router group doesn't account for all values (no "else" group)

**Resolution:**
1. Always connect the Default group of Router to an error/reject target
2. Review Router group conditions — ensure they are mutually exclusive and collectively exhaustive
3. Use Expression transformation to add a flag column and validate routing logic

---

## Error Type 5: Source Qualifier — SQL Override Issues

**Common Error:**
```
SQ_1104 [Database Error: ORA-00907 missing right parenthesis]
SQ_1104 [Database Error: ORA-00942 table or view does not exist]
```

**Root Cause:**
- Manual SQL override in Source Qualifier has syntax error
- Table referenced in SQL override does not exist in the connected database schema

**Resolution Steps:**
1. Test the SQL override directly in SQL Developer or DBeaver before pasting into Informatica
2. Always use schema-qualified table names: `SCHEMA_NAME.TABLE_NAME`
3. Avoid using database-specific functions that don't match the source DB (e.g., ISNULL in Oracle — use NVL instead)
4. Validate mapping before running the session: Mapping → Validate

---

## General Debugging Tips for Mapping Errors

| Step | Action |
|---|---|
| 1 | Validate the mapping (Mapping → Validate) and fix all errors/warnings |
| 2 | Set Tracing Level to `Verbose Data` for suspect transformations |
| 3 | Check the session log for DTM or transformation-level errors |
| 4 | Use Expression Transformation to add debug ports and log intermediate values |
| 5 | Run session with a small sample (Source Filter / Override) to isolate bad rows |

---

## Datatype Cheat Sheet

| Source Type | Informatica Type | Notes |
|---|---|---|
| VARCHAR2 | String | Max length must match |
| NUMBER | Decimal | Specify precision and scale |
| DATE | Date/Time | Use TO_DATE() for string conversion |
| CLOB | Nstring/Text | Use SUBSTR() if truncation needed |
| NUMERIC NULL | Decimal with nullable | Always check ISNULL before arithmetic |
