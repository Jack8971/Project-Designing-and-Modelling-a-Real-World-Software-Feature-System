# Learning Platform Access System

A role-based access control (RBAC) and feature restriction simulation built in Python. This project demonstrates core computational thinking principles—decomposition, data structure modeling, truth table boolean logic, algorithm pseudocode, and system modeling—for a modern educational access control system.

---

## 📅 Project Details & Deadlines
* **Course Assignment:** Designing & Modelling a Real-World Software Feature System
* **Project Theme:** Learning Platform Access System
* **Due Date:** October 27, 2026 @ 11:59 PM
* **Target Language:** Python 3.x
* **Primary GitHub ID:** 34843252

---

## 🎯 Project Overview & Deliverables

This system models user authentication, role-based feature permissions (Students, Instructors, Admins), subscription status validation, and error-handling logic.

### 📋 Deliverable Structure

| Part | Description | Primary Artifacts |
|---|---|---|
| **Part A** | Problem Definition & Requirements | Problem statement, 5–7 functional/non-functional requirements, input/output constraints |
| **Part B** | Data Structures & Logical Reasoning | User & feature data models (dicts/lists), 3-variable truth table, boolean expressions & natural language translation |
| **Part C** | Pseudocode & Algorithm Design | Structured pseudocode covering decomposition, sequence, selection, and repetition |
| **Part D** | System Modeling | UML Activity Diagram / Flowchart (showing conditional branches, actions, and loops) |
| **Part E** | System Simulation | Executable Python script (`main.py`) with role checks, error handling, and terminal output |
| **Part F** | Individual Reflections | 150–200 word individual reflection per team member |

---

## 📂 Repository Structure

```text
├── docs/
│   ├── Part_A_Requirements.md       # Problem statement, requirements & constraints
│   ├── Part_B_Data_and_Logic.md     # Data models, truth table, and boolean rules
│   ├── Part_C_Pseudocode.md         # System algorithm and pseudocode breakdown
│   ├── Part_D_Activity_Diagram.png  # UML Activity diagram / flowchart export
│   └── Part_F_Reflections.md        # Group reflections (150-200 words each)
├── src/
│   ├── data.py                      # User dictionaries, role lists, and feature permissions
│   ├── auth.py                      # Login validation & retry handling logic
│   ├── permissions.py               # Boolean logic evaluator for feature access
│   └── main.py                      # CLI entry point and interactive system simulation
├── tests/
│   └── test_simulation.py           # Test cases for logins, role restrictions, & edge cases
├── Project_Report.pdf               # Complete compiled group submission PDF
└── README.md                        # Repository overview and guide
```

---

## 🛠 System Logic & Feature Matrix

The access control engine evaluates three main conditions:
1. `IsLoggedIn` (Boolean)
2. `UserRole` (`Student`, `Instructor`, `Admin`)
3. `HasActiveSubscription` (Boolean)

### Feature Access Matrix

| Role | Quizzes / Content | Grades / Submissions | Course Analytics | System Admin Config |
|---|:---:|:---:|:---:|:---:|
| **Student** | ✅ | ✅ (Read Only) | ❌ | ❌ |
| **Instructor** | ✅ | ✅ (Full Access) | ✅ | ❌ |
| **Admin** | ✅ | ✅ | ✅ | ✅ |

---

## 💻 How to Run the Simulation

### Prerequisites
* Python 3.8 or higher installed on your machine.

### Execution
1. Clone the repository:
   git clone <REPOSITORY_URL>
   cd <REPOSITORY_FOLDER>

2. Run the main simulation script:
   python src/main.py
   python src/main.py --interactive

### Sample Simulation Output
=== Learning Platform Access System ===
Logging in user: student_alex ... SUCCESS
Evaluating Role Permissions [Role: Student | Active Sub: True] ...
 - Accessing Quizzes: GRANTED
 - Accessing Grades: GRANTED (Student View)
 - Accessing System Analytics: DENIED (Instructor/Admin required)

---

## 👥 Team Workflow & Git Guidelines

To maintain a clean repository and record contributions for peer review:

1. **Branching:** Do not work directly on `main`. Create feature branches for your tasks:
   * `docs/part-a-b`
   * `feature/auth-simulation`
   * `docs/diagrams`
2. **Commit Messages:** Use clear titles (e.g., `feat: add truth table logic to docs`, `fix: update login retry loop in auth.py`).
