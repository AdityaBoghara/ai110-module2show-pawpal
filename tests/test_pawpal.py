import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from pawpal_system import Task, Pet


def test_mark_complete_changes_status():
    """Task Completion: mark_complete() should set completed to True."""
    task = Task(
        description="Morning walk",
        duration_minutes=30,
        priority=3,
        due_time="08:00",
        pet_name="Buddy",
    )
    assert task.completed is False
    task.mark_complete()
    assert task.completed is True


def test_add_task_increases_pet_task_count():
    """Task Addition: adding a task to a Pet should increase its task count."""
    pet = Pet(name="Buddy", species="dog")
    assert len(pet.tasks) == 0

    task = Task(
        description="Evening feed",
        duration_minutes=10,
        priority=2,
        due_time="18:00",
        pet_name="Buddy",
    )
    pet.add_task(task)
    assert len(pet.tasks) == 1
