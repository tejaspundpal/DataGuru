# Spark / PySpark — Data Skew & Skewed Join Issues

## Overview
Data skew is when data is unevenly distributed across partitions, causing some tasks to process 100x more data than others. The slowest task bottlenecks the entire Spark stage. This document covers real incidents and fix techniques.

---

## Incident INC-2024-0312 — Customer Join Skew Causing 4-Hour Stage

**Date:** March 12, 2024
**Reported By:** Spark UI Monitoring Alert
**Cluster:** Databricks `de-batch-prod`
**Ticket:** JIRA-DE-2056

### Symptom
`spark_customer_360.py` job stuck for 4 hours on a single stage. Spark UI showed:
- Stage 5 (SortMergeJoin): 199 of 200 tasks finished in 3 minutes
- 1 task still running after 4 hours with 6.2 GB of shuffle read
- All other tasks had ~30 MB of shuffle read

### Root Cause
Joining `fact_transactions` (2 billion rows) with `dim_customer` on `customer_id`. One customer (`customer_id = 'GUEST_999'`) had 450 million transactions (22.5% of all rows). This created one massive partition containing all guest transactions.

```python
# Problematic code — standard join on skewed key
result = df_transactions.join(df_customers, "customer_id")
```

### Resolution — Salting Technique

**Salting = Adding a random suffix to the skewed key to distribute it across multiple partitions**

```python
import pyspark.sql.functions as F
from pyspark.sql.types import IntegerType
import random

SALT_BUCKETS = 20   # spread the skewed key across 20 partitions

# Step 1: Salt the large (fact) table — add random suffix to customer_id
df_transactions_salted = df_transactions.withColumn(
    "salt", (F.rand() * SALT_BUCKETS).cast(IntegerType())
).withColumn(
    "customer_id_salted", F.concat(F.col("customer_id"), F.lit("_"), F.col("salt"))
)

# Step 2: Explode the small (dimension) table — create copies for each salt bucket
df_customers_exploded = df_customers.crossJoin(
    spark.range(SALT_BUCKETS).withColumnRenamed("id", "salt")
).withColumn(
    "customer_id_salted", F.concat(F.col("customer_id"), F.lit("_"), F.col("salt"))
)

# Step 3: Join on salted key — now GUEST_999 is distributed across 20 partitions
result = df_transactions_salted.join(
    df_customers_exploded,
    "customer_id_salted"
).drop("salt", "customer_id_salted")
```

**Outcome:** Stage completed in 8 minutes instead of 4 hours.

---

## Incident INC-2024-0528 — GroupBy Skew on Product Category

**Date:** May 28, 2024
**Ticket:** JIRA-DE-2198

### Symptom
`spark_product_analytics.py` — groupBy on `product_category` was extremely slow. One category ("Electronics") had 60% of all orders.

### Resolution — Two-Phase Aggregation

```python
# Phase 1: Add salt, then aggregate (distributes hot key across partitions)
SALT_BUCKETS = 10

df_salted = df.withColumn("salt", (F.rand() * SALT_BUCKETS).cast(IntegerType()))

# Partial aggregation with salt
partial_agg = df_salted.groupBy("product_category", "salt").agg(
    F.sum("revenue").alias("partial_revenue"),
    F.count("order_id").alias("partial_count")
)

# Phase 2: Remove salt, final aggregation
final_agg = partial_agg.groupBy("product_category").agg(
    F.sum("partial_revenue").alias("total_revenue"),
    F.sum("partial_count").alias("total_orders")
)
```

---

## How to Detect Skew

### Method 1: Spark UI
- Open Spark UI → Stages → click on the slow stage
- Look at Task Duration Distribution — if one task is 10x+ longer than median, it's skewed
- Check Shuffle Read Size per task — uneven sizes confirm skew

### Method 2: Programmatic Check
```python
# Check partition sizes
from pyspark.sql.functions import spark_partition_id

partition_counts = df.groupBy(spark_partition_id().alias("partition_id")).count()
partition_counts.describe().show()

# Check key distribution
df.groupBy("customer_id").count().orderBy(F.desc("count")).show(20)
# If top key has 100x more rows than average → skew confirmed
```

### Method 3: Use AQE Skew Join Optimization
```python
# Spark 3.0+ — Adaptive Query Execution handles skew automatically
spark.conf.set("spark.sql.adaptive.enabled", "true")
spark.conf.set("spark.sql.adaptive.skewJoin.enabled", "true")
spark.conf.set("spark.sql.adaptive.skewJoin.skewedPartitionFactor", "5")
spark.conf.set("spark.sql.adaptive.skewJoin.skewedPartitionThresholdInBytes", "256m")
# AQE will automatically split skewed partitions during join
```

---

## Skew Handling Decision Matrix

| Scenario | Technique | Complexity |
|---|---|---|
| Join skew on single known key | Salting | Medium |
| Join skew on unknown/dynamic keys | AQE Skew Join (Spark 3.0+) | Low (config only) |
| GroupBy skew | Two-phase aggregation | Medium |
| Skew + Small dimension table | Broadcast join (if dim < 500MB) | Low |
| Write skew to partitioned output | Repartition before write | Low |

---

## Key Metrics to Monitor for Skew

| Metric | Where | Alert Threshold |
|---|---|---|
| Max task duration vs median | Spark UI → Stage | >10x difference |
| Shuffle read size per task | Spark UI → Task | >1 GB while median is <100 MB |
| Key cardinality | Programmatic check | Top key >5% of total rows |
| GC time on executors | Spark UI → Executors | >30% of task time |
