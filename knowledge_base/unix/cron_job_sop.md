# Unix — Cron Job SOP for Data Engineering Pipelines

## Overview
Cron jobs are used to schedule ETL scripts, data quality checks, file transfers, and monitoring tasks. This SOP defines how our team creates, manages, and monitors cron jobs safely.

---

## Cron Syntax Reference

```
# ┌───────────── minute (0–59)
# │ ┌───────────── hour (0–23)
# │ │ ┌───────────── day of month (1–31)
# │ │ │ ┌───────────── month (1–12)
# │ │ │ │ ┌───────────── day of week (0–7, 0 and 7 = Sunday)
# │ │ │ │ │
# * * * * *   command to execute
```

**Common Examples:**
```bash
# Run every day at 2:00 AM
0 2 * * * /etl/scripts/run_daily_load.sh

# Run every Monday at 6:00 AM
0 6 * * 1 /etl/scripts/run_weekly_report.sh

# Run every 15 minutes
*/15 * * * * /etl/scripts/check_sftp_files.sh

# Run first day of every month at midnight
0 0 1 * * /etl/scripts/monthly_archival.sh

# Run every weekday (Mon–Fri) at 8:00 PM
0 20 * * 1-5 /etl/scripts/evening_sync.sh
```

---

## Team SOP for Adding a New Cron Job

### Step 1: Create the Script
```bash
#!/bin/bash
# Script: run_daily_load.sh
# Owner: Data Engineering Team
# Schedule: Every day at 2:00 AM
# Description: Triggers daily fact_orders ETL Python script

LOG_DIR="/etl/logs"
LOG_FILE="$LOG_DIR/daily_load_$(date +%Y%m%d).log"
SCRIPT="/etl/scripts/daily_order_load.py"

echo "=== Daily Load Started at $(date) ===" >> "$LOG_FILE"

/opt/python3/bin/python3 "$SCRIPT" >> "$LOG_FILE" 2>&1
EXIT_CODE=$?

if [ $EXIT_CODE -ne 0 ]; then
    echo "=== FAILED with exit code $EXIT_CODE ===" >> "$LOG_FILE"
    # Send email alert
    echo "Daily load failed. Check log: $LOG_FILE" | mail -s "[ALERT] ETL Failure" de-team@company.com
else
    echo "=== SUCCESS at $(date) ===" >> "$LOG_FILE"
fi
```

### Step 2: Make Script Executable
```bash
chmod +x /etl/scripts/run_daily_load.sh
```

### Step 3: Edit Crontab
```bash
# Always edit using crontab -e (never edit crontab files directly)
crontab -e

# Add the new entry
0 2 * * * /etl/scripts/run_daily_load.sh
```

### Step 4: Verify It Was Added
```bash
crontab -l
```

### Step 5: Document in Pipeline Registry
Update the team's pipeline registry (Confluence/Notion) with:
- Script name, cron expression, owner, dependencies, alert contact

---

## Common Cron Failures & Fixes

### Issue 1: Cron Job Doesn't Run — Environment Variables Missing

**Root Cause:** Cron runs in a minimal environment — `PATH`, `PYTHONPATH`, and other env vars set in `.bashrc` or `.profile` are NOT available to cron.

**Fix:**
```bash
# Option 1: Set PATH explicitly in the script
export PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:/opt/python3/bin

# Option 2: Source the user profile at start of cron script
source /home/etl_user/.bashrc

# Option 3: Set SHELL and PATH in crontab header
SHELL=/bin/bash
PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
0 2 * * * /etl/scripts/run_daily_load.sh
```

### Issue 2: Cron Output Goes to /dev/null — No Logs

**Fix:** Always redirect both stdout and stderr to a log file:
```bash
# Redirect stdout and stderr to log file
0 2 * * * /etl/scripts/run_daily_load.sh >> /etl/logs/cron.log 2>&1
```

### Issue 3: Cron Job Runs Multiple Times (Overlapping)

**Cause:** Previous execution not finished when next one starts.

**Fix:** Use a lock file:
```bash
#!/bin/bash
LOCKFILE="/tmp/daily_load.lock"

if [ -f "$LOCKFILE" ]; then
    echo "Another instance is running. Exiting."
    exit 1
fi

touch "$LOCKFILE"
trap "rm -f $LOCKFILE" EXIT   # Always remove lock on exit

# ... script logic here ...
```

### Issue 4: Cron Job Fails Silently — No Alert

**Fix:** Send email on failure (as shown in script template above), or post to Slack:
```bash
curl -X POST -H 'Content-type: application/json' \
  --data '{"text":"ETL cron failed: daily_load.sh"}' \
  "$SLACK_WEBHOOK_URL"
```

---

## Log Rotation for Cron Logs

Add to `/etc/logrotate.d/etl_cron`:
```
/etl/logs/*.log {
    daily
    rotate 30
    compress
    missingok
    notifempty
}
```

---

## Cron Job Inventory (Team Standard)

All cron jobs must be documented in `cron_inventory.csv`:
```
script_name, schedule, owner, description, alert_email, last_modified
run_daily_load.sh, "0 2 * * *", Tejas, "Daily orders ETL", de-team@co.com, 2024-01-15
check_sftp_files.sh, "*/15 * * * *", Priya, "SFTP file arrival check", priya@co.com, 2024-02-01
```
