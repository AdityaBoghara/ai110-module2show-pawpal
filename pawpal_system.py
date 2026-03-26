"""
PawPal+ - Pet Care Task Scheduling System

Core classes for managing pet owners, pets, tasks, and scheduling.
This is the central logic layer that handles the domain model.
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import List, Dict


@dataclass
class Task:
    """
    Represents a single pet care task.

    A task is a unit of work tied to a specific pet with duration,
    priority, and timing constraints.
    """

    title: str
    duration_minutes: int
    priority: int
    due_time: str
    pet_name: str
    completed: bool = False

    def mark_complete(self):
        """Mark this task as completed."""
        self.completed = True

    def is_due_today(self, date):
        """Check if this task is due on a given date.

        Since tasks store only a time (not a full date), all tasks are
        treated as daily and are always considered due today.
        """
        return True

    def to_dict(self):
        """Convert task to dictionary representation."""
        return {
            "title": self.title,
            "duration_minutes": self.duration_minutes,
            "priority": self.priority,
            "due_time": self.due_time,
            "pet_name": self.pet_name,
            "completed": self.completed,
        }


@dataclass
class Pet:
    """
    Represents a pet and its associated care tasks.

    A pet serves as a container for managing all tasks related to that animal,
    and tracks the pet's basic information.
    """

    name: str
    tasks: List[Task] = field(default_factory=list)

    def add_task(self, task):
        """Add a task to this pet's task list.

        Enforces that task.pet_name matches this pet's name to prevent
        silent data inconsistency between the task and its owning pet.
        """
        if task.pet_name != self.name:
            raise ValueError(
                f"Task pet_name '{task.pet_name}' does not match pet name '{self.name}'"
            )
        self.tasks.append(task)

    def get_tasks(self):
        """Get all tasks for this pet."""
        return list(self.tasks)

    def get_tasks_for_today(self, date):
        """Get tasks due today for this pet."""
        return [task for task in self.tasks if task.is_due_today(date)]


@dataclass
class Owner:
    """
    Represents a pet owner who manages one or more pets.

    An owner aggregates multiple pets and has a time budget constraint
    for managing daily pet care tasks.
    """

    name: str
    daily_time_budget: int
    pets: List[Pet] = field(default_factory=list)

    def add_pet(self, pet):
        """Add a pet to this owner's collection."""
        self.pets.append(pet)

    def get_all_tasks(self):
        """Get all tasks across all pets."""
        return [task for pet in self.pets for task in pet.get_tasks()]

    def get_due_tasks(self, date):
        """Get all tasks due on a specific date across all pets."""
        return [task for pet in self.pets for task in pet.get_tasks_for_today(date)]


class Scheduler:
    """
    Core scheduling logic for generating daily pet care plans.

    A stateless utility class that produces optimal schedules based on
    owner constraints, task properties, and scheduling strategies.
    """

    def sort_tasks(self, tasks):
        """
        Sort tasks by priority (descending) then due time (ascending).

        Higher priority numbers are scheduled first. Tasks with unparseable
        due_time strings are sorted last.

        Args:
            tasks: List of tasks to sort

        Returns:
            Sorted list of tasks
        """
        def sort_key(task):
            try:
                due = datetime.strptime(task.due_time, "%H:%M")
            except ValueError:
                due = datetime.max
            return (-task.priority, due)

        return sorted(tasks, key=sort_key)

    def generate_daily_plan(self, owner, date):
        """
        Generate a daily care plan for an owner.

        Greedily schedules tasks in priority/time order until the owner's
        daily_time_budget is exhausted. Already-completed tasks are skipped.

        Args:
            owner: The pet owner
            date: The date to plan for

        Returns:
            Dictionary with keys:
              "scheduled"   — list of Task objects to be done
              "skipped"     — list of Task objects that did not fit or are done
              "time_used"   — total minutes scheduled
              "time_budget" — owner's daily time budget in minutes
              "date"        — the date this plan is for
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

        return {
            "scheduled": scheduled,
            "skipped": skipped,
            "time_used": time_used,
            "time_budget": owner.daily_time_budget,
            "date": date,
        }

    def detect_conflicts(self, tasks):
        """
        Identify scheduling conflicts in a task list.

        Two tasks conflict when their time windows overlap, i.e.
        [due_time, due_time + duration) intersects for both tasks.
        Tasks with unparseable due_time strings are skipped.

        Args:
            tasks: List of tasks to check

        Returns:
            List of (Task, Task) tuples that have overlapping time windows
        """
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

    def explain_plan(self, plan):
        """
        Generate a human-readable explanation of the schedule.

        Args:
            plan: Dictionary returned by generate_daily_plan

        Returns:
            Multi-line string describing scheduled and skipped tasks
        """
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
                    f"  [{task.due_time}] {task.title} ({task.pet_name})"
                    f" — {task.duration_minutes} min, priority {task.priority}"
                )
        else:
            lines.append("No tasks scheduled.")

        lines.append("")

        if plan["skipped"]:
            lines.append("Skipped tasks:")
            for task in plan["skipped"]:
                reason = "already completed" if task.completed else "insufficient time remaining"
                lines.append(f"  {task.title} ({task.pet_name}) — {reason}")
        else:
            lines.append("No tasks were skipped.")

        return "\n".join(lines)
