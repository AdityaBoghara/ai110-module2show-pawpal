"""
PawPal+ - Pet Care Task Scheduling System

Core classes for managing pet owners, pets, tasks, and scheduling.
This is the central logic layer that handles the domain model.
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import List, Dict


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
    """

    description: str
    duration_minutes: int
    priority: int
    due_time: str
    pet_name: str
    frequency: str = "daily"   # "daily" | "weekly" | "once"
    completed: bool = False

    def mark_complete(self):
        """Mark this task as completed."""
        self.completed = True

    def is_due_today(self, date):
        """Return True if this task is due on the given date."""
        return True

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

    def add_pet(self, pet: Pet):
        """Register a pet with this owner."""
        self.pets.append(pet)

    def remove_pet(self, name: str) -> bool:
        """Remove a pet by name. Returns True if found and removed."""
        for i, pet in enumerate(self.pets):
            if pet.name.lower() == name.lower():
                self.pets.pop(i)
                return True
        return False

    def get_pet(self, name: str):
        """Return a pet by name, or None if not found."""
        for pet in self.pets:
            if pet.name.lower() == name.lower():
                return pet
        return None

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
        return {
            "owner": self.name,
            "pets": len(self.pets),
            "total_tasks": len(all_tasks),
            "completed_tasks": sum(1 for t in all_tasks if t.completed),
            "pending_tasks": sum(1 for t in all_tasks if not t.completed),
            "daily_time_budget": self.daily_time_budget,
        }

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

    def sort_tasks(self, tasks: List[Task]) -> List[Task]:
        """Sort tasks by priority descending, then due_time ascending (unparseable times last)."""
        def sort_key(task):
            try:
                due = datetime.strptime(task.due_time, "%H:%M")
            except ValueError:
                due = datetime.max
            return (-task.priority, due)

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
        """Build a greedy daily schedule fitting tasks within the owner's time budget."""
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

        return {
            "scheduled": scheduled,
            "skipped": skipped,
            "time_used": time_used,
            "time_budget": owner.daily_time_budget,
            "date": date,
        }

    # ── Conflict detection ───────────────────────────────────────────────

    def detect_conflicts(self, tasks: List[Task]) -> List[tuple]:
        """Return (Task, Task) pairs whose time windows overlap."""
        conflicts = []
        for i in range(len(tasks)):
            for j in range(i + 1, len(tasks)):
                t1, t2 = tasks[i], tasks[j]
                try:
                    start1 = datetime.strptime(t1.due_time, "%H:%M")
                    start2 = datetime.strptime(t2.due_time, "%H:%M")
                except ValueError:
                    continue
                end1 = start1 + timedelta(minutes=t1.duration_minutes)
                end2 = start2 + timedelta(minutes=t2.duration_minutes)
                if start1 < end2 and start2 < end1:
                    conflicts.append((t1, t2))
        return conflicts

    # ── Bulk task management ─────────────────────────────────────────────

    def mark_all_complete(self, tasks: List[Task]):
        """Mark every task in the list as completed."""
        for task in tasks:
            task.mark_complete()

    def reset_completed(self, tasks: List[Task]):
        """Reset the completed flag on all tasks (useful for a new day)."""
        for task in tasks:
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

        return "\n".join(lines)
