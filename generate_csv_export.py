#!/usr/bin/env python3
"""
Generate CSV export from pipelines.json + status.json
Format: Project MAGNUM (Timeline)((Table) DRAGON - HSO).csv

Columns (exact match):
No, Project, Priority, Indikator, Phase/Delay, Platform, DAG ID, Assets,
Database Name, Table Name, Layer Bucket, Dataset BQ, Config (.cfg),
Parameter SP, Target Layer, Script/File, Script File, Tool Target GCP,
Schedule/Cadence, Initial Landing, Initial Mart, DA Maping, ETL Conversion,
Incremental, Internal Testing, PQA Test, BI Dev, Orchestration,
Labeling Charging, Dataplex, Sign-off Document, Last Updated
"""

import json
import csv
import re
import os
from datetime import datetime

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(SCRIPT_DIR, "data")

with open(os.path.join(DATA_DIR, "pipelines.json")) as f:
    pipelines = json.load(f)

with open(os.path.join(DATA_DIR, "status.json")) as f:
    statuses = json.load(f)

HEADERS = [
    "No", "Project", "Priority", "Indikator", "Phase/Delay", "Platform",
    "DAG ID", "Assets", "Database Name", "Table Name", "Layer Bucket",
    "Dataset BQ", "Config (.cfg)", "Parameter SP", "Target Layer",
    "Script/File", "Script File", "Tool Target GCP", "Schedule/Cadence",
    "Initial Landing", "Initial Mart", "DA Maping", "ETL Conversion",
    "Incremental", "Internal Testing", "PQA Test", "BI Dev", "Orchestration",
    "Labeling Charging", "Dataplex", "Sign-off Document", "Last Updated"
]

# Map pipeline status → ETL Conversion column value
ETL_STATUS_MAP = {
    "done":     "Done",
    "ready":    "Done",
    "testing":  "Done",
    "pending":  "In Progress",
    "blocked":  "In Progress",
}

# Map task status → ETL Conversion value
TASK_STATUS_MAP = {
    "Done":           "Done",
    "SKIP":           "Skip",
    "Belum Convert":  "In Progress",
    "Skip":           "Skip",
}

def extract_script(catatan, tool):
    for text in [catatan, tool]:
        found = re.findall(r'[\w\-\.]+\.py', text)
        if found:
            return found[0]
        found = re.findall(r'[\w\-\.]+\.sql', text)
        if found:
            return found[0]
    return "-"

def tested_to_phase(tested, status):
    """Map tested flag + status to Internal Testing column."""
    s = str(status).lower()
    if s == "skip":
        return "Skip"
    return "Completed" if tested else ""

rows = []
global_no = 1
project_no = 1

for pipe_name, pipe in pipelines.items():
    dag_id = pipe.get("dag_id", pipe_name)
    priority = str(pipe.get("priority", ""))
    schedule = pipe.get("schedule", "-")
    status_entry = statuses.get(pipe_name, {})
    pipe_status_raw = (status_entry.get("status", "pending") or "pending").lower()
    etl_conv = ETL_STATUS_MAP.get(pipe_status_raw, "In Progress")
    last_updated = status_entry.get("last_updated", "")
    dag_converted = status_entry.get("dag_converted", False)
    sql_converted = status_entry.get("sql_converted", False)
    tested_flag = status_entry.get("tested", False)
    indikator = pipe.get("description", "")
    tasks = pipe.get("tasks", [])

    # Pipeline-level header row (like merged row in original CSV)
    rows.append({
        "No": project_no,
        "Project": "dragon",
        "Priority": priority,
        "Indikator": indikator or pipe_name,
        "Phase/Delay": "",
        "Platform": "Cloudera",
        "DAG ID": dag_id,
        "Assets": "",
        "Database Name": "",
        "Table Name": "",
        "Layer Bucket": "",
        "Dataset BQ": "L3_CLOUDERA_DRAGON_HSO",
        "Config (.cfg)": "-",
        "Parameter SP": "-",
        "Target Layer": "L3",
        "Script/File": "",
        "Script File": f"{dag_id}.py",
        "Tool Target GCP": "",
        "Schedule/Cadence": schedule,
        "Initial Landing": "Completed",
        "Initial Mart": "Completed",
        "DA Maping": "Completed",
        "ETL Conversion": etl_conv,
        "Incremental": "",
        "Internal Testing": "Completed" if tested_flag else "",
        "PQA Test": "",
        "BI Dev": "",
        "Orchestration": "Done" if dag_converted else "",
        "Labeling Charging": "",
        "Dataplex": "",
        "Sign-off Document": "",
        "Last Updated": last_updated,
    })
    project_no += 1

    for task in tasks:
        task_id = task.get("task_id", "")
        task_status = task.get("status", "")
        tested = task.get("tested", False)
        tool = task.get("tool", "-")
        catatan = task.get("catatan", "")
        tipe = task.get("type", "-")
        script = extract_script(catatan, tool)

        task_etl = TASK_STATUS_MAP.get(task_status, "Done" if task_status == "Done" else "In Progress")
        int_testing = tested_to_phase(tested, task_status)

        rows.append({
            "No": global_no,
            "Project": "",
            "Priority": priority,
            "Indikator": indikator or pipe_name,
            "Phase/Delay": tipe,
            "Platform": "Cloudera",
            "DAG ID": dag_id,
            "Assets": "",
            "Database Name": "opr_ast_so2w_wh_dm",
            "Table Name": task_id,
            "Layer Bucket": "",
            "Dataset BQ": "L3_CLOUDERA_DRAGON_HSO",
            "Config (.cfg)": "-",
            "Parameter SP": "-",
            "Target Layer": "L3",
            "Script/File": script,
            "Script File": f"{dag_id}.py",
            "Tool Target GCP": tool,
            "Schedule/Cadence": schedule,
            "Initial Landing": "Completed",
            "Initial Mart": "Completed",
            "DA Maping": "Completed",
            "ETL Conversion": task_etl,
            "Incremental": "",
            "Internal Testing": int_testing,
            "PQA Test": "",
            "BI Dev": "",
            "Orchestration": "Done" if dag_converted else "",
            "Labeling Charging": "",
            "Dataplex": "",
            "Sign-off Document": "",
            "Last Updated": last_updated,
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
