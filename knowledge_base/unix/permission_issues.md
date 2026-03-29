# Unix — File Permission Issues & Resolution Guide

## Overview
File and directory permission issues frequently block data engineering pipelines. This guide covers common permission errors, resolution steps, and team standards.

---

## Issue 1: ETL Script Cannot Write to Output Directory

**Error:**
```
IOError: [Errno 13] Permission denied: '/etl/output/orders_20240115.csv'
```

**Root Cause:**
The output directory `/etl/output/` is owned by `root` or another user. The `etl_user` account running the cron job does not have write permission.

**Resolution:**
```bash
# Check current permissions
ls -la /etl/output/
# drwxr-xr-x  2 root root  4096 Jan 15 02:00 output

# Fix: Change ownership to etl_user (or etl group)
sudo chown -R etl_user:etl_group /etl/output/
# Now: drwxr-xr-x  2 etl_user etl_group  4096 Jan 15 02:00 output

# Also ensure write permission
chmod 775 /etl/output/
# Owner: rwx, Group: rwx, Others: r-x
```

---

## Issue 2: Cannot Execute Shell Script — Permission Denied

**Error:**
```bash
$ /etl/scripts/run_daily_load.sh
bash: /etl/scripts/run_daily_load.sh: Permission denied
```

**Root Cause:**
Script does not have the execute (`x`) permission bit set.

**Resolution:**
```bash
# Check current permissions
ls -la /etl/scripts/run_daily_load.sh
# -rw-r--r--  1 etl_user etl_group  2048 Jan 10 12:00 run_daily_load.sh
# Missing 'x' bit — cannot execute

# Add execute permission for owner and group
chmod 755 /etl/scripts/run_daily_load.sh
# -rwxr-xr-x  1 etl_user etl_group  2048 Jan 10 12:00 run_daily_load.sh

# Alternatively, add execute for just the owner
chmod u+x /etl/scripts/run_daily_load.sh
```

---

## Issue 3: Informatica Cannot Read Source File — Permission Mismatch

**Scenario:**
Informatica session reads from flat files dropped by an upstream SFTP process. Session fails with:
```
FR_3032 [Error opening file /data/landing/customer_feed.csv: Permission denied]
```

**Root Cause:**
Files dropped by SFTP are owned by `sftp_user` with permissions `600` (only owner can read). The Informatica process runs as `infa_user` — different user, no access.

**Resolution:**
```bash
# Option 1: Add both users to the same group
sudo usermod -aG data_group sftp_user
sudo usermod -aG data_group infa_user

# Set group read permission on the landing directory
chmod 750 /data/landing/
chmod 640 /data/landing/*.csv
# Owner: rw, Group: r, Others: none

# Option 2: Use ACLs for fine-grained control (without changing ownership)
setfacl -m u:infa_user:r /data/landing/customer_feed.csv
# Gives infa_user read access without changing file owner

# Option 3: Auto-fix permissions on file arrival (add to SFTP post-upload hook)
chmod 644 /data/landing/*.csv
```

---

## Issue 4: SSH Key Permission Too Open

**Error:**
```
@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
@ WARNING: UNPROTECTED PRIVATE KEY FILE! @
Permissions 0644 for '/home/etl_user/.ssh/id_rsa' are too open.
This private key will be ignored.
```

**Root Cause:**
SSH requires private key files to have strict permissions (only owner can read).

**Resolution:**
```bash
chmod 600 /home/etl_user/.ssh/id_rsa        # private key: owner read/write only
chmod 644 /home/etl_user/.ssh/id_rsa.pub     # public key: readable by all OK
chmod 700 /home/etl_user/.ssh                 # .ssh directory: owner only
```

---

## Permission Cheat Sheet

### Numeric Mode
| Number | Permission | Meaning |
|---|---|---|
| 7 | rwx | Read + Write + Execute |
| 6 | rw- | Read + Write |
| 5 | r-x | Read + Execute |
| 4 | r-- | Read only |
| 0 | --- | No access |

### Common Permission Settings
| Numeric | Symbolic | Use Case |
|---|---|---|
| `755` | rwxr-xr-x | Scripts/executables — owner full, group/others can run |
| `644` | rw-r--r-- | Data files — owner write, group/others read |
| `750` | rwxr-x--- | Directories with sensitive data — group can read |
| `600` | rw------- | Private keys, credentials — owner only |
| `775` | rwxrwxr-x | Shared directories — owner and group can write |
| `700` | rwx------ | Private directories (.ssh, personal logs) |

### Key Commands
```bash
# Change ownership (user:group)
chown etl_user:etl_group /etl/scripts/run_daily_load.sh

# Change ownership recursively
chown -R etl_user:etl_group /etl/output/

# Change permissions
chmod 755 script.sh

# Add execute permission for owner only
chmod u+x script.sh

# Check effective permissions for a specific user
sudo -u infa_user cat /data/landing/customer_feed.csv

# List ACLs on a file
getfacl /data/landing/customer_feed.csv

# Set ACL to grant read to a specific user
setfacl -m u:infa_user:r /data/landing/customer_feed.csv
```

---

## Team Standards

1. All ETL scripts must be owned by `etl_user:etl_group` with permissions `755`
2. Landing zone files must have group read (`640` or `644`)
3. SSH keys must be `600` — never more permissive
4. Log directories must be `775` so monitoring tools can read
5. Credential files (`.env`, `.pgpass`, wallet files) must be `600`
6. Never use `chmod 777` — it gives write access to everyone (security violation)
