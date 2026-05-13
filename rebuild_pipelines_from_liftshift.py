#!/usr/bin/env python3
"""
Rebuild pipelines.json from Lift & Shift Dragon CSV
- Only Dragon project (not Star)
- Keep existing priority mapping
- Include table list per task
"""
import pandas as pd
import json
import re

# Read Lift & Shift CSV
df = pd.read_csv('../reference_data/Lift_and_Shift_DW_Migration_Risk_Assessment(HSO DRAGON).csv', 
                 encoding='latin-1', on_bad_lines='skip')

# Filter only Dragon project
dragon = df[df['Project'] == 'Dragon'].copy()
print(f"Dragon rows: {len(dragon)}")

# Load existing pipelines.json for priority mapping
with open('data/pipelines.json') as f:
    existing = json.load(f)

# Extract priority mapping
priority_map = {}
for name, p in existing.items():
    priority_map[name] = p.get('priority', 'unassigned')

# Extract DAG name from DAG Link column
def extract_dag_name(dag_link):
    if pd.isna(dag_link):
        return None
    # Pattern: http://10.252.136.230:8080/dags/DAG_NAME/grid
    match = re.search(r'/dags/([^/]+)/grid', str(dag_link))
    if match:
        return match.group(1)
    return None

# Group by Platform and create pipeline structure
pipelines = {}

# Process Cloudera rows
cloudera = dragon[dragon['Platform'] == 'Cloudera']
print(f"\nCloudera rows: {len(cloudera)}")

for _, row in cloudera.iterrows():
    dag_link = row.get('DAG Link/ Other Orchestration', '')
    dag_name = extract_dag_name(dag_link)
    
    if not dag_name:
        continue
    
    # Normalize dag_name
    dag_name = dag_name.lower()
    
    if dag_name not in pipelines:
        pipelines[dag_name] = {
            'dag_id': dag_name,
            'platform': 'Cloudera',
            'priority': priority_map.get(dag_name, 'unassigned'),
            'schedule': '',
            'total_tasks': 0,
            'status_counts': {},
            'tasks': []
        }
    
    # Create task entry
    task = {
        'task_id': str(row.get('Activity Name (Synapse & Fabric)', row.get('Asset', ''))),
        'type': str(row.get('Tech Scripting  (Pyspark. Python. Hive. Impala. Scala)', '')),
        'status': 'Belum Convert',
        'tool': '',
        'database': str(row.get('Database Name', '')),
        'table': str(row.get('Table Name', '')),
        'script_file': str(row.get('Script FileName', '')),
        'script_location': str(row.get('Script FileLocation', '')),
        'tested': False
    }
    
    pipelines[dag_name]['tasks'].append(task)
    pipelines[dag_name]['total_tasks'] = len(pipelines[dag_name]['tasks'])

# Process Synapse rows
synapse = dragon[dragon['Platform'] == 'Synapse']
print(f"Synapse rows: {len(synapse)}")

for _, row in synapse.iterrows():
    pipeline_name = row.get('Pipeline Name (Synapse/Fabric)', '')
    if pd.isna(pipeline_name) or not pipeline_name:
        continue
    
    # Normalize pipeline name
    pipeline_key = str(pipeline_name).lower().replace(' ', '_').replace('-', '_')
    
    if pipeline_key not in pipelines:
        pipelines[pipeline_key] = {
            'dag_id': pipeline_key,
            'platform': 'Synapse',
            'priority': priority_map.get(pipeline_key, 'unassigned'),
            'schedule': '',
            'total_tasks': 0,
            'status_counts': {},
            'tasks': []
        }
    
    task = {
        'task_id': str(row.get('Activity Name (Synapse & Fabric)', '')),
        'type': str(row.get('Tech Scripting  (Pyspark. Python. Hive. Impala. Scala)', '')),
        'status': 'Belum Convert',
        'tool': 'Synapse',
        'database': str(row.get('Database Name', '')),
        'table': str(row.get('Table Name', '')),
        'script_file': str(row.get('Script FileName', '')),
        'script_location': str(row.get('Script FileLocation', '')),
        'link': str(row.get('Link Script (TFS/Notebook)', '')),
        'tested': False
    }
    
    pipelines[pipeline_key]['tasks'].append(task)
    pipelines[pipeline_key]['total_tasks'] = len(pipelines[pipeline_key]['tasks'])

# Process Fabric rows
fabric = dragon[dragon['Platform'].isin(['Fabric', 'Fabric Tenant AI'])]
print(f"Fabric rows: {len(fabric)}")

for _, row in fabric.iterrows():
    pipeline_name = row.get('Pipeline Name (Synapse/Fabric)', '')
    if pd.isna(pipeline_name) or not pipeline_name:
        pipeline_name = row.get('Asset', 'unknown_fabric')
    
    # Normalize pipeline name
    pipeline_key = 'fab_' + str(pipeline_name).lower().replace(' ', '_').replace('-', '_')
    
    if pipeline_key not in pipelines:
        pipelines[pipeline_key] = {
            'dag_id': pipeline_key,
            'platform': 'Fabric',
            'priority': priority_map.get(pipeline_key, 'unassigned'),
            'schedule': '',
            'total_tasks': 0,
            'status_counts': {},
            'tasks': []
        }
    
    task = {
        'task_id': str(row.get('Activity Name (Synapse & Fabric)', '')),
        'type': str(row.get('Tech Scripting  (Pyspark. Python. Hive. Impala. Scala)', '')),
        'status': 'Belum Convert',
        'tool': 'Fabric',
        'database': str(row.get('Database Name', '')),
        'table': str(row.get('Table Name', '')),
        'script_file': str(row.get('Script FileName', '')),
        'link': str(row.get('Link Script (TFS/Notebook)', '')),
        'tested': False
    }
    
    pipelines[pipeline_key]['tasks'].append(task)
    pipelines[pipeline_key]['total_tasks'] = len(pipelines[pipeline_key]['tasks'])

# Update status_counts based on tasks
for name, p in pipelines.items():
    belum = sum(1 for t in p['tasks'] if t['status'] == 'Belum Convert')
    done = sum(1 for t in p['tasks'] if t['status'] == 'Done')
    skip = sum(1 for t in p['tasks'] if 'SKIP' in t['status'].upper())
    
    p['status_counts'] = {}
    if done > 0:
        p['status_counts']['Done'] = done
    if skip > 0:
        p['status_counts']['SKIP'] = skip
    if belum > 0:
        p['status_counts']['Belum Convert'] = belum

# Summary
print(f"\n=== Summary ===")
print(f"Total pipelines: {len(pipelines)}")
total_tasks = sum(p['total_tasks'] for p in pipelines.values())
print(f"Total tasks: {total_tasks}")

# By platform
cloudera_pipes = [p for p in pipelines.values() if p['platform'] == 'Cloudera']
synapse_pipes = [p for p in pipelines.values() if p['platform'] == 'Synapse']
fabric_pipes = [p for p in pipelines.values() if p['platform'] == 'Fabric']
print(f"Cloudera pipelines: {len(cloudera_pipes)}, tasks: {sum(p['total_tasks'] for p in cloudera_pipes)}")
print(f"Synapse pipelines: {len(synapse_pipes)}, tasks: {sum(p['total_tasks'] for p in synapse_pipes)}")
print(f"Fabric pipelines: {len(fabric_pipes)}, tasks: {sum(p['total_tasks'] for p in fabric_pipes)}")

# Save to new file for review
with open('data/pipelines_rebuilt.json', 'w') as f:
    json.dump(pipelines, f, indent=2)

print(f"\n✅ Saved to data/pipelines_rebuilt.json")
print("Review the file before replacing data/pipelines.json")
