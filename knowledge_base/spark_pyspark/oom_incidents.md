# Spark / PySpark — OOM Incidents & Memory Configuration

## Overview
Out-of-memory (OOM) errors are the most common Spark failure mode in production. This document covers real incidents and memory configuration best practices.

---

## Incident INC-2024-0205 — Executor OOM on Daily Sales Aggregation

**Date:** February 5, 2024
**Reported By:** Airflow Alert — Task Failed
**Cluster:** Databricks cluster `de-batch-prod` (8 workers, `r5.2xlarge`)
**Ticket:** JIRA-DE-1934

### Symptom
PySpark job `spark_daily_sales_agg.py` failed after 45 minutes:
```
ExecutorDeadException: java.lang.OutOfMemoryError: GC overhead limit exceeded
Executor heartbeat timed out after 120000 ms
Container killed by YARN for exceeding memory limits.
```

### Root Cause
The job was doing a `groupBy().agg()` on 800 million rows without any partitioning. All shuffle data landed on 200 default partitions, creating very large partitions (avg 4GB per partition). Each executor (16GB RAM) couldn't hold the partition data during shuffle.

```python
# Problematic code
df.groupBy("region", "product_id").agg(
    F.sum("sales_amount").alias("total_sales"),
    F.count("order_id").alias("order_count")
)
# Default 200 shuffle partitions — too few for 800M rows
```

### Resolution

**Fix 1: Increase shuffle partitions**
```python
spark.conf.set("spark.sql.shuffle.partitions", "2000")
# Rule of thumb: target ~200MB per partition
# 800M rows × ~100 bytes/row = 80GB / 200MB = ~400 partitions minimum
```

**Fix 2: Increase executor memory**
```python
# In Spark config:
spark.conf.set("spark.executor.memory", "24g")
spark.conf.set("spark.executor.memoryOverhead", "4g")  # off-heap for JVM overhead
```

**Fix 3: Enable Adaptive Query Execution (AQE)**
```python
spark.conf.set("spark.sql.adaptive.enabled", "true")
spark.conf.set("spark.sql.adaptive.coalescePartitions.enabled", "true")
# AQE automatically adjusts partition count based on actual data size
```

**Outcome:** After fixes, job completed in 18 minutes with no OOM.

---

## Incident INC-2024-0419 — Driver OOM from collect() on Large Dataset

**Date:** April 19, 2024
**Reported By:** Tejas (Data Engineer)
**Ticket:** JIRA-DE-2087

### Symptom
```
java.lang.OutOfMemoryError: Java heap space (Driver)
```
Driver memory used: 14GB / 8GB configured.

### Root Cause
Developer used `.collect()` to bring 50 million rows back to the driver for local processing:
```python
# NEVER do this on large datasets
all_rows = df.collect()   # Pulls 50M rows to driver RAM → OOM
for row in all_rows:
    process(row)
```

### Resolution
```python
# Option 1: Process in Spark, write to sink (never collect large data)
df.write.mode("overwrite").parquet("s3://bucket/output/")

# Option 2: If you MUST iterate, use toLocalIterator() — streams one partition at a time
for row in df.toLocalIterator():
    process(row)

# Option 3: Aggregate first, then collect only summary data
summary = df.groupBy("region").agg(F.sum("amount")).collect()
# Now only collecting ~10 rows, not 50M
```

### Rule Added to Team Standards
> **Never call `.collect()` on any DataFrame with more than 100,000 rows in production.**

---

## Incident INC-2024-0731 — Broadcast Join Causing Driver OOM

**Date:** July 31, 2024
**Ticket:** JIRA-DE-2334

### Root Cause
Auto-broadcast join was enabled and Spark tried to broadcast a 3GB dimension table:
```
java.lang.OutOfMemoryError: Java heap space (broadcast)
```

### Resolution
```python
# Disable auto-broadcast or increase threshold carefully
spark.conf.set("spark.sql.autoBroadcastJoinThreshold", "-1")  # disable auto-broadcast

# Manually broadcast ONLY small tables (<500MB)
from pyspark.sql.functions import broadcast

result = df_orders.join(broadcast(df_small_dim), "region_id")
# Only use broadcast for tables < 200MB to be safe
```

---

## Memory Configuration Reference

| Config | Description | Recommended |
|---|---|---|
| `spark.executor.memory` | JVM heap per executor | 8–24g depending on node |
| `spark.executor.memoryOverhead` | Off-heap (JVM native, Python process) | 10–15% of executor memory |
| `spark.driver.memory` | Driver JVM heap | 4–8g (increase if using collect/broadcast) |
| `spark.driver.memoryOverhead` | Driver off-heap | 1–2g |
| `spark.memory.fraction` | Fraction of heap for execution+storage | 0.6 (default) |
| `spark.sql.shuffle.partitions` | Number of shuffle partitions | 200 (default), increase for large joins |
| `spark.sql.adaptive.enabled` | Adaptive Query Execution | Always set to `true` in prod |

## Quick Memory Sizing Formula

```
Total data size = row_count × avg_row_size_bytes
Target partition size = ~200MB
Required partitions = Total data size / 200MB
Set shuffle partitions = Required partitions × 1.5 (buffer)
```
