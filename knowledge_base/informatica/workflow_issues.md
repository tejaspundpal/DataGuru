# Informatica Workflow Issues — SOP & Troubleshooting Guide

## Overview
Common Informatica PowerCenter workflow-level problems: scheduling failures, dead states, parameter file errors, and notification issues.

---

## Issue 1: Workflow Stuck in "Running" State (Dead Workflow)

**Symptom:**
Workflow shows status as "Running" in Workflow Monitor, but no sessions are actively processing. CPU usage is 0%. Has been "running" for hours.

**Root Cause:**
- Informatica Integration Service crashed mid-run
- Server was rebooted while workflow was executing
- Network timeout disconnected the pmserver process

**Resolution Steps:**
1. Open Workflow Monitor → right-click the workflow → Stop
2. If Stop doesn't work → right-click → Abort
3. If still stuck, kill the pmserver process on the Informatica server:
   ```bash
   # Find the process
   ps -ef | grep pmserver
   # Kill it
   kill -9 <pid>
   ```
4. Restart Integration Service from Informatica Administrator
5. Re-run the workflow

**Prevention:**
- Enable automatic workflow recovery in session properties
- Set `Recovery Strategy` to `Restart Task` for critical workflows

---

## Issue 2: Workflow Scheduling Not Triggering

**Symptom:**
Workflow is scheduled but does not run at the expected time.

**Root Cause:**
- Scheduler timezone mismatch (server timezone vs. scheduled timezone)
- Integration Service is in safe mode (paused)
- Workflow is suspended after a previous failure
- Schedule set to "Run Once" and was already executed

**Resolution Steps:**
1. Check Integration Service status in Informatica Administrator — must be `Running`
2. Verify the schedule: Workflow → Properties → Scheduler
   - Confirm timezone is correct (use server local time or UTC consistently)
3. Check if workflow is suspended: Workflow Monitor → right-click → Resume
4. For "Run Once" schedules, change to a repeating schedule or trigger manually
5. Review Informatica server time: `date` on Linux, `time` on Windows

---

## Issue 3: Parameter File Not Found / Parameter Not Resolved

**Common Error:**
```
WF_46034 [Parameter file [$PMRootDir/parameter_files/wf_orders_load.par] cannot be found.]
PETL_24037 [Parameter [$DBConnection_SRC] cannot be resolved.]
```

**Root Cause:**
- Parameter file path is wrong (case-sensitive on Linux)
- Parameter file doesn't have the correct section header
- Parameter file not copied to the correct server directory

**Parameter File Format:**
```ini
[Global]
$DBConnection_SRC=SRC_ORACLE_PROD
$DBConnection_TGT=TGT_DATAWAREHOUSE

[wf_orders_load.s_m_orders_daily]
$$START_DATE=2024-01-01
$$END_DATE=2024-01-31
$$BATCH_ID=20240101
```

**Resolution Steps:**
1. Verify file exists at path: `ls -la /etl/informatica/pmserver/infa_shared/parameter_files/`
2. Check section header matches exactly: `[workflow_name.session_name]`
3. For global parameters, put them under `[Global]` section
4. Test by running workflow manually and checking logs for parameter resolution

---

## Issue 4: Concurrent Workflow Conflicts

**Symptom:**
Error when trying to start a workflow that is already "Running" from a previous execution. Target table gets duplicate data.

**Root Cause:**
- Workflow triggered twice (manual + scheduler conflict)
- Previous run hung but still marked as Running
- Concurrent execution not disabled for workflows that shouldn't run in parallel

**Resolution Steps:**
1. In Workflow properties → uncheck "Allow concurrent runs" for singleton workflows
2. Add a `BATCH_LOCK` check in the workflow using a pre-session command:
   ```sql
   -- Check if batch is already running
   SELECT COUNT(*) FROM batch_control WHERE workflow_name = 'wf_orders_load' AND status = 'RUNNING';
   ```
3. Use Workflow variables to track execution state and skip if already locked

---

## Issue 5: Email Notification Not Sending

**Root Cause:**
- SMTP settings not configured in Informatica Administrator
- Firewall blocking outbound SMTP port (25, 465, 587)
- Task email notification not enabled in workflow task

**Configuration Steps:**
1. Informatica Administrator → Domain → Environment Variables → set SMTP_SERVER_HOST
2. Enable email in Workflow Designer: Workflow → Properties → General → uncheck "Disable Email"
3. In session properties → Success Email / Failure Email — add recipients

---

## Workflow Recovery Best Practices

| Setting | Recommended Value |
|---|---|
| Recovery Strategy | Restart Task |
| Maximum Concurrent Sessions | 1 (for critical pipelines) |
| Error Threshold | 0 for Prod, 100 for Dev/Test |
| Log Level | Normal (Verbose only for debugging) |
| Suspend on Error | Enabled for Prod |
