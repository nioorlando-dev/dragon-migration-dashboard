#!/usr/bin/env python3
import json

# Load pipelines.json
with open('data/pipelines.json', 'r') as f:
    pipelines = json.load(f)

# Update empty pipeline folders based on file analysis
empty_pipelines = [
    'dragon',  # pipeline_29_dragon
    'dragon_customerpersona',  # pipeline_21_customerpersona
    'fab_dragon_customerprofilesales',  # pipeline_fab_dragon_customerprofilesales
    'so2w_dragon',  # pipeline_30_so2w_dragon
    'so2w_dragon_2',  # pipeline_31_so2w_dragon_2
]

for pipeline_id in empty_pipelines:
    if pipeline_id in pipelines:
        print(f"Updating {pipeline_id} to 0 tasks")
        pipelines[pipeline_id]['total_tasks'] = 0
        pipelines[pipeline_id]['status_counts'] = {}
        pipelines[pipeline_id]['tasks'] = []

# Save updated pipelines.json
with open('data/pipelines.json', 'w') as f:
    json.dump(pipelines, f, indent=2)

print("pipelines.json updated successfully")
