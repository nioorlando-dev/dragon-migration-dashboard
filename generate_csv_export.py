#!/usr/bin/env python3
"""
Generate CSV export from pipelines.json + status.json
matching the column format of [ASTRA INTERNATIONAL] - MIGRATION & CONVERT ETL PROGRESS (1).xlsx (sheet: HSO Dragon)

Columns:
No, Platform, Phase/Delay, Indikator, Step Order, Task ID (Airflow), Tipe Step,
Script/File, Config (.cfg), Parameter SP, SSH Host, Dependency,
Status Convert, Tested/Untested, PIC, Catatan, DAG ID, Task Group,
Source System, Target Layer, Tool Target GCP, Schedule/Cadence,
Bukti Referensi, Priority, Due Date
"""

import json
import csv
import sys
import os
from datetime import datetime

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(SCRIPT_DIR, "data")

with open(os.path.join(DATA_DIR, "pipelines.json")) as f:
    pipelines = json.load(f)

with open(os.path.join(DATA_DIR, "status.json")) as f:
    statuses = json.load(f)

HEADERS = [
    "No", "Platform", "Phase/Delay", "Indikator", "Step Order",
    "Task ID (Airflow)", "Tipe Step", "Script/File", "Config (.cfg)",
    "Parameter SP", "SSH Host", "Dependency", "Status Convert",
    "Tested/Untested", "PIC", "Catatan", "DAG ID", "Task Group",
    "Source System", "Target Layer", "Tool Target GCP", "Schedule/Cadence",
    "Bukti Referensi", "Priority", "Due Date"
]

STATUS_MAP = {
    "done":     "Done",
    "testing":  "Testing",
    "ready":    "Ready",
    "pending":  "Pending",
    "blocked":  "Blocked",
}

rows = []
global_no = 1

for pipe_name, pipe in pipelines.items():
    dag_id = pipe.get("dag_id", pipe_name)
    priority = pipe.get("priority", "-")
    schedule = pipe.get("schedule", "-")
    status_entry = statuses.get(pipe_name, {})
    pipe_status = STATUS_MAP.get(status_entry.get("status", "pending").lower(), "Pending")
    indikator = pipe.get("description", pipe_name.replace("_", " ").title())
    tasks = pipe.get("tasks", [])

    # One header row per pipeline (like the Excel merged header row)
    rows.append({
        "No": "",
        "Platform": "",
        "Phase/Delay": "",
        "Indikator": f"PIPELINE | {dag_id} | {schedule}",
        "Step Order": "",
        "Task ID (Airflow)": "",
        "Tipe Step": "",
        "Script/File": "",
        "Config (.cfg)": "",
        "Parameter SP": "",
        "SSH Host": "",
        "Dependency": "",
        "Status Convert": pipe_status,
        "Tested/Untested": "",
        "PIC": "",
        "Catatan": status_entry.get("notes", ""),
        "DAG ID": dag_id,
        "Task Group": "",
        "Source System": "Cloudera",
        "Target Layer": "L3",
        "Tool Target GCP": "",
        "Schedule/Cadence": schedule,
        "Bukti Referensi": "",
        "Priority": priority,
        "Due Date": status_entry.get("last_updated", ""),
    })

    for step_i, task in enumerate(tasks, 1):
        task_id = task.get("task_id", "")
        status_raw = task.get("status", "")
        tested = task.get("tested", False)
        tool = task.get("tool", "-")
        catatan = task.get("catatan", "")
        tipe = task.get("type", "-")

        # Derive Script/File from tool or catatan
        script = "-"
        if ".py" in catatan:
            import re
            found = re.findall(r'[\w\-\.]+\.py', catatan)
            if found:
                script = found[0]
        elif ".sql" in catatan:
            found = re.findall(r'[\w\-\.]+\.sql', catatan)
            if found:
                script = found[0]
        elif ".py" in tool:
            found = re.findall(r'[\w\-\.]+\.py', tool)
            if found:
                script = found[0]

        rows.append({
            "No": global_no,
            "Platform": "Cloudera",
            "Phase/Delay": "",
            "Indikator": indikator,
            "Step Order": step_i,
            "Task ID (Airflow)": task_id,
            "Tipe Step": tipe,
            "Script/File": script,
            "Config (.cfg)": "-",
            "Parameter SP": "-",
            "SSH Host": "-",
            "Dependency": "-",
            "Status Convert": status_raw,
            "Tested/Untested": "Tested" if tested else "Untested",
            "PIC": "NIO",
            "Catatan": catatan,
            "DAG ID": dag_id,
            "Task Group": "",
            "Source System": "Cloudera",
            "Target Layer": "L3",
            "Tool Target GCP": tool,
            "Schedule/Cadence": schedule,
            "Bukti Referensi": "",
            "Priority": priority,
            "Due Date": "",
        })
        global_no += 1

# Output CSV
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
out_path = os.path.join(SCRIPT_DIR, f"HSO_DRAGON_EXPORT_{timestamp}.csv")

with open(out_path, "w", newline="", encoding="utf-8-sig") as f:
    writer = csv.DictWriter(f, fieldnames=HEADERS)
    writer.writeheader()
    writer.writerows(rows)

print(f"✅ Export selesai: {out_path}")
print(f"   Total rows: {len(rows)}")
