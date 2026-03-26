from datetime import date
from pawpal_system import Owner, Pet, Task, Scheduler

# ── Create owner ─────────────────────────────────────────────────────────────
owner = Owner(name="Alex", daily_time_budget=120)

# ── Create pets ──────────────────────────────────────────────────────────────
buddy = Pet(name="Buddy", species="dog")
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
whiskers.add_task(Task(
    description="Vet checkup",
    duration_minutes=60,
    priority=5,
    due_time="14:00",
    pet_name="Whiskers",
    frequency="once",
))

# ── Generate and print Today's Schedule ──────────────────────────────────────
scheduler = Scheduler()
today = date.today()
plan = scheduler.generate_daily_plan(owner, today)

print("=" * 50)
print("         PAWPAL+ — TODAY'S SCHEDULE")
print("=" * 50)
print(scheduler.explain_plan(plan))
print("=" * 50)
