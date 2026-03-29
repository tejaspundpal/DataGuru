# Python Scripting Patterns for Data Engineering

## Overview
Common Python patterns and utilities used by our data engineering team for pipeline scripts, file processing, database operations, and automation.

---

## Pattern 1: Database Connection with Retry Logic

```python
import time
import logging
from functools import wraps

logger = logging.getLogger(__name__)

def retry(max_retries=3, delay_seconds=5, backoff_factor=2):
    """Decorator that retries a function on exception with exponential backoff."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            current_delay = delay_seconds
            for attempt in range(1, max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if attempt == max_retries:
                        logger.error(f"FAILED after {max_retries} attempts: {e}")
                        raise
                    logger.warning(f"Attempt {attempt} failed: {e}. Retrying in {current_delay}s...")
                    time.sleep(current_delay)
                    current_delay *= backoff_factor
        return wrapper
    return decorator

@retry(max_retries=3, delay_seconds=5)
def get_db_connection(conn_string):
    """Create database connection with automatic retry on failure."""
    import pyodbc
    return pyodbc.connect(conn_string, timeout=30)
```

**When to use:** Any database or API call that can fail due to transient network issues near our team uses this pattern for all production ETL scripts.

---

## Pattern 2: Config-Driven Pipeline with YAML

Instead of hardcoding table names, file paths, and database details, use a YAML config file.

**pipeline_config.yml:**
```yaml
source:
  type: oracle
  host: ora-prod-db.internal
  port: 1521
  database: HRDB
  schema: HR
  table: EMPLOYEES

target:
  type: sqlserver
  host: dwh-prod.internal
  database: DWH_PROD
  schema: dbo
  table: DIM_EMPLOYEE

load_type: incremental
watermark_column: LAST_MODIFIED_DATE
batch_size: 50000
```

**Python config loader:**
```python
import yaml

def load_config(config_path="pipeline_config.yml"):
    with open(config_path, "r") as f:
        return yaml.safe_load(f)

config = load_config()
src_table = f"{config['source']['schema']}.{config['source']['table']}"
# "HR.EMPLOYEES"
```

---

## Pattern 3: File Watcher — Monitor SFTP/Landing Zone

```python
import os
import time
from pathlib import Path

def watch_directory(watch_path, pattern="*.csv", poll_interval=30, timeout=3600):
    """
    Watch a directory for file arrival. Used for SFTP landing zones.
    Returns the file path when a matching file appears.
    Raises TimeoutError if no file arrives within timeout.
    """
    watch_dir = Path(watch_path)
    elapsed = 0

    while elapsed < timeout:
        matching_files = sorted(watch_dir.glob(pattern))
        if matching_files:
            latest_file = matching_files[-1]
            # Wait 10 seconds and recheck size to ensure file is fully transferred
            size_1 = latest_file.stat().st_size
            time.sleep(10)
            size_2 = latest_file.stat().st_size

            if size_1 == size_2 and size_1 > 0:
                return latest_file
            # File still being written, wait

        time.sleep(poll_interval)
        elapsed += poll_interval

    raise TimeoutError(f"No {pattern} file found in {watch_path} within {timeout}s")
```

**Used in:** Pre-ETL step when waiting for upstream systems to drop files into SFTP landing folders.

---

## Pattern 4: Logging Setup for ETL Scripts

```python
import logging
from datetime import datetime

def setup_logger(script_name, log_dir="/etl/logs"):
    """Standard logging setup used by all team ETL scripts."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = f"{log_dir}/{script_name}_{timestamp}.log"

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()    # also print to console
        ]
    )

    logger = logging.getLogger(script_name)
    logger.info(f"Logger initialized. Log file: {log_file}")
    return logger

# Usage
logger = setup_logger("daily_orders_etl")
logger.info("Starting ETL...")
logger.error("Failed to connect to source DB")
```

---

## Pattern 5: Batch Processing with Progress Tracking

```python
def process_in_batches(dataframe, batch_size, process_func):
    """
    Process a pandas DataFrame in batches. Used for:
    - Large INSERT operations (avoid memory overflow)
    - API calls with rate limits
    - Checkpoint/resume after failures
    """
    total_rows = len(dataframe)
    total_batches = (total_rows + batch_size - 1) // batch_size

    for batch_num in range(total_batches):
        start_idx = batch_num * batch_size
        end_idx = min(start_idx + batch_size, total_rows)
        batch = dataframe.iloc[start_idx:end_idx]

        logger.info(f"Processing batch {batch_num + 1}/{total_batches} "
                     f"(rows {start_idx}–{end_idx})")
        process_func(batch)

    logger.info(f"All {total_batches} batches processed successfully.")
```

---

## Pattern 6: Environment-Specific Configuration

```python
import os

ENV = os.getenv("ETL_ENVIRONMENT", "DEV").upper()

DB_CONFIG = {
    "DEV": {
        "host": "dev-db.internal",
        "database": "DWH_DEV",
    },
    "QA": {
        "host": "qa-db.internal",
        "database": "DWH_QA",
    },
    "PROD": {
        "host": "prod-db.internal",
        "database": "DWH_PROD",
    },
}

current_db = DB_CONFIG.get(ENV, DB_CONFIG["DEV"])
# Set ETL_ENVIRONMENT=PROD in crontab or systemd to auto-select prod config
```

**Rule:** Never hardcode `PROD` connection strings in scripts. Always use environment-based configuration.

---

## Pattern 7: Data Validation Helper

```python
def validate_dataframe(df, rules):
    """
    Validate a DataFrame against a list of rules before loading to target.
    Returns (is_valid, errors) tuple.
    """
    errors = []

    for rule in rules:
        col = rule.get("column")
        check = rule.get("check")

        if check == "not_null":
            null_count = df[col].isna().sum()
            if null_count > 0:
                errors.append(f"Column '{col}' has {null_count} NULL values")

        elif check == "unique":
            dup_count = df[col].duplicated().sum()
            if dup_count > 0:
                errors.append(f"Column '{col}' has {dup_count} duplicate values")

        elif check == "positive":
            neg_count = (df[col] < 0).sum()
            if neg_count > 0:
                errors.append(f"Column '{col}' has {neg_count} negative values")

        elif check == "min_rows":
            min_count = rule.get("value", 1)
            if len(df) < min_count:
                errors.append(f"DataFrame has {len(df)} rows, expected at least {min_count}")

    return len(errors) == 0, errors

# Usage
rules = [
    {"column": "customer_id", "check": "not_null"},
    {"column": "customer_id", "check": "unique"},
    {"column": "order_amount", "check": "positive"},
    {"check": "min_rows", "value": 100},
]
is_valid, errors = validate_dataframe(df, rules)
if not is_valid:
    logger.error(f"Validation failed: {errors}")
    raise ValueError("Data quality check failed")
```
