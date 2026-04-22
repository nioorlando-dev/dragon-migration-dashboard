# Prompt untuk claude.ai/design

Copy semua teks di bawah garis ini dan paste ke claude.ai/design:

---

Build a local web dashboard app (HTML + CSS + JS, no framework, runs on localhost via `python -m http.server`) for monitoring an ETL migration project at Astra International. The project migrates 28 Hadoop/Cloudera pipelines to GCP (BigQuery + Cloud Composer).

## Visual Design

- **Style**: Inspired by Vercel dashboard — dark mode, sharp, minimal, professional. NOT generic AI-generated style.
- **Colors**: Background #0a0a0a, cards #111111, borders #222222, accent green #00d084 for success, red #ff4444 for blocked, yellow #f5a623 for pending, blue #0070f3 for primary actions
- **Typography**: `Inter` or `Geist` font (load from Google Fonts), sharp and clean
- **Animations**: Rich micro-interactions throughout — card hover glows, animated status badges (pulse for blocked, shimmer for pending), smooth sidebar transitions, progress bars animate on load with easing, counters count up from 0 on load, section transitions with fade+slide

## Layout

Fixed sidebar (240px) + main content area. Single HTML file + JS reads from `data/pipelines.json` and `data/status.json` via `fetch()`.

### Sidebar
- App title: "HSO Dragon Migration" with a small dragon emoji or custom icon
- Navigation items with icons:
  - Overview
  - P1 Critical (badge showing count: 5)
  - P2 High (badge: 6)
  - P3 Medium (badge: 6)
  - P4-P5 Low (badge: 4)
  - Unassigned (badge: 7)
  - All Pipelines
- Active state: left border accent, subtle background highlight
- Bottom: last updated timestamp

### Sections

#### 1. Overview (default view)
- Top stats row (4 cards, animate count-up on load):
  - Total Pipelines: 28
  - Total Tasks: 922
  - Converted: X (calculate from status)
  - Blocked: X

- Pipeline status summary cards (3 columns):
  - Done / In Progress / Blocked / Pending — color coded

- Progress bar per priority group (P1 → P5 → Unassigned), with % converted

- "P1 Critical" section highlighted with special styling — these 5 pipelines need attention:
  dragon_leads_funnel_management, dragon_customerprofilesales, dragon_partsharecontribution, dragon_ustk2, so2w_dragon_sdue_fabric

#### 2. Priority Views (P1, P2, P3, P4-P5, Unassigned)
- Grid of pipeline cards for that priority
- Each card shows:
  - Pipeline name (monospace font)
  - Priority badge
  - Schedule (e.g. "Daily 21:00")
  - Total tasks count
  - Mini progress bar (converted / total tasks)
  - Status badge: "DAG Done", "Blocked", "Pending", "Testing"
  - Blocker text in red if blocked
  - Last updated date
- Hover: card lifts with subtle shadow + border glow

#### 3. All Pipelines
- Table view with columns: Pipeline Name | Priority | Tasks | Converted | Status | Blocker | Last Updated
- Sortable columns (click header)
- Filter bar: search by name, filter by priority, filter by status
- Row click → expands to show task list

#### 4. Pipeline Detail (opens when clicking a card or table row)
- Full-screen overlay or side panel with slide-in animation
- Pipeline header: name, priority badge, schedule, overall status
- Blocker alert box (red) if blocked
- Notes section
- Task list table:
  - Columns: Task ID | Type | Status | GCP Tool | Notes
  - Status color coded: SKIP (gray), Belum Convert (yellow), Done (green), NEED INPUT (red)
- Close button (X) or click outside to dismiss

## Data Structure

Reads from two JSON files via fetch():

**`data/status.json`** — dynamic, updated when work progresses:
```json
{
  "dragon_leads_funnel_management": {
    "status": "dag_done",
    "dag_converted": true,
    "sql_converted": true,
    "tested": false,
    "blocker": "Source data belum ada di BigQuery",
    "notes": "DAG + 5 SQL files selesai. Siap deploy ke Composer.",
    "last_updated": "2026-04-18"
  }
}
```

Status values: `"done"`, `"dag_done"`, `"blocked"`, `"pending"`, `"testing"`

**`data/pipelines.json`** — static pipeline + task data:
```json
{
  "dragon_leads_funnel_management": {
    "dag_id": "dragon_leads_funnel_management",
    "priority": "P1",
    "schedule": "Daily 21:00",
    "total_tasks": 11,
    "status_counts": {"Belum Convert": 9, "SKIP": 2},
    "tasks": [
      {"task_id": "start", "type": "Dummy", "status": "SKIP", "tool": "SKIP", "catatan": ""}
    ]
  }
}
```

## Interactions Required

1. Sidebar navigation → smooth content transition (fade out old, fade in new)
2. Pipeline cards → clickable, opens detail panel with slide-in from right
3. Detail panel → close with X button or ESC key or click backdrop
4. Table → sortable by clicking column headers (toggle asc/desc with arrow indicator)
5. Table row → expand inline to show tasks (accordion)
6. Search/filter → live filter as user types (no button needed)
7. Status badges → "blocked" pulses red, "pending" has shimmer animation, "done" has solid green
8. Progress bars → animate from 0% to actual value on section load
9. Counters in overview → count up from 0 to actual number on load
10. Hover states on all interactive elements (cards, rows, nav items)

## Key Pipelines Reference

**P1 (5 pipelines):**
- `dragon_leads_funnel_management` — 11 tasks, DAG+SQL done, blocked (data not in BQ)
- `dragon_customerprofilesales` — 10 tasks, DAG done, blocked (dbt models on Cloudera)
- `dragon_partsharecontribution` — 9 tasks, DAG done, blocked (dbt models)
- `dragon_ustk2` — 7 tasks, DAG done, blocked (dbt models)
- `so2w_dragon_sdue_fabric` — 26 tasks, DAG done, blocked (dbt models + Fabric ID)

**P2 (6 pipelines):** dragon_datarevenue, dragon_motorkux, dragon_monitoring_bku, dragon_marketsharedata, dragon_nms_handleleasing, so2w_smartstock, dragon_report_bd

**P3 (5 pipelines):** dragon_monitoringkuitansi_all, dragon_niguri_partstock, dragon_monitoring_stnk_bpkb, dragon_leadtimesalesheader_fromspk, dragon_customerpersona_segmentation

**Unassigned large pipelines:** dragon (275 tasks), so2w_dragon (236 tasks), so2w_dragon_2 (204 tasks)

## Technical Notes

- Pure HTML/CSS/JS — no React, no Vue, no build step
- All fetch() calls use relative paths (`./data/pipelines.json`)
- Handle fetch errors gracefully (show "Failed to load data" message)
- Responsive enough for 1440px width (primary target)
- ESC key closes any open panel/overlay
- All pipeline names displayed in monospace font
- Timestamps formatted as "18 Apr 2026"

## IMPORTANT — Output Instructions

Generate ONLY these files:
1. `index.html` — main app file (can include inline `<style>` and `<script>`)
2. `app.js` — only if JS is too large for inline

DO NOT generate:
- `data/` folder or any JSON files (they already exist locally)
- README or documentation files
- Any other files

The `data/pipelines.json` and `data/status.json` files already exist on the user's machine. Just reference them via fetch().
