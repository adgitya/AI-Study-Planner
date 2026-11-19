# REST API Reference Documentation

All endpoints are versioned under `/api/v1` (with convenient root aliases). Interactive Swagger UI is hosted at `http://localhost:8000/docs`.

---

## Authentication

All protected endpoints require an `Authorization: Bearer <JWT_TOKEN>` header.

### 1. `POST /api/v1/auth/register`
Creates a student account and initializes default study preferences.
- **Request Body:**
  ```json
  {
    "full_name": "Alice Johnson",
    "email": "alice@example.com",
    "password": "Password123!",
    "confirm_password": "Password123!"
  }
  ```
- **Response (201 Created):**
  ```json
  {
    "access_token": "eyJhbGciOi...",
    "token_type": "bearer",
    "user": {
      "id": 1,
      "full_name": "Alice Johnson",
      "email": "alice@example.com",
      "created_at": "2026-11-05T12:00:00Z"
    }
  }
  ```

### 2. `POST /api/v1/auth/login`
- **Request Body:**
  ```json
  {
    "email": "alice@example.com",
    "password": "Password123!"
  }
  ```
- **Response (200 OK):** JWT Bearer token and user payload.

### 3. `GET /api/v1/auth/me`
Returns current authenticated user details.

---

## Student Preferences & Profile

### `GET /api/v1/profile`
Returns current student daily study limits, start/end times, and preferences.

### `PUT /api/v1/profile`
Updates preferences.
```json
{
  "full_name": "Alice Johnson",
  "daily_study_hours": 5.0,
  "preferred_start_time": "09:00",
  "preferred_end_time": "21:00",
  "preferred_study_days": "Monday,Tuesday,Wednesday,Thursday,Friday",
  "break_duration": 15,
  "academic_goals": "Score top percentile in examinations",
  "preferred_learning_style": "Visual"
}
```

---

## Subjects & Topics

- `GET /api/v1/subjects`: List all subjects with completion statistics.
- `POST /api/v1/subjects`: Create a new subject with color, difficulty, and priority.
- `GET /api/v1/subjects/{id}`: Detail view including all associated topics.
- `PUT /api/v1/subjects/{id}`: Update subject metadata.
- `DELETE /api/v1/subjects/{id}`: Delete subject and cascades.

- `GET /api/v1/topics?subject_id={id}&status_filter={status}`: Filter topics.
- `POST /api/v1/topics`: Create topic under subject.
- `PUT /api/v1/topics/{id}`: Update progress, time spent, or toggle completion.
- `DELETE /api/v1/topics/{id}`: Delete topic.

---

## Examinations

- `GET /api/v1/exams`: List upcoming examinations with auto-calculated `days_remaining` and `is_urgent` badge.
- `POST /api/v1/exams`: Add an examination deadline.
- `PUT /api/v1/exams/{id}`: Update examination.
- `DELETE /api/v1/exams/{id}`: Delete examination.

---

## Study Plans & Scheduling

### `POST /api/v1/plans/generate`
Executes deterministic scheduling and enriches with AI personalization.
- **Request Body:**
  ```json
  {
    "plan_type": "weekly",
    "target_date": "2026-11-05",
    "focus_subject_ids": null,
    "regenerate": true
  }
  ```
- **Response (200 OK):**
  ```json
  {
    "plan_type": "weekly",
    "start_date": "2026-11-05",
    "end_date": "2026-11-11",
    "total_sessions": 14,
    "total_study_minutes": 840,
    "sessions": [...],
    "ai_summary": "Your plan balances upcoming OS exam preparation...",
    "strategy_notes": [...]
  }
  ```

### `POST /api/v1/plans/adjust`
Identifies missed or uncompleted sessions, recalculates topic urgency, and redistributes pending tasks without exceeding daily study hours.

### `PUT /api/v1/sessions/{id}/status`
Marks a session as `Completed`, `Partially Completed`, `Not Completed`, or `Skipped`. Automatically logs `ProgressRecord` and increments topic progress.

---

## AI Assistant & Quiz Generator

- `POST /api/v1/ai/chat`: Context-aware academic assistant that injects student's actual database context (exams, subjects, pending topics).
- `GET /api/v1/ai/conversations`: Returns conversation history.
- `DELETE /api/v1/ai/conversations/{id}`: Clears chat history.

- `POST /api/v1/ai/generate-quiz`: Generates MCQs with 4 options, correct answer, and explanation.
- `POST /api/v1/ai/submit-quiz`: Evaluates answers, calculates score, and feeds results into the Spaced Revision engine.
- `GET /api/v1/ai/quiz-history`: Past attempts and scores.

---

## Spaced Revisions & Notifications

- `GET /api/v1/revision`: Active spaced repetitions across Step 1 (1d), Step 2 (3d), Step 3 (7d), and Step 4 (14d).
- `POST /api/v1/revision/{id}/complete`: Marks step complete and schedules next interval.

- `GET /api/v1/notifications`: List background reminders and alerts.
- `PUT /api/v1/notifications/{id}/read`: Mark as read.
- `PUT /api/v1/notifications/read-all/mark`: Mark all as read.

