# Database Schema Documentation

## 1. Entity-Relationship Diagram

```mermaid
erDiagram
    USERS ||--o| STUDENT_PREFERENCES : has
    USERS ||--o{ SUBJECTS : owns
    USERS ||--o{ EXAMINATIONS : schedules
    USERS ||--o{ STUDY_SESSIONS : attends
    USERS ||--o{ PROGRESS_RECORDS : logs
    USERS ||--o{ QUIZ_ATTEMPTS : takes
    USERS ||--o{ REVISION_SCHEDULES : manages
    USERS ||--o{ CHAT_CONVERSATIONS : owns
    USERS ||--o{ NOTIFICATIONS : receives

    SUBJECTS ||--o{ TOPICS : contains
    SUBJECTS ||--o{ EXAMINATIONS : tests
    SUBJECTS ||--o{ STUDY_SESSIONS : schedules

    TOPICS ||--o{ STUDY_SESSIONS : targets
    TOPICS ||--o{ REVISION_SCHEDULES : tracks
    TOPICS ||--o{ QUIZ_ATTEMPTS : tests

    QUIZ_ATTEMPTS ||--o{ QUIZ_QUESTIONS : contains
    CHAT_CONVERSATIONS ||--o{ CHAT_MESSAGES : contains
    STUDY_SESSIONS ||--o{ PROGRESS_RECORDS : generates

    USERS {
        int id PK
        string email UK
        string full_name
        string hashed_password
        datetime created_at
        datetime updated_at
    }

    STUDENT_PREFERENCES {
        int id PK
        int user_id FK
        float daily_study_hours
        string preferred_start_time
        string preferred_end_time
        string preferred_study_days
        int break_duration
        text academic_goals
        string preferred_learning_style
    }

    SUBJECTS {
        int id PK
        int user_id FK
        string name
        text description
        string color
        string difficulty
        string priority
        datetime created_at
    }

    TOPICS {
        int id PK
        int subject_id FK
        string name
        text description
        string difficulty
        int estimated_time_minutes
        int actual_time_spent_minutes
        int completion_percentage
        string status
        datetime last_studied_date
        bool revision_required
    }

    EXAMINATIONS {
        int id PK
        int user_id FK
        int subject_id FK
        string title
        datetime exam_date
        string priority
        text notes
    }

    STUDY_SESSIONS {
        int id PK
        int user_id FK
        int subject_id FK
        int topic_id FK
        string session_date
        string start_time
        string end_time
        int duration_minutes
        string priority
        string session_type
        string status
        text ai_recommendation
        text notes
        string plan_type
    }

    PROGRESS_RECORDS {
        int id PK
        int user_id FK
        int session_id FK
        string study_date
        int duration_minutes
        string status
        text notes
    }

    QUIZ_ATTEMPTS {
        int id PK
        int user_id FK
        int subject_id FK
        int topic_id FK
        int total_questions
        int correct_answers
        float score_percentage
        string difficulty
        datetime created_at
    }

    QUIZ_QUESTIONS {
        int id PK
        int quiz_attempt_id FK
        text question_text
        string option_a
        string option_b
        string option_c
        string option_d
        string correct_option
        string selected_option
        text explanation
        bool is_correct
    }

    REVISION_SCHEDULES {
        int id PK
        int user_id FK
        int subject_id FK
        int topic_id FK
        int revision_step
        string scheduled_date
        string status
        datetime completed_at
    }

    CHAT_CONVERSATIONS {
        int id PK
        int user_id FK
        string title
        datetime created_at
    }

    CHAT_MESSAGES {
        int id PK
        int conversation_id FK
        string sender
        text content
        datetime created_at
    }

    NOTIFICATIONS {
        int id PK
        int user_id FK
        string title
        text message
        string type
        bool is_read
        datetime scheduled_for
        datetime created_at
    }
```

---

## 2. PostgreSQL Migration Guide

The application models use SQLAlchemy 2.0 with standard column types and foreign key constraints compatible with both SQLite and PostgreSQL.

To migrate to PostgreSQL:
1. Install `psycopg2-binary` or `asyncpg`:
   ```bash
   pip install psycopg2-binary
   ```
2. Update the `DATABASE_URL` in `.env`:
   ```env
   DATABASE_URL=postgresql://username:password@localhost:5432/study_planner_db
   ```
3. Restart the FastAPI service. The `Base.metadata.create_all(bind=engine)` hook will automatically create all tables and indexes.

