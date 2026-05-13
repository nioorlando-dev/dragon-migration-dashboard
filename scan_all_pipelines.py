#!/usr/bin/env python3
import os
import json
from pathlib import Path

# Load pipelines.json
with open('data/pipelines.json', 'r') as f:
    pipelines = json.load(f)

# Scan all pipeline folders in converted_scripts
base_path = Path("/Users/nioorlandotantio/Documents/work/Astra International/converted_scripts")

pipeline_folder_mapping = {}
for priority in ["P1", "P2", "P3"]:
    priority_path = base_path / priority
    if not priority_path.exists():
        continue

    for pipeline_dir in priority_path.glob("pipeline_*"):
        if pipeline_dir.is_dir():
            # Count actual files
            dag_files = list(pipeline_dir.rglob("*.py"))
            sql_files = list(pipeline_dir.rglob("*.sql"))
            
            # Try to match pipeline name
            pipeline_name = None
            dir_name = pipeline_dir.name.replace("pipeline_", "").lower()
            
            # Try to find matching pipeline in pipelines.json
            for p_name in pipelines.keys():
                if dir_name in p_name.lower() or p_name.lower() in dir_name:
                    pipeline_name = p_name
                    break
            
            if not pipeline_name:
                # Try exact match
                for p_name in pipelines.keys():
                    if pipeline_dir.name == f"pipeline_{p_name}":
                        pipeline_name = p_name
                        break
            
            pipeline_folder_mapping[pipeline_dir.name] = {
                "pipeline_name": pipeline_name,
                "dag_count": len(dag_files),
                "sql_count": len(sql_files),
                "total_files": len(dag_files) + len(sql_files)
            }

print("Pipeline folder mapping:")
for folder, info in sorted(pipeline_folder_mapping.items()):
    print(f"{folder} -> {info['pipeline_name'] or 'NOT FOUND'}: DAG={info['dag_count']}, SQL={info['sql_count']}, Total={info['total_files']}")
