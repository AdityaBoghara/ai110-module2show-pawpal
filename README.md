# PawPal+

A Streamlit web app that helps busy pet owners plan and manage daily care tasks across multiple pets. PawPal+ intelligently schedules tasks within a time budget, detects conflicts, and handles recurring routines automatically.

---

## Table of Contents

- [Demo](#demo)
- [Features](#features)
- [Setup](#setup)
- [Usage Guide](#usage-guide)
- [System Architecture](#system-architecture)
- [Running Tests](#running-tests)
- [Project Structure](#project-structure)

---

## Demo

![PawPal+ app screenshot showing the Owner Setup panel, dashboard metrics (Pets, Tasks Completed, Tasks Pending), and a progress bar — running live in Streamlit](<Demo Screenshot.png>)

> The Owner Setup section lets you configure your name and daily time budget. The dashboard metrics update in real time as tasks are added and completed.

---

## Features

### Priority-Based Greedy Scheduling
Generates an optimized daily plan using a greedy algorithm that respects the owner's time budget. Tasks are considered in priority order (1–5), then by due time, then by duration. Only tasks that fit within the remaining time budget are scheduled; the rest are moved to a skipped list with a reason.

### Three-Tier Task Sorting
Tasks are sorted by three criteria simultaneously: priority (descending), due time (ascending), and duration (ascending as a tiebreaker). Tasks with invalid or missing times are placed last. This ordering ensures the most important and time-sensitive tasks are always scheduled first.

### Time Budget Enforcement
Each owner sets a daily time budget in minutes. The scheduler accumulates task durations and stops adding tasks once the budget is exhausted, preventing over-commitment. The schedule view shows time used, time available, and time remaining.

### Dual Conflict Detection
Two independent algorithms detect scheduling conflicts:
- **Exact-time collision** — O(n) pass using a dictionary to flag any two tasks sharing the same `HH:MM` start time.
- **Time-window overlap** — O(n²) pairwise check that parses start and end times to detect tasks whose durations overlap, even if their start times differ. The lower-priority task is flagged as the reschedule candidate.

Both conflict types are surfaced in the UI with color-coded warnings (red for exact collisions, yellow for overlaps).

### Daily and Weekly Recurrence
Tasks support three frequency modes:
- **Daily** — always due; completing a daily task automatically creates a new instance scheduled for tomorrow.
- **Weekly** — due on a specific weekday; completing a weekly task creates a new instance 7 days out. Weekday matching works correctly across month and year boundaries.
- **Once** — a one-time task; no new instance is created after completion.

### Automatic Next-Occurrence Scheduling
When a recurring task is marked complete, PawPal+ immediately generates the next occurrence and adds it to the pet's task list. The confirmation message shows the next due date so the owner always knows what's coming.

### Smart Filtering
Tasks can be filtered by:
- Completion status (pending / completed / all)
- Pet name (case-insensitive)
- Recurrence frequency (daily / weekly / once)
- Priority threshold (returns high-priority tasks ≥ configurable threshold, sorted descending)

### End-of-Day Reset
A single button resets all recurring (daily and weekly) tasks to incomplete, preparing the schedule for the next day. One-time tasks retain their completed state.

### Multi-Pet Management
One owner account can manage any number of pets. Pets are stored in an indexed dictionary for O(1) lookup by name. The schedule aggregates tasks across all pets, and filtering can be scoped to a single pet or the entire household.

### Persistent Data Storage
All owner, pet, and task data is serialized to `pawpal_data.json` via `to_dict` / `from_dict` methods. State is automatically loaded on app startup and saved after every change.

### High-Priority Warnings
Any task with priority ≥ 4 that cannot fit into the schedule due to budget constraints triggers a visible alert. This ensures critical care (medications, time-sensitive feeding) is never silently dropped.

---

## Setup

```bash
# 1. Clone the repository
git clone <repo-url>
cd ai110-module2show-pawpal

# 2. Create and activate a virtual environment
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Launch the app
streamlit run app.py
```

---

## Usage Guide

### 1. Owner Setup
Enter your name and daily time budget (in minutes). This budget caps how many minutes of tasks can be scheduled in a single day.

### 2. Add Pets
Register each pet with a name and species. Pets can be removed at any time; removing a pet also removes all associated tasks.

### 3. Add Tasks
For each task, provide:
- **Pet** — which pet this task belongs to
- **Title** — a short description (e.g., "Morning walk")
- **Duration** — how many minutes the task takes
- **Due time** — preferred start time in `HH:MM` format
- **Priority** — 1 (low) to 5 (critical)
- **Frequency** — `daily`, `weekly`, or `once`
- **Due date** — required for `weekly` and `once` tasks

After adding tasks, the conflict panel automatically scans for exact-time collisions and time-window overlaps and displays rescheduling suggestions.

### 4. Mark Tasks Complete
Select any pending task and click **Mark Complete**. For recurring tasks, the next occurrence is created automatically and the confirmation shows its due date. Use **Mark All Complete** to close out the day, or **Reset Daily Tasks** to refresh recurring tasks for a new day.

### 5. Generate a Schedule
Pick a date and click **Generate schedule**. The app displays:
- A table of scheduled tasks (sorted by priority and time)
- A table of skipped tasks with skip reasons
- Budget metrics (available / used / remaining)
- Alerts for any high-priority tasks that were skipped

---

## System Architecture

```
Owner
├── daily_time_budget
├── pets: Dict[str, Pet]          # O(1) lookup by name
│   └── Pet
│       ├── name, species
│       └── tasks: List[Task]
│           └── Task
│               ├── description, duration_minutes
│               ├── priority (1–5), due_time (HH:MM)
│               ├── frequency (daily/weekly/once)
│               ├── due_date, completed
│               └── methods: mark_complete(), is_due_today(), to_dict()
└── Scheduler (stateless utility)
    ├── sort_by_time()            # sort by HH:MM ascending
    ├── sort_tasks()              # 3-tier: priority, time, duration
    ├── filter_tasks()            # by status, pet name
    ├── get_tasks_by_frequency()  # by recurrence type
    ├── get_high_priority_tasks() # threshold filter, sorted desc
    ├── generate_daily_plan()     # greedy budget-aware scheduler
    ├── check_same_time_conflicts() # O(n) exact-time collision
    └── detect_conflicts()        # O(n²) time-window overlap

Storage: pawpal_data.json (JSON serialization)
UI:      app.py (Streamlit)
Tests:   tests/test_pawpal.py (pytest, 40+ test cases)
```

### Scheduling Algorithm (Greedy)
1. Collect all tasks due on the target date via `is_due_today()`.
2. Sort with `sort_tasks()` — priority ↓, due time ↑, duration ↑.
3. Iterate in sorted order; add a task to the plan if `time_used + duration ≤ budget`.
4. Skip completed tasks immediately; skip over-budget tasks with a reason.
5. Emit high-priority warnings for any skipped task with priority ≥ 4.
6. Return scheduled tasks, skipped tasks, time metrics, and warnings.

**Time complexity:** O(n log n) sort + O(n) allocation = O(n log n) overall.

---

## Running Tests

```bash
# Run the full test suite
pytest tests/test_pawpal.py -v

# Run a specific test class
pytest tests/test_pawpal.py::TestGenerateDailyPlan -v

# Run with coverage report
pytest tests/test_pawpal.py --cov=pawpal_system
```

The test suite covers all major behaviors:
- Greedy scheduling with budget constraints and edge cases (zero budget, exact fit)
- Daily / weekly / once recurrence logic, including year-boundary weekday matching
- Completion state management and auto-recurrence generation
- Exact-time and time-window conflict detection
- Multi-criteria filtering and three-tier sorting
- JSON serialization round-trips

---

## Project Structure

```
ai110-module2show-pawpal/
├── app.py               # Streamlit UI
├── pawpal_system.py     # Core domain logic (Task, Pet, Owner, Scheduler)
├── main.py              # CLI demonstration script
├── pawpal_data.json     # Persistent data store (auto-generated)
├── requirements.txt     # Python dependencies
└── tests/
    └── test_pawpal.py   # pytest test suite (40+ test cases)
```
