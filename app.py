import json
import os
from datetime import date
import streamlit as st
from pawpal_system import Owner, Pet, Task, Scheduler

_DATA_FILE = os.path.join(os.path.dirname(__file__), "pawpal_data.json")

def save_state():
    if "owner" in st.session_state:
        with open(_DATA_FILE, "w") as f:
            json.dump(st.session_state.owner.to_dict(), f, indent=2)

def load_state():
    if "owner" not in st.session_state and os.path.exists(_DATA_FILE):
        try:
            with open(_DATA_FILE) as f:
                st.session_state.owner = Owner.from_dict(json.load(f))
        except Exception as e:
            st.error(f"Failed to load saved data: {e}")

load_state()

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")

st.title("🐾 PawPal+")

st.divider()

# ── Step 1: Set up the Owner ─────────────────────────────────────────────────
st.subheader("Owner Setup")
owner_name = st.text_input("Owner name", value="Jordan")
daily_budget = st.number_input("Daily time budget (minutes)", min_value=1, max_value=1440, value=120)

if st.button("Set Owner"):
    if "owner" in st.session_state:
        st.session_state.owner.name = owner_name
        st.session_state.owner.daily_time_budget = int(daily_budget)
    else:
        st.session_state.owner = Owner(name=owner_name, daily_time_budget=int(daily_budget))
    save_state()
    st.success(f"Owner '{owner_name}' saved with a {daily_budget}-minute daily budget.")

if "owner" not in st.session_state:
    st.info("Set an owner above to get started.")
    st.stop()

owner = st.session_state.owner
scheduler = Scheduler()
st.caption(f"Current owner: {owner.name} | Budget: {owner.daily_time_budget} min/day")

# ── Dashboard summary metrics ─────────────────────────────────────────────────
s = owner.summary()
col1, col2, col3 = st.columns(3)
col1.metric("Pets", s["pets"])
col2.metric("Tasks Completed", s["completed_tasks"])
col3.metric("Tasks Pending", s["pending_tasks"])

if s["total_tasks"] > 0:
    st.progress(
        s["completed_tasks"] / s["total_tasks"],
        text=f"{s['completed_tasks']}/{s['total_tasks']} tasks completed",
    )

st.divider()

# ── Step 2: Add a Pet ────────────────────────────────────────────────────────
st.subheader("Add a Pet")
pet_name = st.text_input("Pet name", value="Mochi")
species = st.selectbox("Species", ["dog", "cat", "other"])

if st.button("Add Pet"):
    # Check the owner doesn't already have a pet with this name
    if owner.get_pet(pet_name):
        st.warning(f"'{pet_name}' is already added.")
    else:
        new_pet = Pet(name=pet_name, species=species)
        owner.add_pet(new_pet)          # Owner.add_pet() stores it on owner.pets
        save_state()
        st.success(f"Added {pet_name} the {species}!")

if owner.pets:
    st.caption("Registered pets")
    st.dataframe(
        [{"Name": p.name, "Species": p.species.capitalize(), "Tasks": len(p.tasks)} for p in owner.pets],
        width='stretch',
        hide_index=True,
    )

    pet_to_remove = st.selectbox("Select a pet to remove", [p.name for p in owner.pets], key="remove_pet_select")
    if st.button("Remove Pet"):
        owner.remove_pet(pet_to_remove)
        save_state()
        st.success(f"Removed '{pet_to_remove}'.")
else:
    st.info("No pets yet. Add one above.")

st.divider()

# ── Step 3: Add a Task to a Pet ──────────────────────────────────────────────
st.subheader("Add a Task")

if not owner.pets:
    st.info("Add a pet first before scheduling tasks.")
else:
    pet_options = [p.name for p in owner.pets]
    col1, col2, col3 = st.columns(3)
    with col1:
        task_pet = st.selectbox("For which pet?", pet_options)
        task_title = st.text_input("Task title", value="Morning walk")
    with col2:
        duration = st.number_input("Duration (minutes)", min_value=1, max_value=240, value=20)
        due_time = st.text_input("Due time (HH:MM)", value="08:00")
    with col3:
        priority = st.slider("Priority (1–5)", min_value=1, max_value=5, value=3)
        frequency = st.selectbox("Frequency", ["daily", "weekly", "once"])

    if frequency != "daily":
        due_date = st.date_input("Due date", value=None)
    else:
        due_date = None

    if st.button("Add Task"):
        new_task = Task(
            description=task_title,
            duration_minutes=int(duration),
            priority=priority,
            due_time=due_time,
            pet_name=task_pet,
            frequency=frequency,
            due_date=due_date,
        )
        pet = owner.get_pet(task_pet)   # Owner.get_pet() looks up the right Pet
        pet.add_task(new_task)          # Pet.add_task() validates and stores it
        save_state()
        st.success(f"Task '{task_title}' added to {task_pet}.")

    # Show all tasks across all pets
    all_tasks = owner.get_all_tasks()   # Owner.get_all_tasks() aggregates across pets
    if all_tasks:
        sorted_tasks = scheduler.sort_tasks(all_tasks)
        st.caption("All tasks — sorted by priority (high → low), then due time")
        _PRIORITY_LABEL = {1: "1 – Lowest", 2: "2 – Low", 3: "3 – Medium", 4: "4 – High", 5: "5 – Critical"}
        st.dataframe(
            [
                {
                    "Status": "✅ Done" if t.completed else "⏳ Pending",
                    "Task": t.description,
                    "Pet": t.pet_name,
                    "Due": t.due_time,
                    "Duration": f"{t.duration_minutes} min",
                    "Priority": _PRIORITY_LABEL.get(t.priority, str(t.priority)),
                    "Frequency": t.frequency.capitalize(),
                }
                for t in sorted_tasks
            ],
            width='stretch',
            hide_index=True,
        )

        # Conflict detection — detect_conflicts catches exact same-time as a subset
        # of window overlaps, so it's the single source of truth here.
        st.markdown("**Schedule Conflicts**")
        overlap_conflicts = scheduler.detect_conflicts(all_tasks)
        if overlap_conflicts:
            for t1, t2, reschedule in overlap_conflicts:
                exact_same_time = t1.due_time == t2.due_time
                with st.container(border=True):
                    if exact_same_time:
                        st.error(
                            f"Both tasks start at exactly **{t1.due_time}** "
                            f"and cannot run simultaneously."
                        )
                    else:
                        st.warning(
                            f"**{t1.description}** ({t1.due_time}, {t1.duration_minutes} min) "
                            f"overlaps with **{t2.description}** ({t2.due_time}, {t2.duration_minutes} min)."
                        )
                    col_a, col_b = st.columns(2)
                    with col_a:
                        st.markdown(f"**{t1.description}**")
                        st.caption(
                            f"Pet: {t1.pet_name} · Start: {t1.due_time} "
                            f"· {t1.duration_minutes} min · Priority {t1.priority}"
                        )
                    with col_b:
                        st.markdown(f"**{t2.description}**")
                        st.caption(
                            f"Pet: {t2.pet_name} · Start: {t2.due_time} "
                            f"· {t2.duration_minutes} min · Priority {t2.priority}"
                        )
                    st.info(
                        f"💡 Suggested fix: reschedule **{reschedule.description}** "
                        f"({reschedule.pet_name}) — it has the lower priority of the two."
                    )
        else:
            st.success("No schedule conflicts — all tasks have distinct time windows.")

        remove_from_pet = st.selectbox("Remove a task from pet", [p.name for p in owner.pets], key="remove_task_pet")
        remove_pet_obj = owner.get_pet(remove_from_pet)
        if remove_pet_obj and remove_pet_obj.tasks:
            task_to_remove = st.selectbox("Select task to remove", [t.description for t in remove_pet_obj.tasks], key="remove_task_select")
            if st.button("Remove Task"):
                remove_pet_obj.remove_task(task_to_remove)
                save_state()
                st.success(f"Removed '{task_to_remove}' from {remove_from_pet}.")
    else:
        st.info("No tasks yet. Add one above.")

st.divider()

# ── Step 4: Mark a Task Complete ─────────────────────────────────────────────
st.subheader("Mark Task Complete")

all_tasks = owner.get_all_tasks()
pending_tasks = scheduler.sort_tasks(scheduler.filter_tasks(all_tasks, completed=False))

if not pending_tasks:
    st.info("No pending tasks to complete.")
else:
    task_labels = [f"{t.description} ({t.pet_name}) @ {t.due_time}" for t in pending_tasks]
    selected_label = st.selectbox("Select a task to mark complete", task_labels)
    selected_task = pending_tasks[task_labels.index(selected_label)]

    with st.container(border=True):
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Pet", selected_task.pet_name)
        c2.metric("Due", selected_task.due_time)
        c3.metric("Duration", f"{selected_task.duration_minutes} min")
        c4.metric("Priority", selected_task.priority)

    if st.button("Mark Complete"):
        pet = owner.get_pet(selected_task.pet_name)
        next_task = scheduler.mark_task_complete(selected_task, pet, date.today())
        save_state()
        if next_task:
            st.success(
                f"'{selected_task.description}' marked complete! "
                f"Next occurrence scheduled for {next_task.due_date}."
            )
        else:
            st.success(f"'{selected_task.description}' marked complete!")

    if st.button("Mark All Complete"):
        scheduler.mark_all_complete(pending_tasks)
        save_state()
        st.success(f"All {len(pending_tasks)} pending task(s) marked complete.")

all_tasks = owner.get_all_tasks()
if st.button("Reset Daily Tasks"):
    scheduler.reset_completed(all_tasks)
    save_state()
    st.success("Recurring tasks reset for a new day.")

st.divider()

# ── Step 5: Generate Schedule ────────────────────────────────────────────────
st.subheader("Build Schedule")

# High-priority task alert banner
all_tasks = owner.get_all_tasks()
urgent = scheduler.get_high_priority_tasks(all_tasks, min_priority=4)
if urgent:
    st.error(f"🚨 {len(urgent)} high-priority task(s) need attention")
    st.dataframe(
        [{"Task": t.description, "Pet": t.pet_name, "Due": t.due_time, "Priority": t.priority} for t in urgent],
        width='stretch',
        hide_index=True,
    )

schedule_date = st.date_input("Schedule date", value=date.today())

if st.button("Generate schedule"):
    plan = scheduler.generate_daily_plan(owner, schedule_date)

    # Budget summary
    remaining = plan["time_budget"] - plan["time_used"]
    m1, m2, m3 = st.columns(3)
    m1.metric("Budget", f"{plan['time_budget']} min")
    m2.metric("Time Used", f"{plan['time_used']} min")
    m3.metric("Remaining", f"{remaining} min")

    st.divider()

    # Scheduled tasks
    if plan["scheduled"]:
        st.success(f"{len(plan['scheduled'])} task(s) scheduled for {plan['date']}")
        st.dataframe(
            [
                {
                    "Time": t.due_time,
                    "Task": t.description,
                    "Pet": t.pet_name,
                    "Duration": f"{t.duration_minutes} min",
                    "Priority": t.priority,
                    "Frequency": t.frequency.capitalize(),
                }
                for t in plan["scheduled"]
            ],
            width='stretch',
            hide_index=True,
        )
    else:
        st.info("No tasks scheduled for this day.")

    # Skipped tasks
    skipped_over_budget = [t for t in plan["skipped"] if not t.completed]
    skipped_done = [t for t in plan["skipped"] if t.completed]

    if skipped_over_budget:
        st.warning(f"{len(skipped_over_budget)} task(s) skipped — insufficient time remaining")
        st.dataframe(
            [{"Task": t.description, "Pet": t.pet_name, "Duration": f"{t.duration_minutes} min", "Priority": t.priority} for t in skipped_over_budget],
            width='stretch',
            hide_index=True,
        )

    if skipped_done:
        st.info(f"{len(skipped_done)} task(s) already completed and excluded from plan")

    # Budget warnings for high-priority skips
    for w in plan["warnings"]:
        st.error(f"⚠️ {w}")
