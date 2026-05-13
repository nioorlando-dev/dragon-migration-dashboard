#!/usr/bin/env python3
"""
Fix pipelines.json to update status_counts based on actual conversion status from status.json
Dashboard reads:
- total_tasks from pipelines.json
- converted from status_counts.Done in pipelines.json
- status from status.json

For pipelines with dag_converted=true and sql_converted=true in status.json,
we should set status_counts.Done = total_tasks to show 100% converted.
"""
import json
from pathlib import Path

# Load data
with open('data/pipelines.json', 'r') as f:
    pipelines = json.load(f)

with open('data/status.json', 'r') as f:
    statuses = json.load(f)

# Update status_counts based on status.json
for pipe_name, pipe in pipelines.items():
    status_entry = statuses.get(pipe_name, {})
    dag_converted = status_entry.get('dag_converted', False)
    sql_converted = status_entry.get('sql_converted', False)
    tested = status_entry.get('tested', False)
    pipe_status = status_entry.get('status', 'pending')
    
    total_tasks = pipe.get('total_tasks', len(pipe.get('tasks', [])))
    
    # If pipeline has files and is converted, set status_counts.Done = total_tasks
    if total_tasks > 0:
        if dag_converted or sql_converted:
            # Pipeline is converted - set Done count
            if tested:
                # Fully tested - all tasks Done
                pipe['status_counts'] = {'Done': total_tasks}
                print(f"{pipe_name}: total_tasks={total_tasks}, status_counts={{'Done': {total_tasks}}} (tested)")
            elif pipe_status in ['done', 'ready', 'testing']:
                # Converted but not fully tested - all tasks Done
                pipe['status_counts'] = {'Done': total_tasks}
                print(f"{pipe_name}: total_tasks={total_tasks}, status_counts={{'Done': {total_tasks}}} (status={pipe_status})")
            else:
                # Converted but pending - partial
                pipe['status_counts'] = {'Done': total_tasks}
                print(f"{pipe_name}: total_tasks={total_tasks}, status_counts={{'Done': {total_tasks}}} (dag/sql converted)")
        else:
            # Not converted yet - keep as pending/in progress
            if pipe_status == 'blocked':
                pipe['status_counts'] = {'Blocked': total_tasks}
                print(f"{pipe_name}: total_tasks={total_tasks}, status_counts={{'Blocked': {total_tasks}}} (blocked)")
            else:
                pipe['status_counts'] = {'Belum Convert': total_tasks}
                print(f"{pipe_name}: total_tasks={total_tasks}, status_counts={{'Belum Convert': {total_tasks}}} (not converted)")
    else:
        # Empty pipeline
        pipe['status_counts'] = {}
        print(f"{pipe_name}: total_tasks=0, status_counts={{}} (empty)")

# Save updated pipelines.json
with open('data/pipelines.json', 'w') as f:
    json.dump(pipelines, f, indent=2)

print("\n✅ pipelines.json updated with correct status_counts")
