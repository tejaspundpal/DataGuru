# Spark / PySpark — Performance Tuning Guide

## Overview
Production PySpark performance best practices covering partitioning, caching, join strategies, serialization, and file format optimization.

---

## 1. Partitioning Strategy

### Shuffle Partitions (spark.sql.shuffle.partitions)

The default is 200 — almost never optimal. Set based on data size:

```python
# Rule of thumb: target ~200MB per partition after shuffle
# Data size: 100GB → 100GB / 200MB = 500 partitions
spark.conf.set("spark.sql.shuffle.partitions", "500")
```

### Repartition vs Coalesce

| Method | Use Case | Cost |
|---|---|---|
| `repartition(n)` | Increase partition count, even distribution needed | Full shuffle (expensive) |
| `coalesce(n)` | Decrease partition count only | No shuffle (fast) |
| `repartition(n, col)` | Partition by specific column(s) | Full shuffle |

```python
# Writing to partitioned Parquet — repartition by partition column first
df.repartition("year", "month").write \
    .partitionBy("year", "month") \
    .mode("overwrite") \
    .parquet("s3://bucket/output/")

# Reducing output files from 200 to 10 (no shuffle, just merges partitions)
df.coalesce(10).write.mode("overwrite").parquet("s3://bucket/output/")
```

### File Size after Write
- **Target:** 128MB – 512MB per Parquet file
- Too many small files = slow reads (driver overhead listing files)
- Too few large files = can't parallelize reads effectively

---

## 2. Join Strategies

### Broadcast Join (Map-Side Join)
Use when one table is small enough to fit in executor memory.

```python
from pyspark.sql.functions import broadcast

# Broadcast the small table (< 500MB)
result = df_orders.join(broadcast(df_regions), "region_id")
```

**Config:**
```python
# Default auto-broadcast threshold: 10MB — too small for most cases
spark.conf.set("spark.sql.autoBroadcastJoinThreshold", "500m")
```

### Sort-Merge Join (Default for large-large joins)
Used when both tables are large. Requires both sides to be sorted on the join key.

**Optimization:** If joining repeatedly on the same key, pre-bucket the tables:
```python
# Write bucketed table (sorted by join key, pre-partitioned)
df.write.bucketBy(100, "customer_id").sortBy("customer_id") \
    .mode("overwrite").saveAsTable("bucketed_orders")
```

### Join Strategy Decision Matrix

| Left Table | Right Table | Best Strategy |
|---|---|---|
| Large (>1GB) | Small (<500MB) | Broadcast Join |
| Large | Large | Sort-Merge Join + AQE |
| Large (skewed) | Small | Broadcast Join (avoids skew entirely) |
| Large (skewed) | Large | Salted Join or AQE Skew Join |

---

## 3. Caching and Persistence

```python
# Cache when a DataFrame is used multiple times in the same job
df_customers = spark.read.parquet("s3://bucket/dim_customer/")
df_customers.cache()        # stores in MEMORY_AND_DISK by default
df_customers.count()        # triggers actual caching (lazy evaluation)

# Use persist() for control over storage level
from pyspark import StorageLevel
df_customers.persist(StorageLevel.MEMORY_AND_DISK_SER)
# SER = serialized — uses less memory but slightly slower to read

# Always unpersist when done
df_customers.unpersist()
```

**When to cache:**
- DataFrame read from disk and used in 3+ operations
- After expensive filter/join that significantly reduces data size
- Lookup tables used in multiple joins

**When NOT to cache:**
- DataFrame used only once (caching wastes memory + time)
- Very large DataFrames (>50% of cluster memory)
- When data changes between uses

---

## 4. File Format Selection

| Format | Read Speed | Write Speed | Compression | Schema Evolution | Best For |
|---|---|---|---|---|---|
| **Parquet** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | Good | DWH fact tables, analytics |
| **Delta** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | Excellent (ACID) | Production pipelines, SCD |
| **ORC** | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | Good | Hive ecosystem |
| **CSV** | ⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐ | Poor | Landing zone, external sources |
| **JSON** | ⭐⭐ | ⭐⭐⭐ | ⭐⭐ | Flexible | Semi-structured data, APIs |
| **Avro** | ⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ | Excellent | Kafka, streaming |

**Team Standard:** Use **Parquet with Snappy compression** for all batch pipeline outputs. Use **Delta Lake** for tables that need ACID/MERGE/SCD2.

```python
# Write optimized Parquet
df.write \
    .mode("overwrite") \
    .option("compression", "snappy") \
    .parquet("s3://bucket/output/")
```

---

## 5. Predicate Pushdown & Column Pruning

Spark automatically optimizes these if you filter/select before processing:

```python
# GOOD — Spark reads only 2 columns and pushes date filter to Parquet reader
df = spark.read.parquet("s3://bucket/fact_orders/") \
    .select("order_id", "order_amount") \
    .filter(F.col("order_date") >= "2024-01-01")

# BAD — reads all columns, all rows, then filters
df = spark.read.parquet("s3://bucket/fact_orders/")
result = df.filter(F.col("order_date") >= "2024-01-01").select("order_id", "order_amount")
# ⚠ Actually, Spark Catalyst optimizer will rewrite this to be the same.
# BUT: it's still best practice to filter/select early for readability.
```

---

## 6. UDF Performance Warning

User-Defined Functions (UDFs) are slow because they execute row-by-row in Python, not in JVM.

```python
# SLOW — Python UDF (serializes/deserializes every row)
from pyspark.sql.functions import udf
from pyspark.sql.types import StringType

@udf(returnType=StringType())
def classify(amount):
    return "HIGH" if amount > 1000 else "LOW"

df.withColumn("category", classify("order_amount"))   # Slow!

# FAST — Use built-in functions (runs in JVM, columnar)
df.withColumn("category", F.when(F.col("order_amount") > 1000, "HIGH").otherwise("LOW"))

# If you MUST use a UDF, use Pandas UDF (vectorized, 10–100x faster)
from pyspark.sql.functions import pandas_udf
import pandas as pd

@pandas_udf(StringType())
def classify_vectorized(amounts: pd.Series) -> pd.Series:
    return amounts.apply(lambda x: "HIGH" if x > 1000 else "LOW")

df.withColumn("category", classify_vectorized("order_amount"))  # Much faster
```

---

## 7. Production Config Template

```python
# Standard production Spark config for batch ETL jobs
spark.conf.set("spark.sql.adaptive.enabled", "true")
spark.conf.set("spark.sql.adaptive.coalescePartitions.enabled", "true")
spark.conf.set("spark.sql.adaptive.skewJoin.enabled", "true")
spark.conf.set("spark.sql.shuffle.partitions", "auto")    # AQE handles it
spark.conf.set("spark.serializer", "org.apache.spark.serializer.KryoSerializer")
spark.conf.set("spark.sql.parquet.compression.codec", "snappy")
spark.conf.set("spark.sql.autoBroadcastJoinThreshold", "256m")
spark.conf.set("spark.dynamicAllocation.enabled", "true")
spark.conf.set("spark.dynamicAllocation.minExecutors", "2")
spark.conf.set("spark.dynamicAllocation.maxExecutors", "50")
```
