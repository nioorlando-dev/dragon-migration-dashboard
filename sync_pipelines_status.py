#!/usr/bin/env python3
"""
Sync pipelines.json status_counts with status.json conversion status.

Logic:
- If sql_converted=true in status.json, update status_counts.Done to reflect converted tasks
- Preserve SKIP counts
- Update Belum Convert for remaining tasks
"""
import json

with open('data/status.json') as f:
    status = json.load(f)
with open('data/pipelines.json') as f:
    pipelines = json.load(f)

updated = 0
for name, p in pipelines.items():
    s = status.get(name, {})
    sql_converted = s.get('sql_converted', False)
    dag_converted = s.get('dag_converted', False)
    tested = s.get('tested', False)
    pipe_status = s.get('status', 'pending')
    
    total = p.get('total_tasks', len(p.get('tasks', [])))
    sc = p.get('status_counts', {})
    skip = sc.get('SKIP', 0)
    countable = total - skip  # Tasks that need conversion
    
    if countable <= 0:
        continue
    
    old_done = sc.get('Done', 0)
    
    # If sql_converted=true, set all countable tasks as Done
    if sql_converted or dag_converted:
        new_done = countable
        if old_done != new_done:
            p['status_counts'] = {'Done': new_done}
            if skip > 0:
                p['status_counts']['SKIP'] = skip
            print(f'{name}: Done {old_done} -> {new_done} (sql_converted={sql_converted}, dag_converted={dag_converted})')
            updated += 1
    else:
        # Not converted - keep as Belum Convert
        if old_done == 0 and sc.get('Belum Convert', 0) != countable:
            p['status_counts'] = {'Belum Convert': countable}
            if skip > 0:
                p['status_counts']['SKIP'] = skip
            print(f'{name}: Belum Convert = {countable}')
            updated += 1

# Save updated pipelines.json
with open('data/pipelines.json', 'w') as f:
    json.dump(pipelines, f, indent=2)

print(f'\n✅ Updated {updated} pipelines in pipelines.json')
