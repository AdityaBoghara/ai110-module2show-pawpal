# PawPal+ Project Reflection

## 1. System Design

Register and manage pets
Create, view, and update pet profiles (name, species, age). This establishes the primary entity container for all subsequent task management.

Create and manage care tasks
Add, edit, and remove tasks tied to a specific pet with attributes such as duration, priority, due time, and recurrence. This forms the input space for the scheduling system.

Generate and review the daily care plan
Compute a prioritized schedule based on constraints (time budget, priority, deadlines), display selected vs skipped tasks, and provide an explanation of scheduling decisions.

1. Task
    Core unit of work.

    Attributes

    title
    duration_minutes
    priority
    due_time
    completed
    pet_name

    Methods

    mark_complete()
    is_due_today(date)
    to_dict()

2. Pet
    Container for tasks.

    Attributes

    name
    tasks

    Methods

    add_task(task)
    get_tasks()
    get_tasks_for_today(date)

3. Owner

    Container for pets.

    Attributes

    name
    daily_time_budget
    pets

    Methods

    add_pet(pet)
    get_all_tasks()
    get_due_tasks(date)
    
4. Scheduler

    Core logic.

    Attributes

    none required (stateless)

    Methods

    sort_tasks(tasks)
    generate_daily_plan(owner, date)
    detect_conflicts(tasks)
    explain_plan(plan)


Mermaid.js:

classDiagram
    class Owner {
        -name: str
        -daily_time_budget: int
        -pets: list[Pet]
        +add_pet(pet: Pet) void
        +get_all_tasks() list[Task]
        +get_due_tasks(date) list[Task]
    }
    
    class Pet {
        -name: str
        -tasks: list[Task]
        +add_task(task: Task) void
        +get_tasks() list[Task]
        +get_tasks_for_today(date) list[Task]
    }
    
    class Task {
        -title: str
        -duration_minutes: int
        -priority: int
        -due_time: str
        -completed: bool
        -pet_name: str
        +mark_complete() void
        +is_due_today(date) bool
        +to_dict() dict
    }
    
    class Scheduler {
        +sort_tasks(tasks: list) list
        +generate_daily_plan(owner: Owner, date) dict
        +detect_conflicts(tasks: list) list
        +explain_plan(plan: dict) str
    }
    
    Owner "1" --> "*" Pet : owns
    Pet "1" --> "*" Task : contains
    Scheduler --> Owner : operates on
    Scheduler --> Task : organizes


**a. Initial design**

- Briefly describe your initial UML design.
- What classes did you include, and what responsibilities did you assign to each?

**b. Design changes**

- Did your design change during implementation?
- If yes, describe at least one change and why you made it.

---

## 2. Scheduling Logic and Tradeoffs

**a. Constraints and priorities**

- What constraints does your scheduler consider (for example: time, priority, preferences)?
- How did you decide which constraints mattered most?

**b. Tradeoffs**

- Describe one tradeoff your scheduler makes.
- Why is that tradeoff reasonable for this scenario?

---

## 3. AI Collaboration

**a. How you used AI**

- How did you use AI tools during this project (for example: design brainstorming, debugging, refactoring)?
- What kinds of prompts or questions were most helpful?

**b. Judgment and verification**

- Describe one moment where you did not accept an AI suggestion as-is.
- How did you evaluate or verify what the AI suggested?

---

## 4. Testing and Verification

**a. What you tested**

- What behaviors did you test?
- Why were these tests important?

**b. Confidence**

- How confident are you that your scheduler works correctly?
- What edge cases would you test next if you had more time?

---

## 5. Reflection

**a. What went well**

- What part of this project are you most satisfied with?

**b. What you would improve**

- If you had another iteration, what would you improve or redesign?

**c. Key takeaway**

- What is one important thing you learned about designing systems or working with AI on this project?
