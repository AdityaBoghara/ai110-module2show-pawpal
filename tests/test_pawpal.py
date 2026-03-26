import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
from datetime import date, timedelta
from pawpal_system import Task, Pet, Owner, Scheduler


# ── Fixtures ─────────────────────────────────────────────────────────────────

@pytest.fixture
def daily_task():
    return Task(
        description="Morning walk",
        duration_minutes=30,
        priority=3,
        due_time="08:00",
        pet_name="Buddy",
        frequency="daily",
    )

@pytest.fixture
def buddy():
    return Pet(name="Buddy", species="dog")

@pytest.fixture
def whiskers():
    return Pet(name="Whiskers", species="cat")

@pytest.fixture
def owner(buddy, whiskers):
    o = Owner(name="Alex", daily_time_budget=120)
    o.add_pet(buddy)
    o.add_pet(whiskers)
    return o

@pytest.fixture
def scheduler():
    return Scheduler()

@pytest.fixture
def today():
    return date.today()


# ══════════════════════════════════════════════════════════════════════════════
# Task
# ══════════════════════════════════════════════════════════════════════════════

class TestTaskMarkComplete:
    def test_initial_state_is_false(self, daily_task):
        """Task starts incomplete."""
        assert daily_task.completed is False

    def test_mark_complete_changes_status(self, daily_task):
        """mark_complete() sets completed to True."""
        daily_task.mark_complete()
        assert daily_task.completed is True

    def test_mark_complete_idempotent(self, daily_task):
        """Calling mark_complete() twice keeps completed True."""
        daily_task.mark_complete()
        daily_task.mark_complete()
        assert daily_task.completed is True


class TestTaskIsDueToday:
    def test_daily_always_due(self, today):
        task = Task("Feed", 10, 3, "08:00", "Buddy", frequency="daily")
        assert task.is_due_today(today) is True

    def test_daily_due_on_any_date(self):
        task = Task("Feed", 10, 3, "08:00", "Buddy", frequency="daily")
        assert task.is_due_today(date(2020, 1, 1)) is True

    def test_once_due_on_exact_date(self, today):
        task = Task("Vet", 60, 5, "14:00", "Buddy", frequency="once", due_date=today)
        assert task.is_due_today(today) is True

    def test_once_not_due_on_different_date(self, today):
        task = Task("Vet", 60, 5, "14:00", "Buddy", frequency="once", due_date=today)
        assert task.is_due_today(today + timedelta(days=1)) is False

    def test_once_no_due_date_is_due_any_day(self, today):
        task = Task("Vet", 60, 5, "14:00", "Buddy", frequency="once", due_date=None)
        assert task.is_due_today(today) is True

    def test_weekly_due_on_matching_weekday(self, today):
        task = Task("Groom", 20, 2, "10:00", "Buddy", frequency="weekly", due_date=today)
        assert task.is_due_today(today) is True

    def test_weekly_due_seven_days_later(self, today):
        task = Task("Groom", 20, 2, "10:00", "Buddy", frequency="weekly", due_date=today)
        assert task.is_due_today(today + timedelta(weeks=1)) is True

    def test_weekly_not_due_on_wrong_weekday(self, today):
        task = Task("Groom", 20, 2, "10:00", "Buddy", frequency="weekly", due_date=today)
        # tomorrow has a different weekday
        assert task.is_due_today(today + timedelta(days=1)) is False

    def test_weekly_no_due_date_is_due_any_day(self, today):
        task = Task("Groom", 20, 2, "10:00", "Buddy", frequency="weekly", due_date=None)
        assert task.is_due_today(today) is True

    def test_weekly_due_across_year_boundary(self):
        """A weekly task anchored to a Monday in late December is due 7 days later
        in early January of the following year (weekday comparison is date-agnostic)."""
        anchor = date(2025, 12, 29)  # Monday
        next_monday = date(2026, 1, 5)   # Monday, next year
        not_tuesday = date(2026, 1, 6)   # Tuesday
        task = Task("Groom", 20, 2, "10:00", "Buddy", frequency="weekly", due_date=anchor)
        assert task.is_due_today(next_monday) is True
        assert task.is_due_today(not_tuesday) is False

    def test_unknown_frequency_returns_false(self, today):
        task = Task("Mystery", 10, 1, "09:00", "Buddy", frequency="monthly")
        assert task.is_due_today(today) is False


class TestTaskToDict:
    def test_keys_present(self, daily_task):
        d = daily_task.to_dict()
        assert set(d) == {
            "description", "duration_minutes", "priority",
            "due_time", "pet_name", "frequency", "completed", "due_date",
        }

    def test_values_match_fields(self, daily_task):
        d = daily_task.to_dict()
        assert d["description"] == "Morning walk"
        assert d["duration_minutes"] == 30
        assert d["priority"] == 3
        assert d["due_time"] == "08:00"
        assert d["pet_name"] == "Buddy"
        assert d["frequency"] == "daily"
        assert d["completed"] is False

    def test_due_date_none_serialises_as_none(self, daily_task):
        assert daily_task.to_dict()["due_date"] is None

    def test_due_date_serialises_as_isoformat(self, today):
        task = Task("Vet", 60, 5, "14:00", "Buddy", frequency="once", due_date=today)
        assert task.to_dict()["due_date"] == today.isoformat()


class TestTaskStr:
    def test_completed_shows_checkmark(self):
        task = Task("Feed", 10, 3, "08:00", "Buddy", completed=True)
        assert "✓" in str(task)

    def test_incomplete_shows_circle(self, daily_task):
        assert "○" in str(daily_task)

    def test_str_contains_description(self, daily_task):
        assert "Morning walk" in str(daily_task)


# ══════════════════════════════════════════════════════════════════════════════
# Pet
# ══════════════════════════════════════════════════════════════════════════════

class TestPetAddTask:
    def test_add_task_increases_count(self, buddy):
        assert len(buddy.tasks) == 0
        task = Task("Feed", 10, 2, "18:00", "Buddy")
        buddy.add_task(task)
        assert len(buddy.tasks) == 1

    def test_add_multiple_tasks(self, buddy):
        for i in range(3):
            buddy.add_task(Task(f"Task {i}", 10, 1, "08:00", "Buddy"))
        assert len(buddy.tasks) == 3

    def test_mismatched_pet_name_raises(self, buddy):
        wrong = Task("Feed", 10, 2, "18:00", pet_name="Whiskers")
        with pytest.raises(ValueError, match="does not match"):
            buddy.add_task(wrong)


class TestPetRemoveTask:
    def test_remove_existing_task_returns_true(self, buddy):
        buddy.add_task(Task("Feed", 10, 2, "18:00", "Buddy"))
        assert buddy.remove_task("Feed") is True
        assert len(buddy.tasks) == 0

    def test_remove_nonexistent_task_returns_false(self, buddy):
        assert buddy.remove_task("Nonexistent") is False

    def test_remove_is_case_insensitive(self, buddy):
        buddy.add_task(Task("Morning Walk", 30, 3, "07:00", "Buddy"))
        assert buddy.remove_task("morning walk") is True

    def test_remove_first_match_only(self, buddy):
        buddy.add_task(Task("Feed", 10, 2, "07:00", "Buddy"))
        buddy.add_task(Task("Feed", 10, 2, "18:00", "Buddy"))
        buddy.remove_task("Feed")
        assert len(buddy.tasks) == 1


class TestPetGetTasks:
    def test_get_tasks_returns_copy(self, buddy):
        buddy.add_task(Task("Feed", 10, 2, "08:00", "Buddy"))
        result = buddy.get_tasks()
        result.clear()
        assert len(buddy.tasks) == 1  # original unaffected

    def test_get_pending_tasks_excludes_completed(self, buddy):
        buddy.add_task(Task("Feed", 10, 2, "08:00", "Buddy", completed=True))
        buddy.add_task(Task("Walk", 30, 3, "07:00", "Buddy", completed=False))
        pending = buddy.get_pending_tasks()
        assert len(pending) == 1
        assert pending[0].description == "Walk"

    def test_get_tasks_for_today_daily(self, buddy, today):
        buddy.add_task(Task("Feed", 10, 2, "08:00", "Buddy", frequency="daily"))
        assert len(buddy.get_tasks_for_today(today)) == 1

    def test_get_tasks_for_today_once_wrong_date(self, buddy, today):
        buddy.add_task(Task("Vet", 60, 5, "14:00", "Buddy",
                            frequency="once", due_date=today + timedelta(days=1)))
        assert len(buddy.get_tasks_for_today(today)) == 0

    def test_pet_str_contains_name_and_species(self, buddy):
        assert "Buddy" in str(buddy)
        assert "dog" in str(buddy)


# ══════════════════════════════════════════════════════════════════════════════
# Owner
# ══════════════════════════════════════════════════════════════════════════════

class TestOwnerPetManagement:
    def test_add_pet_increments_count(self):
        o = Owner(name="Sam", daily_time_budget=60)
        o.add_pet(Pet("Max", "dog"))
        assert len(o.pets) == 1

    def test_get_pet_case_insensitive(self, owner):
        assert owner.get_pet("buddy") is not None
        assert owner.get_pet("BUDDY") is not None
        assert owner.get_pet("Buddy") is not None

    def test_get_pet_not_found_returns_none(self, owner):
        assert owner.get_pet("Unknown") is None

    def test_remove_pet_returns_true_when_found(self, owner):
        assert owner.remove_pet("Buddy") is True
        assert owner.get_pet("Buddy") is None
        assert len(owner.pets) == 1

    def test_remove_pet_returns_false_when_not_found(self, owner):
        assert owner.remove_pet("Ghost") is False

    def test_post_init_indexes_initial_pets(self):
        buddy = Pet("Buddy", "dog")
        o = Owner(name="Sam", daily_time_budget=60, pets=[buddy])
        assert o.get_pet("buddy") is buddy


class TestOwnerTaskAggregation:
    def test_get_all_tasks_spans_pets(self, owner, buddy, whiskers):
        buddy.add_task(Task("Walk", 30, 3, "07:00", "Buddy"))
        whiskers.add_task(Task("Feed", 5, 4, "08:00", "Whiskers"))
        assert len(owner.get_all_tasks()) == 2

    def test_get_due_tasks_filters_by_date(self, owner, buddy, today):
        buddy.add_task(Task("Walk", 30, 3, "07:00", "Buddy", frequency="daily"))
        buddy.add_task(Task("Vet", 60, 5, "14:00", "Buddy",
                            frequency="once", due_date=today + timedelta(days=5)))
        assert len(owner.get_due_tasks(today)) == 1

    def test_get_pending_tasks_excludes_done(self, owner, buddy):
        buddy.add_task(Task("Walk", 30, 3, "07:00", "Buddy", completed=True))
        buddy.add_task(Task("Feed", 10, 2, "08:00", "Buddy", completed=False))
        assert len(owner.get_pending_tasks()) == 1


class TestOwnerSummary:
    def test_summary_keys(self, owner):
        s = owner.summary()
        assert set(s) == {
            "owner", "pets", "total_tasks",
            "completed_tasks", "pending_tasks", "daily_time_budget",
        }

    def test_summary_counts(self, owner, buddy):
        buddy.add_task(Task("Walk", 30, 3, "07:00", "Buddy", completed=True))
        buddy.add_task(Task("Feed", 10, 2, "08:00", "Buddy", completed=False))
        s = owner.summary()
        assert s["total_tasks"] == 2
        assert s["completed_tasks"] == 1
        assert s["pending_tasks"] == 1

    def test_summary_no_tasks(self, owner):
        s = owner.summary()
        assert s["total_tasks"] == 0
        assert s["completed_tasks"] == 0
        assert s["pending_tasks"] == 0


# ══════════════════════════════════════════════════════════════════════════════
# Scheduler – sorting and filtering
# ══════════════════════════════════════════════════════════════════════════════

class TestSchedulerSortByTime:
    def test_sorts_ascending(self, scheduler):
        tasks = [
            Task("C", 10, 1, "18:00", "Buddy"),
            Task("A", 10, 1, "07:00", "Buddy"),
            Task("B", 10, 1, "12:00", "Buddy"),
        ]
        result = scheduler.sort_by_time(tasks)
        assert [t.due_time for t in result] == ["07:00", "12:00", "18:00"]

    def test_empty_list(self, scheduler):
        assert scheduler.sort_by_time([]) == []

    def test_missing_due_time_sorts_last(self, scheduler):
        tasks = [
            Task("A", 10, 1, "", "Buddy"),
            Task("B", 10, 1, "07:00", "Buddy"),
        ]
        result = scheduler.sort_by_time(tasks)
        assert result[0].description == "B"
        assert result[1].description == "A"


class TestSchedulerFilterTasks:
    def _sample(self):
        return [
            Task("Walk",  30, 3, "07:00", "Buddy",    completed=False),
            Task("Feed",  10, 4, "08:00", "Buddy",    completed=True),
            Task("Litter",10, 3, "12:00", "Whiskers", completed=False),
        ]

    def test_filter_completed_true(self, scheduler):
        result = scheduler.filter_tasks(self._sample(), completed=True)
        assert all(t.completed for t in result)
        assert len(result) == 1

    def test_filter_completed_false(self, scheduler):
        result = scheduler.filter_tasks(self._sample(), completed=False)
        assert all(not t.completed for t in result)
        assert len(result) == 2

    def test_filter_by_pet_name(self, scheduler):
        result = scheduler.filter_tasks(self._sample(), pet_name="Buddy")
        assert all(t.pet_name == "Buddy" for t in result)
        assert len(result) == 2

    def test_filter_pet_name_case_insensitive(self, scheduler):
        result = scheduler.filter_tasks(self._sample(), pet_name="buddy")
        assert len(result) == 2

    def test_filter_combined(self, scheduler):
        result = scheduler.filter_tasks(self._sample(), completed=True, pet_name="Buddy")
        assert len(result) == 1
        assert result[0].description == "Feed"

    def test_filter_no_criteria_returns_all(self, scheduler):
        sample = self._sample()
        assert scheduler.filter_tasks(sample) == sample


class TestSchedulerSortTasks:
    def test_priority_descending(self, scheduler):
        tasks = [
            Task("Low",  10, 1, "08:00", "Buddy"),
            Task("High", 10, 5, "08:00", "Buddy"),
            Task("Mid",  10, 3, "08:00", "Buddy"),
        ]
        result = scheduler.sort_tasks(tasks)
        assert result[0].description == "High"
        assert result[-1].description == "Low"

    def test_time_ascending_within_same_priority(self, scheduler):
        tasks = [
            Task("Late",  10, 3, "18:00", "Buddy"),
            Task("Early", 10, 3, "07:00", "Buddy"),
        ]
        result = scheduler.sort_tasks(tasks)
        assert result[0].description == "Early"

    def test_duration_ascending_as_tiebreaker(self, scheduler):
        tasks = [
            Task("Long",  60, 3, "08:00", "Buddy"),
            Task("Short",  5, 3, "08:00", "Buddy"),
        ]
        result = scheduler.sort_tasks(tasks)
        assert result[0].description == "Short"

    def test_bad_time_sorts_last(self, scheduler):
        # Same priority so the time key decides ordering
        tasks = [
            Task("Bad",  10, 3, "BADTIME", "Buddy"),
            Task("Good", 10, 3, "08:00",   "Buddy"),
        ]
        result = scheduler.sort_tasks(tasks)
        assert result[-1].description == "Bad"


class TestSchedulerGetByFrequency:
    def test_returns_only_matching(self, scheduler):
        tasks = [
            Task("A", 10, 1, "08:00", "Buddy", frequency="daily"),
            Task("B", 10, 1, "08:00", "Buddy", frequency="weekly"),
            Task("C", 10, 1, "08:00", "Buddy", frequency="once"),
        ]
        assert len(scheduler.get_tasks_by_frequency(tasks, "daily")) == 1
        assert len(scheduler.get_tasks_by_frequency(tasks, "weekly")) == 1
        assert len(scheduler.get_tasks_by_frequency(tasks, "once")) == 1

    def test_no_match_returns_empty(self, scheduler):
        tasks = [Task("A", 10, 1, "08:00", "Buddy", frequency="daily")]
        assert scheduler.get_tasks_by_frequency(tasks, "once") == []


class TestSchedulerHighPriority:
    def test_returns_only_high(self, scheduler):
        tasks = [
            Task("Low",  10, 2, "08:00", "Buddy"),
            Task("High", 10, 5, "08:00", "Buddy"),
            Task("Med",  10, 4, "08:00", "Buddy"),
        ]
        result = scheduler.get_high_priority_tasks(tasks, min_priority=4)
        assert all(t.priority >= 4 for t in result)
        assert len(result) == 2

    def test_sorted_descending(self, scheduler):
        tasks = [
            Task("P4", 10, 4, "08:00", "Buddy"),
            Task("P5", 10, 5, "08:00", "Buddy"),
        ]
        result = scheduler.get_high_priority_tasks(tasks)
        assert result[0].priority >= result[1].priority

    def test_empty_when_none_qualify(self, scheduler):
        tasks = [Task("Low", 10, 1, "08:00", "Buddy")]
        assert scheduler.get_high_priority_tasks(tasks, min_priority=4) == []


# ══════════════════════════════════════════════════════════════════════════════
# Scheduler – generate_daily_plan
# ══════════════════════════════════════════════════════════════════════════════

class TestGenerateDailyPlan:
    def _make_owner(self, budget):
        return Owner(name="Test", daily_time_budget=budget)

    def test_all_tasks_fit(self, scheduler, today):
        o = self._make_owner(120)
        p = Pet("Buddy", "dog")
        o.add_pet(p)
        p.add_task(Task("Walk", 30, 3, "07:00", "Buddy"))
        p.add_task(Task("Feed", 10, 4, "08:00", "Buddy"))
        plan = scheduler.generate_daily_plan(o, today)
        assert len(plan["scheduled"]) == 2
        assert len(plan["skipped"]) == 0
        assert plan["time_used"] == 40

    def test_task_skipped_when_over_budget(self, scheduler, today):
        o = self._make_owner(30)
        p = Pet("Buddy", "dog")
        o.add_pet(p)
        p.add_task(Task("Walk", 30, 5, "07:00", "Buddy"))
        p.add_task(Task("Feed", 10, 4, "08:00", "Buddy"))
        plan = scheduler.generate_daily_plan(o, today)
        assert len(plan["scheduled"]) == 1
        assert len(plan["skipped"]) == 1

    def test_completed_tasks_go_to_skipped(self, scheduler, today):
        o = self._make_owner(120)
        p = Pet("Buddy", "dog")
        o.add_pet(p)
        p.add_task(Task("Walk", 30, 3, "07:00", "Buddy", completed=True))
        plan = scheduler.generate_daily_plan(o, today)
        assert len(plan["scheduled"]) == 0
        assert len(plan["skipped"]) == 1

    def test_warning_generated_for_skipped_high_priority(self, scheduler, today):
        o = self._make_owner(1)  # tiny budget
        p = Pet("Buddy", "dog")
        o.add_pet(p)
        p.add_task(Task("Critical", 60, 5, "07:00", "Buddy"))
        plan = scheduler.generate_daily_plan(o, today)
        assert len(plan["warnings"]) == 1
        assert "Critical" in plan["warnings"][0]

    def test_no_warning_for_skipped_low_priority(self, scheduler, today):
        o = self._make_owner(1)
        p = Pet("Buddy", "dog")
        o.add_pet(p)
        p.add_task(Task("Low", 60, 1, "07:00", "Buddy"))
        plan = scheduler.generate_daily_plan(o, today)
        assert plan["warnings"] == []

    def test_plan_keys_present(self, scheduler, today):
        o = self._make_owner(60)
        p = Pet("Buddy", "dog")
        o.add_pet(p)
        plan = scheduler.generate_daily_plan(o, today)
        assert set(plan) == {"scheduled", "skipped", "time_used", "time_budget", "date", "warnings"}

    def test_zero_budget_skips_all(self, scheduler, today):
        o = self._make_owner(0)
        p = Pet("Buddy", "dog")
        o.add_pet(p)
        p.add_task(Task("Walk", 30, 3, "07:00", "Buddy"))
        plan = scheduler.generate_daily_plan(o, today)
        assert len(plan["scheduled"]) == 0

    def test_task_fits_exactly_on_remaining_budget(self, scheduler, today):
        """A task whose duration equals the remaining budget must be scheduled (<=, not <)."""
        o = self._make_owner(30)
        p = Pet("Buddy", "dog")
        o.add_pet(p)
        p.add_task(Task("Walk", 30, 3, "07:00", "Buddy"))
        plan = scheduler.generate_daily_plan(o, today)
        assert len(plan["scheduled"]) == 1
        assert plan["time_used"] == 30
        assert len(plan["skipped"]) == 0

    def test_once_task_no_due_date_appears_in_plan_every_day(self, scheduler, today):
        """once task with due_date=None is treated as always-due and appears in the plan."""
        o = self._make_owner(120)
        p = Pet("Buddy", "dog")
        o.add_pet(p)
        p.add_task(Task("Vet", 60, 3, "14:00", "Buddy", frequency="once", due_date=None))
        plan_today = scheduler.generate_daily_plan(o, today)
        plan_tomorrow = scheduler.generate_daily_plan(o, today + timedelta(days=1))
        assert len(plan_today["scheduled"]) == 1
        assert len(plan_tomorrow["scheduled"]) == 1


# ══════════════════════════════════════════════════════════════════════════════
# Scheduler – conflict detection
# ══════════════════════════════════════════════════════════════════════════════

class TestCheckSameTimeConflicts:
    def test_no_conflict(self, scheduler):
        tasks = [
            Task("A", 10, 1, "07:00", "Buddy"),
            Task("B", 10, 1, "08:00", "Buddy"),
        ]
        assert scheduler.check_same_time_conflicts(tasks) == []

    def test_two_tasks_same_time_produce_warning(self, scheduler):
        tasks = [
            Task("A", 10, 1, "08:00", "Buddy"),
            Task("B", 10, 1, "08:00", "Whiskers"),
        ]
        warnings = scheduler.check_same_time_conflicts(tasks)
        assert len(warnings) == 1
        assert "08:00" in warnings[0]

    def test_three_tasks_same_time_one_warning(self, scheduler):
        tasks = [Task(f"T{i}", 10, 1, "09:00", "Buddy") for i in range(3)]
        warnings = scheduler.check_same_time_conflicts(tasks)
        assert len(warnings) == 1

    def test_tasks_with_empty_due_time_are_ignored(self, scheduler):
        tasks = [
            Task("A", 10, 1, "", "Buddy"),
            Task("B", 10, 1, "", "Buddy"),
        ]
        assert scheduler.check_same_time_conflicts(tasks) == []

    def test_multiple_conflict_groups(self, scheduler):
        tasks = [
            Task("A", 10, 1, "08:00", "Buddy"),
            Task("B", 10, 1, "08:00", "Buddy"),
            Task("C", 10, 1, "10:00", "Buddy"),
            Task("D", 10, 1, "10:00", "Buddy"),
        ]
        warnings = scheduler.check_same_time_conflicts(tasks)
        assert len(warnings) == 2


class TestDetectConflicts:
    def test_no_overlap(self, scheduler):
        tasks = [
            Task("A", 30, 3, "07:00", "Buddy"),   # 07:00–07:30
            Task("B", 30, 2, "08:00", "Whiskers"), # 08:00–08:30
        ]
        assert scheduler.detect_conflicts(tasks) == []

    def test_adjacent_not_a_conflict(self, scheduler):
        # A ends exactly when B starts — should NOT overlap
        tasks = [
            Task("A", 60, 3, "07:00", "Buddy"),   # 07:00–08:00
            Task("B", 30, 2, "08:00", "Whiskers"), # 08:00–08:30
        ]
        assert scheduler.detect_conflicts(tasks) == []

    def test_overlap_detected(self, scheduler):
        tasks = [
            Task("A", 60, 3, "07:00", "Buddy"),   # 07:00–08:00
            Task("B", 30, 2, "07:30", "Whiskers"), # 07:30–08:00  ← overlaps
        ]
        conflicts = scheduler.detect_conflicts(tasks)
        assert len(conflicts) == 1

    def test_lower_priority_flagged_for_reschedule(self, scheduler):
        tasks = [
            Task("High", 60, 5, "07:00", "Buddy"),
            Task("Low",  30, 2, "07:30", "Buddy"),
        ]
        _, _, reschedule = scheduler.detect_conflicts(tasks)[0]
        assert reschedule.description == "Low"

    def test_higher_priority_not_flagged(self, scheduler):
        tasks = [
            Task("High", 60, 5, "07:00", "Buddy"),
            Task("Low",  30, 2, "07:30", "Buddy"),
        ]
        _, _, reschedule = scheduler.detect_conflicts(tasks)[0]
        assert reschedule.priority == 2

    def test_bad_due_time_skipped_silently(self, scheduler):
        tasks = [
            Task("Bad",  30, 3, "NOTAIME", "Buddy"),
            Task("Good", 30, 2, "07:00",   "Buddy"),
        ]
        # Should not raise; bad task is silently excluded
        assert scheduler.detect_conflicts(tasks) == []

    def test_equal_priority_reschedules_first_task(self, scheduler):
        # When both tasks share the same priority, t1 (first in list) is the reschedule candidate
        tasks = [
            Task("First",  60, 3, "07:00", "Buddy"),   # 07:00–08:00
            Task("Second", 30, 3, "07:30", "Buddy"),   # 07:30–08:00  ← overlaps
        ]
        _, _, reschedule = scheduler.detect_conflicts(tasks)[0]
        assert reschedule.description == "First"

    def test_multiple_overlaps(self, scheduler):
        # Three tasks all overlapping each other
        tasks = [
            Task("A", 120, 3, "07:00", "Buddy"),
            Task("B",  60, 2, "07:30", "Buddy"),
            Task("C",  30, 1, "08:00", "Buddy"),
        ]
        conflicts = scheduler.detect_conflicts(tasks)
        assert len(conflicts) >= 2

    def test_overnight_task_misses_conflict_with_early_morning(self, scheduler):
        """Overnight-spanning tasks produce a missed conflict (false negative).

        LateNight: 23:00 + 120 min → strptime end = 1900-01-02 01:00
        EarlyBird: 00:30 on the same base date = 1900-01-01 00:30

        The overlap check `start1(23:00) < end2(00:30+30=01:00 same day)` is False,
        so no conflict is reported — even though in real time these windows overlap.
        This documents the known limitation of the strptime-based approach."""
        tasks = [
            Task("LateNight", 120, 3, "23:00", "Buddy"),  # 23:00–01:00 next day
            Task("EarlyBird",  30, 2, "00:30", "Buddy"),  # 00:30–01:00 same base date
        ]
        conflicts = scheduler.detect_conflicts(tasks)
        assert len(conflicts) == 0  # overlap is missed — known limitation


# ══════════════════════════════════════════════════════════════════════════════
# Scheduler – task completion and recurrence
# ══════════════════════════════════════════════════════════════════════════════

class TestMarkTaskComplete:
    def test_daily_creates_next_occurrence_tomorrow(self, scheduler, buddy, today):
        task = Task("Walk", 30, 3, "07:00", "Buddy", frequency="daily")
        buddy.add_task(task)
        next_task = scheduler.mark_task_complete(task, buddy, today)
        assert next_task is not None
        assert next_task.due_date == today + timedelta(days=1)
        assert next_task.completed is False

    def test_weekly_creates_next_occurrence_in_seven_days(self, scheduler, buddy, today):
        task = Task("Groom", 20, 2, "10:00", "Buddy", frequency="weekly")
        buddy.add_task(task)
        next_task = scheduler.mark_task_complete(task, buddy, today)
        assert next_task is not None
        assert next_task.due_date == today + timedelta(weeks=1)

    def test_once_returns_none(self, scheduler, buddy, today):
        task = Task("Vet", 60, 5, "14:00", "Buddy", frequency="once", due_date=today)
        buddy.add_task(task)
        result = scheduler.mark_task_complete(task, buddy, today)
        assert result is None

    def test_once_task_still_marked_complete(self, scheduler, buddy, today):
        task = Task("Vet", 60, 5, "14:00", "Buddy", frequency="once", due_date=today)
        buddy.add_task(task)
        scheduler.mark_task_complete(task, buddy, today)
        assert task.completed is True

    def test_next_occurrence_added_to_pet(self, scheduler, buddy, today):
        task = Task("Walk", 30, 3, "07:00", "Buddy", frequency="daily")
        buddy.add_task(task)
        initial_count = len(buddy.tasks)
        scheduler.mark_task_complete(task, buddy, today)
        assert len(buddy.tasks) == initial_count + 1

    def test_next_occurrence_inherits_fields(self, scheduler, buddy, today):
        task = Task("Walk", 30, 3, "07:00", "Buddy", frequency="daily")
        buddy.add_task(task)
        next_task = scheduler.mark_task_complete(task, buddy, today)
        assert next_task.description == task.description
        assert next_task.duration_minutes == task.duration_minutes
        assert next_task.priority == task.priority
        assert next_task.due_time == task.due_time

    def test_defaults_to_date_today_when_no_reference(self, scheduler, buddy):
        task = Task("Walk", 30, 3, "07:00", "Buddy", frequency="daily")
        buddy.add_task(task)
        next_task = scheduler.mark_task_complete(task, buddy)
        assert next_task.due_date == date.today() + timedelta(days=1)

    def test_mark_task_complete_twice_adds_two_occurrences(self, scheduler, buddy, today):
        """Calling mark_task_complete twice on the same recurring task creates two
        next-occurrence entries — documents the duplication behavior."""
        task = Task("Walk", 30, 3, "07:00", "Buddy", frequency="daily")
        buddy.add_task(task)
        initial_count = len(buddy.tasks)
        scheduler.mark_task_complete(task, buddy, today)
        scheduler.mark_task_complete(task, buddy, today)
        assert len(buddy.tasks) == initial_count + 2


class TestMarkAllComplete:
    def test_marks_all_tasks(self, scheduler):
        tasks = [Task(f"T{i}", 10, 1, "08:00", "Buddy") for i in range(3)]
        scheduler.mark_all_complete(tasks)
        assert all(t.completed for t in tasks)

    def test_empty_list_is_noop(self, scheduler):
        scheduler.mark_all_complete([])  # should not raise


class TestResetCompleted:
    def test_resets_daily_and_weekly(self, scheduler):
        tasks = [
            Task("A", 10, 1, "08:00", "Buddy", frequency="daily",  completed=True),
            Task("B", 10, 1, "08:00", "Buddy", frequency="weekly", completed=True),
        ]
        scheduler.reset_completed(tasks)
        assert all(not t.completed for t in tasks)

    def test_once_tasks_stay_completed(self, scheduler):
        task = Task("Vet", 60, 5, "14:00", "Buddy", frequency="once", completed=True)
        scheduler.reset_completed([task])
        assert task.completed is True

    def test_mixed_frequencies(self, scheduler):
        tasks = [
            Task("Daily",  10, 1, "08:00", "Buddy", frequency="daily",  completed=True),
            Task("Once",   60, 5, "14:00", "Buddy", frequency="once",   completed=True),
            Task("Weekly", 20, 2, "10:00", "Buddy", frequency="weekly", completed=True),
        ]
        scheduler.reset_completed(tasks)
        status = {t.frequency: t.completed for t in tasks}
        assert status["daily"]  is False
        assert status["weekly"] is False
        assert status["once"]   is True


# ══════════════════════════════════════════════════════════════════════════════
# Scheduler – explain_plan
# ══════════════════════════════════════════════════════════════════════════════

class TestExplainPlan:
    def _build_plan(self, scheduler, today):
        o = Owner(name="Alex", daily_time_budget=60)
        p = Pet("Buddy", "dog")
        o.add_pet(p)
        p.add_task(Task("Walk", 30, 3, "07:00", "Buddy"))
        p.add_task(Task("Huge", 90, 5, "08:00", "Buddy"))  # will be skipped
        return scheduler.generate_daily_plan(o, today)

    def test_contains_date(self, scheduler, today):
        plan = self._build_plan(scheduler, today)
        output = scheduler.explain_plan(plan)
        assert str(today) in output

    def test_contains_scheduled_section(self, scheduler, today):
        plan = self._build_plan(scheduler, today)
        output = scheduler.explain_plan(plan)
        assert "Scheduled tasks" in output

    def test_contains_skipped_section(self, scheduler, today):
        plan = self._build_plan(scheduler, today)
        output = scheduler.explain_plan(plan)
        assert "Skipped tasks" in output

    def test_contains_warnings_when_high_priority_skipped(self, scheduler, today):
        plan = self._build_plan(scheduler, today)
        output = scheduler.explain_plan(plan)
        assert "Warnings" in output or "⚠" in output

    def test_no_scheduled_tasks_message(self, scheduler, today):
        o = Owner(name="Sam", daily_time_budget=0)
        p = Pet("Buddy", "dog")
        o.add_pet(p)
        p.add_task(Task("Walk", 30, 3, "07:00", "Buddy"))
        plan = scheduler.generate_daily_plan(o, today)
        output = scheduler.explain_plan(plan)
        assert "No tasks scheduled" in output

    def test_no_skipped_tasks_message(self, scheduler, today):
        o = Owner(name="Sam", daily_time_budget=999)
        p = Pet("Buddy", "dog")
        o.add_pet(p)
        p.add_task(Task("Walk", 30, 3, "07:00", "Buddy"))
        plan = scheduler.generate_daily_plan(o, today)
        output = scheduler.explain_plan(plan)
        assert "No tasks were skipped" in output
