#!/usr/bin/env python3
"""
Sync pipelines.json:
1. Fix status_counts to match tasks array
2. Keep existing priority and structure
"""
import json
import re

with open('data/pipelines.json') as f:
    pipelines = json.load(f)

updated = 0
for name, p in pipelines.items():
    tasks = p.get('tasks', [])
    
    # Count actual statuses from tasks
    done = 0
    skip = 0
    belum = 0
    for t in tasks:
        status = (t.get('status') or '').strip().lower()
        if status == 'done':
            done += 1
        elif 'skip' in status:
            skip += 1
        elif 'belum' in status:
            belum += 1
        else:
            belum += 1  # Default to Belum Convert
    
    # Build new status_counts
    new_sc = {}
    if done > 0:
        new_sc['Done'] = done
    if skip > 0:
        new_sc['SKIP'] = skip
    if belum > 0:
        new_sc['Belum Convert'] = belum
    
    old_sc = p.get('status_counts', {})
    
    # Update if different
    if new_sc != old_sc:
        print(f'{name}: {old_sc} -> {new_sc}')
        p['status_counts'] = new_sc
        updated += 1
    
    # Update total_tasks to match tasks array length
    if p.get('total_tasks') != len(tasks):
        print(f'{name}: total_tasks {p.get("total_tasks")} -> {len(tasks)}')
        p['total_tasks'] = len(tasks)

# Save
with open('data/pipelines.json', 'w') as f:
    json.dump(pipelines, f, indent=2)

print(f'\n✅ Updated {updated} pipelines')

# Summary
total_tasks = sum(p.get('total_tasks', 0) for p in pipelines.values())
done = sum(p.get('status_counts', {}).get('Done', 0) for p in pipelines.values())
skip = sum(p.get('status_counts', {}).get('SKIP', 0) for p in pipelines.values())
belum = sum(p.get('status_counts', {}).get('Belum Convert', 0) for p in pipelines.values())

print(f'\n=== Summary ===')
print(f'Total pipelines: {len(pipelines)}')
print(f'Total tasks: {total_tasks}')
print(f'Done: {done}')
print(f'SKIP: {skip}')
print(f'Belum Convert: {belum}')
print(f'Total Tasks (excl SKIP): {total_tasks - skip}')
