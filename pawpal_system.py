"""
PawPal+ - Pet Care Task Scheduling System

Core classes for managing pet owners, pets, tasks, and scheduling.
This is the central logic layer that handles the domain model.
"""

from dataclasses import dataclass, field
from datetime import datetime
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
        pass

    def is_due_today(self, date):
        """Check if this task is due on a given date."""
        pass

    def to_dict(self):
        """Convert task to dictionary representation."""
        pass


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
        """Add a task to this pet's task list."""
        pass

    def get_tasks(self):
        """Get all tasks for this pet."""
        pass

    def get_tasks_for_today(self, date):
        """Get tasks due today for this pet."""
        pass


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
        pass

    def get_all_tasks(self):
        """Get all tasks across all pets."""
        pass

    def get_due_tasks(self, date):
        """Get all tasks due on a specific date across all pets."""
        pass


class Scheduler:
    """
    Core scheduling logic for generating daily pet care plans.

    A stateless utility class that produces optimal schedules based on
    owner constraints, task properties, and scheduling strategies.
    """

    def sort_tasks(self, tasks):
        """
        Sort tasks by priority and due time.

        Args:
            tasks: List of tasks to sort

        Returns:
            Sorted list of tasks
        """
        pass

    def generate_daily_plan(self, owner, date):
        """
        Generate a daily care plan for an owner.

        Considers time budget, task durations, and priorities to create
        a feasible schedule for the given date.

        Args:
            owner: The pet owner
            date: The date to plan for

        Returns:
            Dictionary containing scheduled tasks and skipped tasks
        """
        pass

    def detect_conflicts(self, tasks):
        """
        Identify scheduling conflicts in a task list.

        Args:
            tasks: List of tasks to check

        Returns:
            List of conflicting task pairs
        """
        pass

    def explain_plan(self, plan):
        """
        Generate a human-readable explanation of the schedule.

        Args:
            plan: The generated daily plan

        Returns:
            Explanation text describing the plan and decisions
        """
        pass
