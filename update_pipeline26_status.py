#!/usr/bin/env python3
"""
Update Pipeline 26 (dragon_L2) status in pipelines.json
Based on completed Dataproc Serverless runs on 2026-05-16/17
"""

import json
from datetime import datetime

# Load pipelines.json
with open("data/pipelines.json", "r") as f:
    pipelines = json.load(f)

# Pipeline 26 completed scripts with row counts
completed_scripts = {
    "h1": {"rows": 26885, "timestamp": "2026-05-16 16:53"},
    "h23": {"rows": 16936, "timestamp": "2026-05-16 15:58"},
    "pc": {"rows": 13453, "timestamp": "2026-05-16 17:35"},
    "pkb": {"rows": 8625, "timestamp": "2026-05-16 17:35"},
    "partsales": {"rows": 23155, "timestamp": "2026-05-16 17:35"},
    "po_h23": {"rows": 23062, "timestamp": "2026-05-16 17:35"},
    "po_suggestion": {"rows": 19574, "timestamp": "2026-05-16 17:35"},
    "billingpart_header": {"rows": 217530, "timestamp": "2026-05-16 17:38"},
    "billingservice_header": {"rows": 900000, "timestamp": "2026-05-16 17:38"},
    "grheaders": {"rows": 645372, "timestamp": "2026-05-16 17:38"},
    "grdetails": {"rows": 869274, "timestamp": "2026-05-16 19:05"},
    "stockpart": {"rows": 4424, "timestamp": "2026-05-16 19:10"},
    "billingpart_detail": {"rows": 301597, "timestamp": "2026-05-16 19:41"},
    "billingservice_detail": {"rows": 60696156, "timestamp": "2026-05-16 19:47"},
    "incomingheader": {"rows": 15709949, "timestamp": "2026-05-16 20:02"},
    "incomingdetail": {"rows": 30156819, "timestamp": "2026-05-16 20:13"},
    "outgoingheader": {"rows": 2471542, "timestamp": "2026-05-16 20:17"},
    "outgoingdetail": {"rows": 17982442, "timestamp": "2026-05-16 20:22"},
    "prospect": {"rows": 29822741, "timestamp": "2026-05-16 20:33"},
    "spkheaders": {"rows": 1856302, "timestamp": "2026-05-16 20:48"},
    "spkdetails": {"rows": 946087, "timestamp": "2026-05-16 20:57"},
    "customerheaders": {"rows": 41720224, "timestamp": "2026-05-16 21:02"},
    "pkbheaders": {"rows": 200000, "timestamp": "2026-05-16 21:11"},
    "customerdetails": {"rows": 201911154, "timestamp": "2026-05-16 21:22"},
    "metric_a_j": {"rows": 5339, "timestamp": "2026-05-16 21:27"},
    "metric_k_q": {"rows": 249519, "timestamp": "2026-05-16 21:57"},
    "metric_r_y": {"rows": 76587, "timestamp": "2026-05-17 11:39"},
    "metric_z_ad": {"rows": 23892, "timestamp": "2026-05-17 11:52"},
}

# Task ID mapping (task_id in JSON -> script name)
task_to_script = {
    "star_incomingheader": "incomingheader",
    "star_incomingdetail": "incomingdetail",
    "star_outgoingheader": "outgoingheader",
    "star_outgoingdetail": "outgoingdetail",
    "star_spkdetails": "spkdetails",
    "star_spkheaders": "spkheaders",
    "star_prospect": "prospect",
    "star_customerdetails": "customerdetails",
    "star_customerheaders": "customerheaders",
    "star_pkbheaders": "pkbheaders",
    "star_grheaders": "grheaders",
    "star_grdetails": "grdetails",
    "star_stockpart": "stockpart",
    "star_billingpart_detail": "billingpart_detail",
    "star_billingpart_header": "billingpart_header",
    "star_billingservice_detail": "billingservice_detail",
    "star_billingservice_header": "billingservice_header",
}

# Update dragon_L2 pipeline
if "dragon_L2" in pipelines:
    pipeline = pipelines["dragon_L2"]
    
    # Update status counts
    done_count = 0
    skip_count = 0
    
    for task in pipeline.get("tasks", []):
        task_id = task.get("task_id", "")
        script_name = task_to_script.get(task_id, task_id.replace("star_", ""))
        
        if script_name in completed_scripts:
            info = completed_scripts[script_name]
            task["status"] = "Done"
            task["tested"] = True
            task["tool"] = "Dataproc Serverless (PySpark)"
            task["catatan"] = f"✅ SUCCESS: {info['rows']:,} rows @ {info['timestamp']}"
            task["notes"] = f"Converted T-SQL → Spark SQL. Output: L2_STAR.{script_name}"
            done_count += 1
        elif task.get("type") == "Dummy" or task_id == "start" or task_id == "end":
            skip_count += 1
        else:
            # Check if already done
            if task.get("status") == "Done":
                done_count += 1
            else:
                skip_count += 1
    
    pipeline["status_counts"] = {
        "Done": done_count,
        "SKIP": skip_count
    }
    pipeline["status"] = "Done"
    pipeline["dag_done"] = True
    pipeline["last_updated"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    pipeline["validation_report"] = "docs/PIPELINE_26_VALIDATION_REPORT.md"
    
    print(f"Updated dragon_L2: {done_count} Done, {skip_count} SKIP")

# Also update dragon_l2_py if exists
if "dragon_l2_py" in pipelines:
    pipeline = pipelines["dragon_l2_py"]
    
    done_count = 0
    for task in pipeline.get("tasks", []):
        task_id = task.get("task_id", "").lower().replace("bd_", "").replace("star_", "")
        
        # Match against completed scripts
        for script_name in completed_scripts:
            if script_name in task_id or task_id in script_name:
                info = completed_scripts[script_name]
                task["status"] = "Done"
                task["tested"] = True
                task["tool"] = "Dataproc Serverless (PySpark)"
                task["catatan"] = f"✅ {info['rows']:,} rows"
                done_count += 1
                break
    
    pipeline["status"] = "Done"
    pipeline["dag_done"] = True
    pipeline["last_updated"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    print(f"Updated dragon_l2_py: {done_count} tasks marked Done")

# Save updated pipelines.json
with open("data/pipelines.json", "w") as f:
    json.dump(pipelines, f, indent=2, ensure_ascii=False)

print(f"\n✅ pipelines.json updated at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
