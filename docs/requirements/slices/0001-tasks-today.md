# Slice 1: One-time tasks, Today, and Week shell

**Status:** Spec ready for implementation (you write core assembly logic).
**Depends on:** ADR 0006 (local-date `due_date`), [preferences.md](../preferences.md), [configurable-policies.md](../configurable-policies.md) (hard-coded defaults).
**Excludes:** backlog, routines, appointments, settings UI, auth.

## Goal

Ship a vertical slice: **Task CRUD → persistence → API → Week (default landing) + Today views**.

Prove end-to-end flow with fabricated data only.

## Acceptance criteria mapped

| ID | Covered by |
|----|------------|
| AC-CAP-2 | Create task with `due_date` = today → appears in Today |
| AC-CAP-3 | Empty title → 422, no row created |
| AC-TOD-1 | Today lists pending tasks due on reference date + overdue (policy) |
| AC-TOD-2 | Complete task → completion record + status `completed` |
| AC-TOD-3 | Frontend error state (existing pattern) |
| AC-PRF-1 | Frontend default route = Week |
| AC-PRF-2 | Create/edit task via modal (Slice 1: task-only modal) |
| AC-NF-* | Existing infra + no sensitive logging |

---

## 1. Domain model

### 1.1 Task status

```python
class TaskStatus(StrEnum):
    PENDING = "pending"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
```

Terminal states for MVP: `completed`, `cancelled` (no un-complete).

### 1.2 Completion action

```python
class CompletionAction(StrEnum):
    COMPLETED = "completed"
    CANCELLED = "cancelled"
```

### 1.3 Local date (you implement)

```python
# planforge/domain/local_date.py

@dataclass(frozen=True)
class LocalDate:
    """Calendar date without timezone. ISO format YYYY-MM-DD."""

    year: int
    month: int
    day: int

    @classmethod
    def from_iso(cls, value: str) -> LocalDate: ...

    def to_iso(self) -> str: ...

    def __lt__(self, other: LocalDate) -> bool: ...
```

**Constraints:**

- Valid calendar dates only; reject `2026-02-30`.
- No time component.
- Store in SQLite as `DATE` or `TEXT` ISO string — pick one in migration; document in Alembic revision.

### 1.4 Clock / “today” (you implement)

```python
# planforge/domain/clock.py

class Clock(Protocol):
  def today(self) -> LocalDate: ...
  def timezone_name(self) -> str: ...
```

**Slice 1:** `SystemClock` using configured IANA timezone from settings (add
`PLANFORGE_TIMEZONE` default `UTC` in `.env.example` until preferences UI exists).

---

## 2. Database schema

### 2.1 Table `tasks`

| Column | Type | Nullable | Notes |
|--------|------|----------|-------|
| `id` | `String(36)` | PK | UUID string |
| `owner_id` | `String(36)` | NO | Single-user MVP: constant `LOCAL_OWNER_ID` |
| `title` | `String(500)` | NO | Trimmed; min length 1 |
| `notes` | `Text` | YES | |
| `due_date` | `Date` or ISO text | YES | Local date; null = unscheduled |
| `status` | `String(20)` | NO | `pending` \| `completed` \| `cancelled` |
| `created_at` | `DateTime(tz)` | NO | UTC metadata |
| `updated_at` | `DateTime(tz)` | NO | UTC metadata |

**Indexes:**

- `(owner_id, status, due_date)` — list/filter
- `(owner_id, due_date)` — week range queries

**Multi-user-ready:** `owner_id` on every row; Slice 1 uses one constant.

### 2.2 Table `completion_records`

| Column | Type | Nullable | Notes |
|--------|------|----------|-------|
| `id` | `String(36)` | PK | |
| `owner_id` | `String(36)` | NO | |
| `entity_type` | `String(32)` | NO | Slice 1: always `"task"` |
| `entity_id` | `String(36)` | NO | Task id |
| `action` | `String(20)` | NO | `completed` \| `cancelled` |
| `recorded_at` | `DateTime(tz)` | NO | UTC instant |

**No FK** to `tasks` (append-only audit; task may exist after record).

### 2.3 Alembic

- Revision `0002_tasks_and_completion_records.py`
- Upgrade creates both tables; downgrade drops both.

---

## 3. Hard-coded policies (Slice 1)

Until Slice 5 settings UI, read from a module — not env vars:

```python
# planforge/core/policy_defaults.py

@dataclass(frozen=True)
class PolicySnapshot:
    today_include_rolled_tasks: bool = True
    week_include_overdue_tasks: bool = True
    week_start_day: str = "monday"  # ADR 0006

def get_policy_snapshot() -> PolicySnapshot:
    return PolicySnapshot()
```

**You implement** view assembly using this snapshot.

---

## 4. View assembly (you implement)

### 4.1 Today assembly

```python
# planforge/services/today_view.py

@dataclass(frozen=True)
class TodayTaskItem:
    task_id: str
    title: str
    notes: str | None
    due_date: LocalDate | None
    is_overdue: bool

@dataclass(frozen=True)
class TodayView:
    reference_date: LocalDate
    tasks: list[TodayTaskItem]

def assemble_today_view(
    *,
    session: Session,
    owner_id: str,
    reference_date: LocalDate,
    policies: PolicySnapshot,
) -> TodayView:
    """
    Return pending tasks for Today.

    Include:
    - Tasks with due_date == reference_date
    - If policies.today_include_rolled_tasks:
        pending tasks with due_date < reference_date (overdue reminders)

    Exclude:
    - completed, cancelled
    - Tasks with due_date IS NULL (unscheduled — Week only for Slice 1)
    - Tasks with due_date > reference_date

    Sort: overdue first (oldest due_date first), then due today; title ASC tie-break.
    """
    ...
```

### 4.2 Week assembly

```python
# planforge/services/week_view.py

@dataclass(frozen=True)
class WeekTaskItem:
    task_id: str
    title: str
    due_date: LocalDate | None
    is_overdue: bool

@dataclass(frozen=True)
class WeekDayGroup:
    date: LocalDate | None  # None = "Unscheduled" bucket
    tasks: list[WeekTaskItem]

@dataclass(frozen=True)
class WeekView:
    week_start: LocalDate
    week_end: LocalDate
    days: list[WeekDayGroup]

def week_bounds(
    *,
    reference_date: LocalDate,
    week_start_day: str,
) -> tuple[LocalDate, LocalDate]:
    """Return inclusive Monday-based (or policy) week start/end dates."""

def assemble_week_view(
    *,
    session: Session,
    owner_id: str,
    week_start: LocalDate,
    policies: PolicySnapshot,
) -> WeekView:
    """
    Return pending tasks grouped by due_date for [week_start, week_end].

    Include per day:
    - pending tasks with due_date on that day

    If policies.week_include_overdue_tasks:
    - pending tasks with due_date < week_start appear in week_start day
      OR separate "Overdue" group — DECISION for implementer: use first day
      of week column with is_overdue=True (recommended)

  Unscheduled bucket (due_date IS NULL): single group at end.

  Exclude completed, cancelled.
  """
    ...
```

---

## 5. Task service (you implement business rules)

```python
# planforge/services/task_service.py

def create_task(
    session: Session,
    *,
    owner_id: str,
    title: str,
    notes: str | None = None,
    due_date: LocalDate | None = None,
) -> Task:
    """
    - Strip title; raise ValidationError if empty after strip.
    - status = pending.
  """

def update_task(
    session: Session,
    *,
    task_id: str,
    owner_id: str,
    title: str | None = None,
    notes: str | None = None,
    due_date: LocalDate | None = ...,  # sentinel if omit vs clear
) -> Task:
    """
    - Only pending tasks editable.
    - completed/cancelled → raise TaskNotEditableError.
  """

def complete_task(session: Session, *, task_id: str, owner_id: str) -> Task:
    """
    - pending → completed
    - Append completion_records row (action=completed, recorded_at=now UTC)
    - Idempotency: completing completed → TaskStateError (409)
  """

def cancel_task(session: Session, *, task_id: str, owner_id: str) -> Task:
    """
    - pending → cancelled
    - Append completion_records row (action=cancelled)
    - Idempotency: cancelling cancelled → TaskStateError (409)
  """
```

---

## 6. REST API

Base prefix: `/api`. JSON only. No auth Slice 1 (`owner_id` = constant).

### 6.1 Pydantic schemas (agent may scaffold)

```python
class TaskCreateRequest(BaseModel):
    title: str = Field(min_length=1, max_length=500)
    notes: str | None = None
    due_date: date | None = None  # JSON ISO date

class TaskUpdateRequest(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=500)
    notes: str | None = None
    due_date: date | None = None

class TaskResponse(BaseModel):
    id: str
    title: str
    notes: str | None
    due_date: date | None
    status: TaskStatus
    created_at: datetime
    updated_at: datetime

class TodayViewResponse(BaseModel):
    reference_date: date
    tasks: list[TodayTaskItemResponse]

class WeekViewResponse(BaseModel):
    week_start: date
    week_end: date
    days: list[WeekDayGroupResponse]
```

### 6.2 Endpoints

| Method | Path | Success | Errors |
|--------|------|---------|--------|
| `GET` | `/tasks` | `200` list[`TaskResponse`] | Query: `?status=pending` optional |
| `POST` | `/tasks` | `201` `TaskResponse` | `422` validation |
| `GET` | `/tasks/{id}` | `200` | `404` |
| `PATCH` | `/tasks/{id}` | `200` | `404`, `409` not editable |
| `POST` | `/tasks/{id}/complete` | `200` | `404`, `409` wrong state |
| `POST` | `/tasks/{id}/cancel` | `200` | `404`, `409` |
| `GET` | `/views/today` | `200` `TodayViewResponse` | Query: `?date=YYYY-MM-DD` optional |
| `GET` | `/views/week` | `200` `WeekViewResponse` | Query: `?week_start=YYYY-MM-DD` optional |

**Error body (consistent):**

```json
{ "detail": "Human-readable message" }
```

Never return stack traces.

**Router registration:** `planforge/api/tasks.py`, `planforge/api/views.py` — include in `create_app()`.

---

## 7. Frontend (you implement against API)

### 7.1 Routes (path-based, no router lib required)

| Path | Page | Notes |
|------|------|-------|
| `/` or `/week` | `WeekPage` | **Default landing** (AC-PRF-1) |
| `/today` | `TodayPage` | |
| `/dev/components` | existing gallery | unchanged |

Update `App.tsx` path switch.

### 7.2 API client

```typescript
// src/lib/tasks.ts — types from OpenAPI or hand-written for Slice 1

export interface Task { ... }

export function listTasks(): Promise<Task[]>;
export function createTask(body: TaskCreateBody): Promise<Task>;
export function completeTask(id: string): Promise<Task>;
export function cancelTask(id: string): Promise<Task>;
export function fetchTodayView(date?: string): Promise<TodayView>;
export function fetchWeekView(weekStart?: string): Promise<WeekView>;
```

Run `npm run generate:api-types` after backend OpenAPI includes new routes.

### 7.3 UI components to build

| Component | Responsibility |
|-----------|----------------|
| `TaskModal` | Create task; fields title, notes, due date; fabricated placeholders |
| `TaskRow` | Title, due date badge, complete + cancel buttons |
| `WeekPage` | Fetch week view; group headers; "Add task" opens modal |
| `TodayPage` | Fetch today view; overdue section label if any |
| `AppShell` | Shared header/nav (Week, Today, Components) |

Use existing primitives (`Dialog`, `FormField`, `Input`, `Button`, `Badge`).

**Modal capture (AC-PRF-2):** `TaskModal` uses `Dialog`; no full-page navigation.

### 7.4 Frontend edge cases

- Empty week/today → `EmptyState` with fabricated copy
- API error → inline alert, no stack trace
- Disable complete/cancel while request in flight
- Keyboard: modal focus trap (Dialog), complete via button focus

---

## 8. Edge cases and validation matrix

| Case | Expected |
|------|----------|
| Title `""` or whitespace only | `422`, no DB row |
| Title 501 chars | `422` |
| Invalid ISO date `2026-13-40` | `422` |
| `GET /tasks/{missing}` | `404` |
| `PATCH` completed task | `409` |
| `POST complete` on completed task | `409` |
| Task `due_date` null | Listed under Unscheduled on Week; not on Today |
| Task due yesterday, policy roll on | On Today and Week (overdue) |
| Task due tomorrow | Week only (in correct day column) |
| Two tasks same title | Allowed |
| SQL injection in title | Parameterized ORM; stored literally |

---

## 9. Tests

### 9.1 Backend unit (you write behavior; agent may add mechanical)

**`tests/domain/test_local_date.py`**

- Valid ISO parse
- Invalid date raises
- Ordering

**`tests/services/test_task_service.py`**

- Create trims title
- Empty title raises
- Complete pending → completed + completion record
- Complete twice → error
- Cancel pending → cancelled + record
- Update completed → error

**`tests/services/test_today_view.py`**

- Due today included
- Overdue included when policy true
- Overdue excluded when policy false (mock snapshot)
- Unscheduled excluded
- Completed excluded

**`tests/services/test_week_view.py`**

- Tasks grouped by due_date
- Week bounds Monday default
- Unscheduled bucket

### 9.2 Backend API (httpx + ASGITransport)

**`tests/api/test_tasks_api.py`**

- `POST /api/tasks` 201
- `POST` empty title 422
- `GET /api/views/today` structure
- `POST .../complete` then not in today pending list

### 9.3 Frontend (Vitest)

- `TaskRow` renders and fires complete callback
- `WeekPage` shows loading then empty state (mock fetch)

---

## 10. Suggested file layout

```
backend/planforge/
  domain/
    local_date.py      # you
    clock.py             # you
  models/
    task.py              # ORM
    completion_record.py
  schemas/
    task.py              # Pydantic
    views.py
  services/
    task_service.py      # you
    today_view.py        # you
    week_view.py         # you
  api/
    tasks.py
    views.py
  core/
    policy_defaults.py
    owner.py             # LOCAL_OWNER_ID constant

frontend/src/
  pages/WeekPage.tsx
  pages/TodayPage.tsx
  components/TaskModal.tsx
  components/TaskRow.tsx
  lib/tasks.ts
```

---

## 11. Implementation order (recommended)

1. `LocalDate` + tests
2. Alembic migration + ORM models
3. `task_service` + tests
4. Task API routes + API tests
5. `assemble_today_view` / `assemble_week_view` + tests
6. View API routes
7. Frontend `lib/tasks.ts` + `WeekPage` / `TodayPage` / `TaskModal`
8. Wire default route to Week
9. Manual test with fabricated titles only

---

## 12. Out of scope (do not build in Slice 1)

- Backlog, routines, appointments
- Settings / policy UI (hard-code `PolicySnapshot`)
- Auth, `owner_id` selection
- Categories, tags, priority
- Task un-complete or delete (cancel only)
- Month view
- Browser storage / offline

---

## 13. Demo data

Optional dev-only seed script (`backend/scripts/seed_demo_tasks.py`, gitignored
runner or documented command) creating:

- "Water the plants" due today
- "Example overdue errand" due 3 days ago
- "Future demo task" due next week
- "Unscheduled idea" no due date

All titles obviously fabricated. Never run against real personal data.

---

## 14. Definition of done (Slice 1)

- [ ] All tests in §9 pass locally and in CI
- [ ] Pre-commit clean
- [ ] Week opens by default; Today and Week show correct pending tasks
- [ ] Task modal creates and completes tasks
- [ ] No secrets or personal data in repo
- [ ] OpenAPI updated; frontend types regenerated

When you start coding, say **"Implement this"** for any subsection you want
the agent to scaffold mechanically (models, routes, tests only).
