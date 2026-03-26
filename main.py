from datetime import date
from pawpal_system import Owner, Pet, Task, Scheduler

# ── Create owner ─────────────────────────────────────────────────────────────
owner = Owner(name="Alex", daily_time_budget=120)

# ── Create pets ──────────────────────────────────────────────────────────────
buddy    = Pet(name="Buddy",    species="dog")
whiskers = Pet(name="Whiskers", species="cat")

owner.add_pet(buddy)
owner.add_pet(whiskers)

# ── Add tasks for Buddy ───────────────────────────────────────────────────────
buddy.add_task(Task(
    description="Morning walk",
    duration_minutes=30,
    priority=5,
    due_time="07:00",
    pet_name="Buddy",
    frequency="daily",
))
buddy.add_task(Task(
    description="Feed breakfast",
    duration_minutes=10,
    priority=4,
    due_time="07:30",
    pet_name="Buddy",
    frequency="daily",
))
buddy.add_task(Task(
    description="Evening walk",
    duration_minutes=30,
    priority=3,
    due_time="18:00",
    pet_name="Buddy",
    frequency="daily",
))
# Weekly grooming — anchored to today's weekday so it always shows today
buddy.add_task(Task(
    description="Grooming session",
    duration_minutes=20,
    priority=2,
    due_time="10:00",
    pet_name="Buddy",
    frequency="weekly",
    due_date=date.today(),
))

# ── Add tasks for Whiskers ────────────────────────────────────────────────────
whiskers.add_task(Task(
    description="Feed breakfast",
    duration_minutes=5,
    priority=4,
    due_time="08:00",
    pet_name="Whiskers",
    frequency="daily",
))
whiskers.add_task(Task(
    description="Clean litter box",
    duration_minutes=10,
    priority=3,
    due_time="12:00",
    pet_name="Whiskers",
    frequency="daily",
))
# One-time vet checkup — anchored to today so it appears in today's plan
whiskers.add_task(Task(
    description="Vet checkup",
    duration_minutes=60,
    priority=5,
    due_time="14:00",
    pet_name="Whiskers",
    frequency="once",
    due_date=date.today(),
))
# A task already done — used to demonstrate status filtering
whiskers.add_task(Task(
    description="Morning playtime",
    duration_minutes=15,
    priority=2,
    due_time="09:00",
    pet_name="Whiskers",
    frequency="daily",
    completed=True,
))

scheduler = Scheduler()
today     = date.today()

print("=" * 55)
print("           PAWPAL+ — DAILY REPORT")
print(f"           {today}")
print("=" * 55)

# ── Add extra tasks out of order to demonstrate sorting ──────────────────────
buddy.add_task(Task(
    description="Midday water check",
    duration_minutes=5,
    priority=3,
    due_time="13:00",
    pet_name="Buddy",
    frequency="daily",
))
whiskers.add_task(Task(
    description="Evening playtime",
    duration_minutes=20,
    priority=2,
    due_time="19:30",
    pet_name="Whiskers",
    frequency="daily",
))
buddy.add_task(Task(
    description="Night snack",
    duration_minutes=5,
    priority=1,
    due_time="21:00",
    pet_name="Buddy",
    frequency="daily",
))

# ── Feature 1: Sort all tasks by due time using Scheduler.sort_by_time() ─────
print("\n[FEATURE 1] All Tasks Sorted by Due Time (sort_by_time)")
print("-" * 55)
all_tasks    = owner.get_all_tasks()
sorted_tasks = scheduler.sort_by_time(all_tasks)
for task in sorted_tasks:
    status = "DONE" if task.completed else "    "
    print(f"  [{status}] {task.due_time}  {task.description:<22} ({task.pet_name})")

# ── Feature 2: Filter tasks by pet and by completion status ──────────────────
print("\n[FEATURE 2] Filter by Pet")
print("-" * 55)
for pet in owner.pets:
    pending   = pet.get_pending_tasks()
    completed = [t for t in pet.get_tasks() if t.completed]
    print(f"  {pet.name} — {len(pending)} pending, {len(completed)} completed")
    for t in pending:
        print(f"    - {t.description} @ {t.due_time} (priority {t.priority})")
    for t in completed:
        print(f"    - [DONE] {t.description}")

print("\n[FEATURE 2] Filter by Status — Pending only (all pets)")
print("-" * 55)
pending_all = owner.get_pending_tasks()
for t in pending_all:
    print(f"  {t.pet_name:<10} {t.due_time}  {t.description}")

print("\n[FEATURE 2] filter_tasks — completed tasks only")
print("-" * 55)
done_tasks = scheduler.filter_tasks(all_tasks, completed=True)
for t in done_tasks:
    print(f"  [DONE] {t.pet_name:<10} {t.due_time}  {t.description}")

print("\n[FEATURE 2] filter_tasks — Buddy's tasks only (sorted by time)")
print("-" * 55)
buddy_tasks = scheduler.sort_by_time(scheduler.filter_tasks(all_tasks, pet_name="Buddy"))
for t in buddy_tasks:
    status = "DONE" if t.completed else "    "
    print(f"  [{status}] {t.due_time}  {t.description}")

# ── Feature 3: Recurring task handling ───────────────────────────────────────
print("\n[FEATURE 3] Recurring Task Handling")
print("-" * 55)
print(f"  Tasks due TODAY ({today}):")
due_today = owner.get_due_tasks(today)
for t in due_today:
    print(f"    [{t.frequency:<7}] {t.description:<22} ({t.pet_name})")

print()
print("  Tasks by frequency:")
for freq in ("daily", "weekly", "once"):
    group = scheduler.get_tasks_by_frequency(all_tasks, freq)
    label = f"  {freq.capitalize():<8}"
    print(f"{label}: {', '.join(t.description for t in group) if group else 'none'}")

# simulate end-of-day reset: daily/weekly tasks reset, 'once' tasks stay done
demo_tasks = [t for t in all_tasks if t.completed]
if demo_tasks:
    print()
    print("  Simulating end-of-day reset (once tasks keep their completed state):")
    scheduler.reset_completed(all_tasks)
    for t in all_tasks:
        print(f"    [{t.frequency:<7}] {t.description:<22} completed={t.completed}")

# ── Feature 3b: mark_task_complete auto-creates next occurrence ───────────────
print("\n[FEATURE 3b] Auto-Scheduling Next Occurrence on Completion")
print("-" * 55)
# Pick the first pending daily task for Buddy as the demo target
demo_task = next((t for t in buddy.get_pending_tasks() if t.frequency == "daily"), None)
if demo_task:
    print(f"  Completing daily task: '{demo_task.description}' (due_date={demo_task.due_date})")
    next_occurrence = scheduler.mark_task_complete(demo_task, buddy, today)
    print(f"  Task marked complete : completed={demo_task.completed}")
    if next_occurrence:
        print(f"  New occurrence created: '{next_occurrence.description}' due_date={next_occurrence.due_date}")

# Demo weekly recurrence using Buddy's grooming session
weekly_task = next((t for t in buddy.get_pending_tasks() if t.frequency == "weekly"), None)
if weekly_task:
    print(f"\n  Completing weekly task: '{weekly_task.description}' (due_date={weekly_task.due_date})")
    next_weekly = scheduler.mark_task_complete(weekly_task, buddy, today)
    print(f"  Task marked complete : completed={weekly_task.completed}")
    if next_weekly:
        print(f"  New occurrence created: '{next_weekly.description}' due_date={next_weekly.due_date}")

# ── Feature 4: Conflict detection ────────────────────────────────────────────
print("\n[FEATURE 4] Conflict Detection")
print("-" * 55)

# Add two tasks at the exact same time to trigger same-time conflict warnings
buddy.add_task(Task(
    description="Afternoon training",
    duration_minutes=20,
    priority=3,
    due_time="15:00",
    pet_name="Buddy",
    frequency="daily",
))
whiskers.add_task(Task(
    description="Afternoon brushing",
    duration_minutes=15,
    priority=2,
    due_time="15:00",
    pet_name="Whiskers",
    frequency="daily",
))

# Refresh the due-today list to include the new tasks
due_today = owner.get_due_tasks(today)

# Lightweight same-time conflict check (returns warnings, never crashes)
same_time_warnings = scheduler.check_same_time_conflicts(due_today)
if same_time_warnings:
    print("  Same-Time Conflicts:")
    for warning in same_time_warnings:
        print(f"  {warning}")
    print()

# Full overlap-based conflict detection
conflicts = scheduler.detect_conflicts(due_today)
if conflicts:
    for t1, t2, reschedule in conflicts:
        print(f"  CONFLICT: '{t1.description}' ({t1.due_time}, {t1.duration_minutes}min)")
        print(f"            overlaps with '{t2.description}' ({t2.due_time}, {t2.duration_minutes}min)")
        print(f"            Suggested fix: reschedule '{reschedule.description}' (lower priority)")
        print()
else:
    print("  No overlap conflicts detected.")

# ── Generate and print Today's Full Schedule ─────────────────────────────────
plan = scheduler.generate_daily_plan(owner, today)
print("\n[SCHEDULE] Full Daily Plan")
print("=" * 55)
print(scheduler.explain_plan(plan))
print("=" * 55)

# ── Feature 5: Task and Pet Management ───────────────────────────────────────
print("\n[FEATURE 5] Task and Pet Management")
print("-" * 55)

# mark_all_complete: mark every pending Whiskers task done in one call
pending_whiskers = whiskers.get_pending_tasks()
print(f"  mark_all_complete — marking {len(pending_whiskers)} pending Whiskers task(s) complete")
scheduler.mark_all_complete(pending_whiskers)
print(f"  Whiskers pending after: {len(whiskers.get_pending_tasks())}")

# remove_task: remove a specific task from Buddy by description
removed = buddy.remove_task("Night snack")
print(f"\n  buddy.remove_task('Night snack'): {'removed' if removed else 'not found'}")
print(f"  Buddy task count after: {len(buddy.tasks)}")

# remove_pet: remove Whiskers from the owner's roster
owner.remove_pet("Whiskers")
print("\n  owner.remove_pet('Whiskers')")
print(f"  Owner pets after: {[p.name for p in owner.pets]}")
