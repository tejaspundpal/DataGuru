# Python for Data Engineering — Pandas Issues & Fixes

## Overview
Common pandas and Python data processing issues encountered in our ETL scripts, with root causes and fixes.

---

## Issue 1: MemoryError with Large DataFrames

**Symptom:**
```
MemoryError: Unable to allocate 8.5 GiB for array
```

**Root Cause:**
Loading entire large CSV or database result set into a single pandas DataFrame. Pandas holds everything in RAM.

**Fixes:**

### Fix 1: Use chunked reading
```python
import pandas as pd

# Read CSV in chunks of 100,000 rows
chunk_size = 100_000
results = []

for chunk in pd.read_csv("orders_large.csv", chunksize=chunk_size):
    # Process each chunk
    filtered = chunk[chunk['status'] == 'COMPLETED']
    results.append(filtered)

final_df = pd.concat(results, ignore_index=True)
```

### Fix 2: Specify dtypes to reduce memory
```python
dtype_map = {
    "customer_id":   "int32",      # instead of int64
    "order_amount":  "float32",    # instead of float64
    "status":        "category",   # for low-cardinality string columns
    "region":        "category",
}

df = pd.read_csv("orders.csv", dtype=dtype_map)
print(df.memory_usage(deep=True).sum() / 1024**2, "MB")
```

### Fix 3: Use polars for very large files
For files > 5GB, switch from pandas to polars (10x faster, lazy evaluation):
```python
import polars as pl

df = pl.scan_csv("orders_large.csv").filter(pl.col("status") == "COMPLETED").collect()
```

---

## Issue 2: SettingWithCopyWarning

**Symptom:**
```
SettingWithCopyWarning: A value is trying to be set on a copy of a slice from a DataFrame.
Try using .loc[row_indexer, col_indexer] = value instead
```

**Root Cause:**
Modifying a slice of a DataFrame instead of the original. Pandas makes ambiguous copies during chained indexing.

**Wrong Way:**
```python
# Creates a copy — modification may not persist
filtered_df = df[df['status'] == 'ACTIVE']
filtered_df['flag'] = 1   # SettingWithCopyWarning here
```

**Correct Way:**
```python
# Use .copy() to explicitly make a copy
filtered_df = df[df['status'] == 'ACTIVE'].copy()
filtered_df['flag'] = 1   # Safe — this is a real copy

# OR: Use .loc to modify original
df.loc[df['status'] == 'ACTIVE', 'flag'] = 1
```

---

## Issue 3: Merge / Join Issues

### Problem A: Unexpected Row Multiplication (Many-to-Many Join)

**Symptom:** DataFrame after merge has far more rows than expected.

**Cause:** Duplicate keys in both left and right DataFrames → cartesian product on matching keys.

**Fix:**
```python
# Check for duplicates before merge
print("Left dupes:", df_orders.duplicated(subset=['customer_id']).sum())
print("Right dupes:", df_customers.duplicated(subset=['customer_id']).sum())

# Deduplicate before joining
df_customers = df_customers.drop_duplicates(subset=['customer_id'], keep='last')

# Now merge safely
merged = df_orders.merge(df_customers, on='customer_id', how='left')
```

### Problem B: NaN Values After Left Join

**Symptom:** Columns from right DataFrame are NaN for many rows after merge.

**Cause:** Key mismatch — trailing spaces, case differences, or dtype mismatch.

**Fix:**
```python
# Strip whitespace from keys
df_orders['customer_id'] = df_orders['customer_id'].str.strip()
df_customers['customer_id'] = df_customers['customer_id'].str.strip()

# Ensure same dtype
df_orders['customer_id'] = df_orders['customer_id'].astype(str)
df_customers['customer_id'] = df_customers['customer_id'].astype(str)

merged = df_orders.merge(df_customers, on='customer_id', how='left')
# Check how many didn't match
print("Unmatched rows:", merged['customer_name'].isna().sum())
```

---

## Issue 4: Datetime Parsing Failures

**Symptom:**
```
ValueError: time data '31-13-2024' does not match format '%d-%m-%Y'
ParserError: Unknown string format
```

**Fix:**
```python
# Always specify format explicitly for performance + correctness
df['order_date'] = pd.to_datetime(df['order_date'], format='%Y-%m-%d', errors='coerce')

# 'coerce' converts unparseable values to NaT instead of raising error
# Check how many failed to parse
print("Invalid dates:", df['order_date'].isna().sum())

# Filter out bad dates
df = df.dropna(subset=['order_date'])
```

---

## Issue 5: apply() is Slow — Vectorize Instead

**Symptom:** Script takes 10+ minutes to process 1M rows due to row-by-row apply().

**Wrong Way:**
```python
# Extremely slow — runs Python loop row by row
df['net_amount'] = df.apply(lambda row: row['gross'] - row['discount'], axis=1)
```

**Correct Way:**
```python
# Vectorized — pandas applies operation on entire column at once (C-level speed)
df['net_amount'] = df['gross'] - df['discount']

# For complex logic, use np.where instead of apply
import numpy as np
df['category'] = np.where(df['amount'] > 1000, 'HIGH', 'LOW')
```

---

## General Best Practices

| Practice | Rule |
|---|---|
| Memory | Use `category` dtype for string columns with <50 unique values |
| Memory | Use `int32` / `float32` unless precision > 2 billion required |
| Joins | Always check for duplicate keys before merging |
| Datetime | Always use `errors='coerce'`, handle NaT explicitly |
| Performance | Prefer vectorized operations over `.apply()` |
| Safety | Use `.copy()` when slicing DataFrame before modifying |
