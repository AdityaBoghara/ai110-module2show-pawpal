"""
PawPal+ - Pet Care Task Scheduling System

Core classes for managing pet owners, pets, tasks, and scheduling.
This is the central logic layer that handles the domain model.
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta, date as date_type
from typing import List, Dict, Optional


# ── Task ────────────────────────────────────────────────────────────────────

@dataclass
class Task:
    """
    Represents a single pet care activity.

    Attributes:
        description:       What needs to be done (e.g. "Morning walk").
        duration_minutes:  How long the activity takes.
        priority:          Scheduling importance (higher = scheduled first).
        due_time:          Time-of-day string in "HH:MM" 24-hour format.
        pet_name:          The name of the pet this task belongs to.
        frequency:         How often the task recurs: "daily", "weekly", or "once".
        completed:         Whether the task has been marked done.
        due_date:          Anchor date for "once" (exact match) and "weekly" (same weekday) tasks.
    """

    description: str
    duration_minutes: int
    priority: int
    due_time: str
    pet_name: str
    frequency: str = "daily"   # "daily" | "weekly" | "once"
    completed: bool = False
    due_date: Optional[date_type] = None  # anchor date for "once"/"weekly" tasks

    def mark_complete(self):
        """Mark this task as completed."""
        self.completed = True

    def is_due_today(self, date) -> bool:
        """Determine whether this task falls on the given calendar date.

        Applies different recurrence rules based on the task's frequency:
        - ``daily``  — always due regardless of the date.
        - ``once``   — due only on the exact ``due_date`` (or any day if
                       ``due_date`` is None).
        - ``weekly`` — due on any date whose weekday matches ``due_date``'s
                       weekday (or any day if ``due_date`` is None).

        Args:
            date: A :class:`datetime.date` object representing the day to check.

        Returns:
            ``True`` if the task should appear on the given date, ``False``
            otherwise.
        """
        if self.frequency == "daily":
            return True
        if self.frequency == "once":
            return self.due_date == date if self.due_date is not None else True
        if self.frequency == "weekly":
            if self.due_date is not None:
                return date.weekday() == self.due_date.weekday()
            return True
        return False

    def to_dict(self):
        """Return a plain-dict representation of this task."""
        return {
            "description": self.description,
            "duration_minutes": self.duration_minutes,
            "priority": self.priority,
            "due_time": self.due_time,
            "pet_name": self.pet_name,
            "frequency": self.frequency,
            "completed": self.completed,
            "due_date": self.due_date.isoformat() if self.due_date is not None else None,
        }

    def __str__(self):
        status = "✓" if self.completed else "○"
        return (
            f"[{status}] {self.description} ({self.pet_name}) "
            f"@ {self.due_time} — {self.duration_minutes} min, "
            f"priority {self.priority}, {self.frequency}"
        )


# ── Pet ─────────────────────────────────────────────────────────────────────

@dataclass
class Pet:
    """
    Stores pet details and its list of care tasks.

    Attributes:
        name:    The pet's name.
        species: The type of animal (e.g. "dog", "cat", "rabbit").
        tasks:   All care tasks associated with this pet.
    """

    name: str
    species: str = "unknown"
    tasks: List[Task] = field(default_factory=list)

    def add_task(self, task: Task):
        """Append a task to this pet's list, raising ValueError if pet_name mismatches."""
        if task.pet_name != self.name:
            raise ValueError(
                f"Task pet_name '{task.pet_name}' does not match pet name '{self.name}'"
            )
        self.tasks.append(task)

    def remove_task(self, description: str):
        """Remove the first task whose description matches (case-insensitive)."""
        for i, task in enumerate(self.tasks):
            if task.description.lower() == description.lower():
                self.tasks.pop(i)
                return True
        return False

    def get_tasks(self) -> List[Task]:
        """Return a copy of all tasks for this pet."""
        return list(self.tasks)

    def get_pending_tasks(self) -> List[Task]:
        """Return only incomplete tasks."""
        return [t for t in self.tasks if not t.completed]

    def get_tasks_for_today(self, date) -> List[Task]:
        """Return tasks due today for this pet."""
        return [t for t in self.tasks if t.is_due_today(date)]

    def to_dict(self):
        return {"name": self.name, "species": self.species, "tasks": [t.to_dict() for t in self.tasks]}

    @classmethod
    def from_dict(cls, data):
        from datetime import date as date_type
        pet = cls(name=data["name"], species=data.get("species", "unknown"))
        for td in data.get("tasks", []):
            due_date = date_type.fromisoformat(td["due_date"]) if td.get("due_date") else None
            pet.tasks.append(Task(
                description=td["description"],
                duration_minutes=td["duration_minutes"],
                priority=td["priority"],
                due_time=td["due_time"],
                pet_name=td["pet_name"],
                frequency=td.get("frequency", "daily"),
                completed=td.get("completed", False),
                due_date=due_date,
            ))
        return pet

    def __str__(self):
        return f"{self.name} ({self.species}) — {len(self.tasks)} task(s)"


# ── Owner ────────────────────────────────────────────────────────────────────

@dataclass
class Owner:
    """
    Manages multiple pets and provides access to all their tasks.

    Attributes:
        name:              The owner's display name.
        daily_time_budget: Maximum minutes available for pet care each day.
        pets:              All pets this owner is responsible for.
    """

    name: str
    daily_time_budget: int
    pets: List[Pet] = field(default_factory=list)
    _pet_index: Dict[str, Pet] = field(default_factory=dict, init=False, repr=False)

    def __post_init__(self):
        self._pet_index = {pet.name.lower(): pet for pet in self.pets}

    def add_pet(self, pet: Pet):
        """Register a pet with this owner."""
        self.pets.append(pet)
        self._pet_index[pet.name.lower()] = pet

    def remove_pet(self, name: str) -> bool:
        """Remove a pet by name. Returns True if found and removed."""
        key = name.lower()
        if key in self._pet_index:
            pet = self._pet_index.pop(key)
            self.pets.remove(pet)
            return True
        return False

    def get_pet(self, name: str):
        """Return a pet by name, or None if not found."""
        return self._pet_index.get(name.lower())

    def get_all_tasks(self) -> List[Task]:
        """Aggregate and return every task across all pets."""
        return [task for pet in self.pets for task in pet.get_tasks()]

    def get_due_tasks(self, date) -> List[Task]:
        """Return all tasks due on a specific date across all pets."""
        return [task for pet in self.pets for task in pet.get_tasks_for_today(date)]

    def get_pending_tasks(self) -> List[Task]:
        """Return all incomplete tasks across all pets."""
        return [task for pet in self.pets for task in pet.get_pending_tasks()]

    def summary(self) -> Dict:
        """Return a quick stats summary for this owner."""
        all_tasks = self.get_all_tasks()
        completed = sum(1 for t in all_tasks if t.completed)
        return {
            "owner": self.name,
            "pets": len(self.pets),
            "total_tasks": len(all_tasks),
            "completed_tasks": completed,
            "pending_tasks": len(all_tasks) - completed,
            "daily_time_budget": self.daily_time_budget,
        }

    def to_dict(self):
        return {"name": self.name, "daily_time_budget": self.daily_time_budget, "pets": [p.to_dict() for p in self.pets]}

    @classmethod
    def from_dict(cls, data):
        owner = cls(name=data["name"], daily_time_budget=data["daily_time_budget"])
        for pd in data.get("pets", []):
            owner.add_pet(Pet.from_dict(pd))
        return owner

    def __str__(self):
        return (
            f"Owner: {self.name} | Budget: {self.daily_time_budget} min/day "
            f"| Pets: {len(self.pets)}"
        )


# ── Scheduler ────────────────────────────────────────────────────────────────

class Scheduler:
    """
    The "brain" that retrieves, organises, and manages tasks across pets.

    A stateless utility class that produces optimal daily schedules based on
    owner constraints, task priorities, and timing information.
    """

    # ── Sorting / retrieval ──────────────────────────────────────────────

    def sort_by_time(self, tasks: List[Task]) -> List[Task]:
        """Sort tasks by due_time ascending using a lambda key on 'HH:MM' strings."""
        return sorted(tasks, key=lambda t: t.due_time if t.due_time else "99:99")

    def filter_tasks(
        self,
        tasks: List[Task],
        completed: Optional[bool] = None,
        pet_name: Optional[str] = None,
    ) -> List[Task]:
        """Filter tasks by completion status and/or pet name.

        Args:
            tasks:     Source list of Task objects.
            completed: If True, return only completed tasks; if False, only pending;
                       if None, no status filter is applied.
            pet_name:  If provided, return only tasks for that pet (case-insensitive).
        """
        result = tasks
        if completed is not None:
            result = [t for t in result if t.completed == completed]
        if pet_name is not None:
            result = [t for t in result if t.pet_name.lower() == pet_name.lower()]
        return result

    def sort_tasks(self, tasks: List[Task]) -> List[Task]:
        """Sort tasks using a three-level key to maximise schedule quality.

        Ordering rules applied left-to-right:
        1. **Priority descending** — higher-priority tasks are scheduled first
           so they are never crowded out by lower-priority ones.
        2. **Due time ascending** — among equal-priority tasks, earlier
           start times appear first.
        3. **Duration ascending** — when both priority and time are equal,
           shorter tasks appear first, allowing more tasks to fit within the
           time budget.

        Tasks with an unparseable ``due_time`` are placed at the end of the
        list (sorted as if their time were ``datetime.max``).

        Args:
            tasks: An unsorted list of :class:`Task` objects.

        Returns:
            A new list containing the same tasks in the sorted order.
        """
        def sort_key(task):
            try:
                due = datetime.strptime(task.due_time, "%H:%M")
            except ValueError:
                due = datetime.max
            return (-task.priority, due, task.duration_minutes)

        return sorted(tasks, key=sort_key)

    def get_tasks_by_frequency(self, tasks: List[Task], frequency: str) -> List[Task]:
        """Return only tasks that match the given frequency string."""
        return [t for t in tasks if t.frequency == frequency]

    def get_high_priority_tasks(self, tasks: List[Task], min_priority: int = 4) -> List[Task]:
        """Return tasks at or above min_priority, sorted by priority desc."""
        high = [t for t in tasks if t.priority >= min_priority]
        return sorted(high, key=lambda t: -t.priority)

    # ── Core scheduling ──────────────────────────────────────────────────

    def generate_daily_plan(self, owner: Owner, date) -> Dict:
        """Build a greedy daily schedule fitting tasks within the owner's time budget.

        Algorithm:
        1. Retrieve all tasks due on ``date`` via :meth:`Owner.get_due_tasks`.
        2. Sort them with :meth:`sort_tasks` (priority ↓, due_time ↑, duration ↑).
        3. Iterate through the sorted list; greedily add each pending task to the
           schedule until ``owner.daily_time_budget`` minutes are exhausted.
           Already-completed tasks are moved directly to the *skipped* list.
        4. Collect warning messages for any high-priority (≥ 4) tasks that had to
           be skipped due to insufficient remaining budget.

        Args:
            owner: The :class:`Owner` whose pets and time budget are used.
            date:  A :class:`datetime.date` representing the target day.

        Returns:
            A dictionary with the following keys:

            - ``scheduled`` (:class:`list[Task]`) — tasks added to the plan.
            - ``skipped``   (:class:`list[Task]`) — tasks excluded from the plan.
            - ``time_used`` (:class:`int`)         — total minutes scheduled.
            - ``time_budget`` (:class:`int`)        — the owner's daily limit.
            - ``date``      (:class:`datetime.date`) — the target date.
            - ``warnings``  (:class:`list[str]`)   — human-readable alerts for
              skipped high-priority tasks.
        """
        due_tasks = owner.get_due_tasks(date)
        sorted_tasks = self.sort_tasks(due_tasks)

        scheduled = []
        skipped = []
        time_used = 0

        for task in sorted_tasks:
            if task.completed:
                skipped.append(task)
                continue
            if time_used + task.duration_minutes <= owner.daily_time_budget:
                scheduled.append(task)
                time_used += task.duration_minutes
            else:
                skipped.append(task)

        skipped_high_priority = [t for t in skipped if t.priority >= 4 and not t.completed]
        warnings = [
            f"High-priority task skipped due to time budget: {t.description} ({t.pet_name})"
            for t in skipped_high_priority
        ]

        return {
            "scheduled": scheduled,
            "skipped": skipped,
            "time_used": time_used,
            "time_budget": owner.daily_time_budget,
            "date": date,
            "warnings": warnings,
        }

    # ── Conflict detection ───────────────────────────────────────────────

    def check_same_time_conflicts(self, tasks: List[Task]) -> List[str]:
        """Lightweight check: return warning strings for any two tasks sharing the same due_time.

        Strategy: group tasks by due_time string; any group with more than one task is a
        conflict.  Returns a list of human-readable warning messages — never raises.
        """
        from collections import defaultdict
        time_buckets: Dict[str, List[Task]] = defaultdict(list)
        for task in tasks:
            if task.due_time:
                time_buckets[task.due_time].append(task)

        warnings = []
        for due_time, group in time_buckets.items():
            if len(group) > 1:
                names = ", ".join(f"'{t.description}' ({t.pet_name})" for t in group)
                warnings.append(
                    f"WARNING: {len(group)} tasks share the same start time {due_time}: {names}"
                )
        return warnings

    def detect_conflicts(self, tasks: List[Task]) -> List[tuple]:
        """Detect all pairwise time-window overlaps using an O(n²) sweep.

        For every pair of tasks ``(t1, t2)``, the algorithm parses their
        ``due_time`` strings into :class:`datetime` objects, computes end
        times as ``start + duration``, and checks the standard overlap
        condition::

            start1 < end2  and  start2 < end1

        When an overlap is found, the task with the *lower* priority is
        flagged as the candidate to reschedule.  If both tasks share the
        same priority, ``t1`` is chosen as the reschedule candidate.

        Tasks with an unparseable ``due_time`` are silently skipped.

        Args:
            tasks: A list of :class:`Task` objects to check against each other.

        Returns:
            A list of ``(t1, t2, reschedule)`` tuples where ``t1`` and ``t2``
            are the overlapping tasks and ``reschedule`` is the lower-priority
            of the two (suggested candidate for rescheduling).
        """
        from itertools import combinations

        def parse_window(task):
            try:
                start = datetime.strptime(task.due_time, "%H:%M")
                return start, start + timedelta(minutes=task.duration_minutes)
            except ValueError:
                return None

        # Parse each task's time window exactly once — O(n) instead of O(n²) parses
        parsed = [(task, parse_window(task)) for task in tasks]
        valid_tasks = [(task, window) for task, window in parsed if window is not None]

        conflicts = []
        for (t1, (start1, end1)), (t2, (start2, end2)) in combinations(valid_tasks, 2):
            if start1 < end2 and start2 < end1:
                reschedule = t1 if t1.priority <= t2.priority else t2
                conflicts.append((t1, t2, reschedule))
        return conflicts

    # ── Bulk task management ─────────────────────────────────────────────

    def mark_task_complete(self, task: Task, pet: "Pet", today: Optional[date_type] = None) -> Optional["Task"]:
        """Mark a task complete and auto-create the next occurrence for recurring tasks.

        For 'daily' tasks  → new instance due tomorrow (today + 1 day).
        For 'weekly' tasks → new instance due in 7 days (today + 7 days).
        For 'once' tasks   → just marks complete; no new instance is created.

        Args:
            task:  The Task to mark complete.
            pet:   The Pet that owns the task (new instance is added here).
            today: Reference date; defaults to date.today() if omitted.

        Returns:
            The newly created Task for the next occurrence, or None for 'once' tasks.
        """
        task.mark_complete()

        if task.frequency == "once":
            return None

        reference_date = today if today is not None else date_type.today()

        if task.frequency == "daily":
            next_due_date = reference_date + timedelta(days=1)
        else:  # "weekly"
            next_due_date = reference_date + timedelta(weeks=1)

        next_task = Task(
            description=task.description,
            duration_minutes=task.duration_minutes,
            priority=task.priority,
            due_time=task.due_time,
            pet_name=task.pet_name,
            frequency=task.frequency,
            completed=False,
            due_date=next_due_date,
        )
        pet.add_task(next_task)
        return next_task

    def mark_all_complete(self, tasks: List[Task]):
        """Mark every task in the list as completed."""
        for task in tasks:
            task.mark_complete()

    def reset_completed(self, tasks: List[Task]):
        """Reset the completed flag on recurring tasks only; leaves 'once' tasks unchanged."""
        for task in tasks:
            if task.frequency != "once":
                task.completed = False

    # ── Explanation ──────────────────────────────────────────────────────

    def explain_plan(self, plan: Dict) -> str:
        """Return a human-readable multi-line summary of scheduled and skipped tasks."""
        lines = []
        lines.append(f"Daily Care Plan — {plan['date']}")
        lines.append(
            f"Time budget: {plan['time_budget']} min  |  "
            f"Time used: {plan['time_used']} min  |  "
            f"Remaining: {plan['time_budget'] - plan['time_used']} min"
        )
        lines.append("")

        if plan["scheduled"]:
            lines.append("Scheduled tasks:")
            for task in plan["scheduled"]:
                lines.append(
                    f"  [{task.due_time}] {task.description} ({task.pet_name})"
                    f" — {task.duration_minutes} min, priority {task.priority}"
                    f", {task.frequency}"
                )
        else:
            lines.append("No tasks scheduled.")

        lines.append("")

        if plan["skipped"]:
            lines.append("Skipped tasks:")
            for task in plan["skipped"]:
                reason = "already completed" if task.completed else "insufficient time remaining"
                lines.append(f"  {task.description} ({task.pet_name}) — {reason}")
        else:
            lines.append("No tasks were skipped.")

        if plan.get("warnings"):
            lines.append("")
            lines.append("Warnings:")
            for warning in plan["warnings"]:
                lines.append(f"  ⚠ {warning}")

        return "\n".join(lines)
