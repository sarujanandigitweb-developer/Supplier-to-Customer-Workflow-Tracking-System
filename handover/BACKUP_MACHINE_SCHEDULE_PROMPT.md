# Prompt for the backup developer's machine — SCWTS "add the automatic run schedule ONLY"

Open Claude Code INSIDE the cloned `Supplier-to-Customer-Workflow-Tracking-System` folder and paste the box below.
It installs only the SCWTS cron schedule. It does NOT change any code.

---

```text
Work ONLY inside this folder (the Supplier-to-Customer-Workflow-Tracking-System project, my current directory).
Do not read, scan or touch any other project or folder on this machine.

TASK: add the automatic daily run schedule (cron) for the SCWTS dashboards. Nothing else.

HARD RULES
1. DO NOT modify, create, rename or delete any file in this project (code, SQL, scripts, configs, dashboards, docs, .env). The ONLY thing you may change is my user crontab.
2. First back up my crontab: `crontab -l > ~/crontab_backup_$(date +%Y%m%d_%H%M%S).txt` (if none exists, say so).
3. Never print or copy passwords, tokens or .env values. Only check that the .env file exists.
4. Do NOT run the refresh/publish scripts — they publish to production. Only read-only checks (`test -x`, `bash -n`, `ls`).
5. Idempotent: put what you add between `# >>> SCWTS-SCHEDULE BEGIN` and `# <<< SCWTS-SCHEDULE END`; replace only that block if it exists; never duplicate or remove my other cron entries.
6. Show me the exact block and wait for my "yes" before installing.

STEP 1 — Read-only checks (report as a small table)
- Let P = the absolute path of this folder (`pwd`).
- Exist and executable: P/scripts/refresh_and_publish_v2.sh and P/scripts/refresh_and_publish_v3.sh. `bash -n` passes on both.
- P/logs/ exists (cron's `>>` redirect fails if it doesn't; if missing, tell me — don't create it).
- P/.env exists (names only; do not show values). Tell me the scripts also expect LEDSONE_PG* and PG* variables and a hub-publish credential, provided by the team lead.
- `systemctl is-active cron`, and `timedatectl | grep "Time zone"`. Schedule below is Asia/Colombo (+05:30); if this machine is in another timezone, add `CRON_TZ=Asia/Colombo` at the top of the block.

STEP 2 — The block to install (replace P with the real absolute path)
  # SCWTS Dashboard V2 — daily 11:00 refresh + publish
  0 11 * * * P/scripts/refresh_and_publish_v2.sh >> P/logs/cron_v2.out 2>&1
  # SCWTS Dashboard V3 — daily 16:00 refresh + publish
  0 16 * * * P/scripts/refresh_and_publish_v3.sh >> P/logs/cron_v3.out 2>&1

Do NOT schedule scripts/refresh_and_publish.sh (V1). V1 is frozen; its source folders were deleted and it fails daily.

STEP 3 — After my "yes", install:
  (crontab -l 2>/dev/null | sed '/# >>> SCWTS-SCHEDULE BEGIN/,/# <<< SCWTS-SCHEDULE END/d'; cat /tmp/scwts_block.txt) | crontab -
(write the block file in /tmp, not in this project).

STEP 4 — Verify and report
- `crontab -l` shows the block exactly once, other entries intact.
- Tell me the next run time of V2 and V3 in plain words, and the commands to watch them: `tail -f P/logs/cron_v2.out` and `tail -f P/logs/cron_v3.out`.
- List anything still needed from a human: .env / DB credentials, hub credential, an always-on machine (cron only runs while the machine is on).
For how each job works and troubleshooting, point me to handover/supplier_to_customer_workflow_tracking_system_handover.md (section 8 and 12).
```

---

Notes
- Credentials are not in git; get them from the team lead or the jobs will run and fail.
- Original times come from the developer's crontab (system timezone Asia/Colombo).
