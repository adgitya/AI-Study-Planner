# AI Study Planner 🎓

> An intelligent, full-stack, AI-powered study planning and academic productivity management platform.

AI Study Planner helps students systematically organize academic schedules, manage subjects and topics, prepare for examinations, track study progress, and receive personalized recommendations using a hybrid **deterministic constraint scheduler + LLM personalization engine**.

---

## 🌟 Key Features

1. **🔐 Authentication & User Isolation:**
   - Secure registration, JWT-based bearer authentication, and bcrypt password hashing.
   - Strict data isolation ensuring students only ever access their own academic records.

2. **⚙️ Student Preferences & Capacity Constraints:**
   - Configurable daily available study hours (e.g. 4.0 hrs/day) and rest break durations.
   - Preferred study windows (start/end times), active weekdays, and learning styles.

3. **📚 Hierarchical Subject & Topic Management:**
   - `Subject → Topics → Study Sessions` hierarchy.
   - Topic difficulty (Easy, Medium, Hard), estimated vs actual study time, completion percentages, and urgent revision flags.

4. **🎯 Examination Proximity Tracking:**
   - Automated calculation of days remaining until each exam.
   - Visual urgency indicators ($\le 3$ days critical, $\le 7$ days urgent) prioritizing subjects in the scheduling engine.

5. **🧠 Hybrid AI Study Plan Generator:**
   - **Deterministic Scheduler:** Generates non-overlapping study blocks, respects daily hour limits, allocates breaks, and balances workloads.
   - **LLM Personalization:** Enriches each study session with tactical cognitive advice and overarching strategy notes.
   - **Zero-Failure Fallback:** Functions seamlessly with full scheduling logic even if LLM API keys are offline or unavailable.

6. **⚡ Adaptive Study Planning ("Adjust My Study Plan"):**
   - Continuously monitors missed, skipped, or partially completed sessions.
   - Intelligently redistributes unfinished tasks across upcoming days without overloading the student.

7. **📊 Rich Progress & Productivity Analytics:**
   - Powered by Recharts: Weekly study-hours bar chart (Planned vs Actual), subject-wise progress, 14-day productivity trend, and session status distribution.
   - Real streak tracking and empty-state guidance for new accounts.

8. **🤖 Context-Aware AI Study Assistant:**
   - Chatbot with direct access to the student's actual database (enrolled subjects, pending topics, upcoming exams).
   - Never fabricates nonexistent exams or progress metrics.

9. **📝 AI Quiz Hub & Spaced Repetition:**
   - Synthesizes multiple-choice questions with answer keys and conceptual explanations.
   - **Spaced Revision System:** Automated 1-day, 3-day, 7-day, and 14-day review cycles triggered on topic completion or low quiz scores (< 70%).

10. **🔔 Background Notifications & Reminders:**
    - APScheduler daemon for automated exam alerts, daily session reminders, and overdue revision warnings.
    - Full in-app notification center + browser notification permission support.

11. **🌓 Modern SaaS Interface:**
    - Built with React, Vite, Tailwind CSS, and Lucide React.
    - Full Light Mode and Dark Mode support with responsive layouts across mobile, tablet, and desktop.

---

## 🛠️ Technology Stack

| Layer | Technologies |
|---|---|
| **Frontend** | React 19, Vite, Tailwind CSS, Lucide React, Recharts, React Router DOM, Axios |
| **Backend** | Python 3.13, FastAPI, SQLAlchemy 2.0, Pydantic v2, PyJWT, bcrypt, APScheduler |
| **Database** | SQLite (default for zero-friction setup; seamless migration to PostgreSQL) |
| **AI Layer** | OpenAI API (`gpt-4o-mini`) with structured JSON validation + robust rule-based fallback |

---

## 📁 Project Directory Structure

```text
AI-Study-Planner/
│
├── backend/
│   ├── app/
│   │   ├── core/
│   │   │   ├── config.py         # App configuration & settings
│   │   │   ├── database.py       # SQLAlchemy engine & session maker
│   │   │   ├── deps.py           # Dependency injection (get_current_user)
│   │   │   └── security.py       # Password hashing & JWT encode/decode
│   │   ├── models/
│   │   │   ├── all_models.py     # 13 relational database models
│   │   │   └── __init__.py
│   │   ├── schemas/
│   │   │   ├── all_schemas.py    # Pydantic v2 request/response schemas
│   │   │   └── __init__.py
│   │   ├── services/
│   │   │   ├── ai_service.py           # LLM client & structured prompt templates
│   │   │   ├── planner_service.py      # Deterministic scheduling algorithm
│   │   │   ├── adaptive_service.py     # Adaptive replanning engine
│   │   │   ├── quiz_service.py         # Quiz generation & scoring
│   │   │   ├── revision_service.py     # Spaced repetition cycles (1-3-7-14d)
│   │   │   └── notification_service.py # Background alert generation
│   │   ├── routers/
│   │   │   ├── auth.py           # Registration & login
│   │   │   ├── profile.py        # Student preferences
│   │   │   ├── subjects.py       # Subject CRUD
│   │   │   ├── topics.py         # Topic CRUD & progress updates
│   │   │   ├── exams.py          # Examination deadlines
│   │   │   ├── plans.py          # Daily & weekly plans, status updates
│   │   │   ├── progress.py       # Analytics data for Recharts
│   │   │   ├── ai.py             # Chatbot & quiz endpoints
│   │   │   ├── revision.py       # Spaced revisions
│   │   │   └── notifications.py  # Notification center
│   │   └── main.py               # FastAPI application factory & scheduler
│   ├── tests/
│   │   └── test_study_planner.py # 11 automated pytest test suites
│   ├── requirements.txt
│   ├── .env.example
│   └── main.py                   # Direct entrypoint for running backend
│
├── frontend/
│   ├── src/
│   │   ├── context/
│   │   │   ├── AuthContext.jsx   # Authentication state & token persistence
│   │   │   └── ThemeContext.jsx  # Dark/Light mode theme state
│   │   ├── layouts/
│   │   │   └── AppLayout.jsx     # Navigation sidebar, topbar, alert banner
│   │   ├── pages/
│   │   │   ├── Dashboard.jsx     # Overview, today's schedule, quick actions
│   │   │   ├── Planner.jsx       # Weekly & daily timetable calendar
│   │   │   ├── Subjects.jsx      # Hierarchical subject & topic manager
│   │   │   ├── Examinations.jsx  # Exam countdowns and priorities
│   │   │   ├── Progress.jsx      # Recharts analytics charts
│   │   │   ├── Assistant.jsx     # Context-aware AI chatbot
│   │   │   ├── QuizHub.jsx       # Interactive MCQ quiz generator & review
│   │   │   ├── Revisions.jsx     # Spaced repetition dashboard
│   │   │   ├── Profile.jsx       # Student preferences & hour limits
│   │   │   ├── Login.jsx         # Sign in page
│   │   │   └── Register.jsx      # Sign up page
│   │   ├── services/
│   │   │   └── api.js            # Axios client with JWT interceptor
│   │   ├── App.jsx               # Protected & public routes
│   │   ├── index.css             # Tailwind base & custom scrollbars
│   │   └── main.jsx
│   ├── tailwind.config.js
│   ├── vite.config.js
│   └── package.json
│
├── docs/
│   ├── architecture.md           # System architecture & sequence diagrams
│   ├── database.md               # Complete ER diagram & schema reference
│   └── api_documentation.md      # Comprehensive REST API specifications
│
├── .gitignore
├── requirements.txt
└── README.md
```

---

## 🚀 Installation & Setup

### Prerequisites
- Python 3.10+ (tested on Python 3.13)
- Node.js 18+ (tested on Node.js 24)
- npm or pnpm

---

### Step 1: Backend Setup

1. Open a terminal and navigate to the `backend/` folder:
   ```bash
   cd backend
   ```

2. Activate the virtual environment:
   - **Windows:**
     ```powershell
     .\venv\Scripts\activate
     ```
   - **Linux / macOS:**
     ```bash
     source venv/bin/activate
     ```

3. Install backend dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Configure environment variables:
   ```bash
   cp .env.example .env
   ```
   *(Optional) If you have an OpenAI API key, set `OPENAI_API_KEY=sk-...` in `.env`. If left empty, the application automatically uses the intelligent educational fallback engine.*

5. Run automated tests to verify your setup:
   ```bash
   pytest tests -v
   ```

6. Start the FastAPI backend server:
   ```bash
   python main.py
   ```
   *(Or via uvicorn: `uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload`)*

   - **Backend API URL:** `http://localhost:8000`
   - **Interactive API Documentation:** `http://localhost:8000/docs`

---

### Step 2: Frontend Setup

1. Open a second terminal and navigate to the `frontend/` folder:
   ```bash
   cd frontend
   ```

2. Install dependencies:
   ```bash
   npm install
   ```

3. Start the Vite development server:
   ```bash
   npm run dev
   ```

4. Open your browser at:
   - **Frontend Application URL:** `http://localhost:5173`

---

## 🧪 Testing Results

The automated test suite in `backend/tests/test_study_planner.py` executes 11 comprehensive integration test suites:

```text
tests/test_study_planner.py::test_health_check PASSED                    [  9%]
tests/test_study_planner.py::test_auth_workflow PASSED                   [ 18%]
tests/test_study_planner.py::test_preferences_and_profile PASSED         [ 27%]
tests/test_study_planner.py::test_subjects_and_topics_crud PASSED        [ 36%]
tests/test_study_planner.py::test_examination_management PASSED          [ 45%]
tests/test_study_planner.py::test_plan_generation_and_sessions PASSED    [ 54%]
tests/test_study_planner.py::test_adaptive_planning PASSED               [ 63%]
tests/test_study_planner.py::test_progress_analytics PASSED              [ 72%]
tests/test_study_planner.py::test_ai_chatbot_and_quiz PASSED             [ 81%]
tests/test_study_planner.py::test_spaced_revisions PASSED                [ 90%]
tests/test_study_planner.py::test_user_data_isolation PASSED             [100%]

============================= 11 passed in 3.39s ==============================
```

---

## 🔒 Security Best Practices

- **Passlib & bcrypt:** Password hashing using standard salt generation.
- **JWT Authentication:** Strict token expiry and user verification on every protected request.
- **Data Isolation:** User ID is extracted from validated JWT payload on every DB query; students can never access or modify another student's data.
- **CORS & Env Security:** Keys and database credentials strictly isolated to `.env` (gitignored).

---

## 🤝 Git & GitHub Integration

This project is prepared for version control with a clean `.gitignore` (ignoring `.env`, `node_modules`, `venv`, `*.db`, and build caches).

### To commit your changes locally:
```bash
git add backend/app backend/tests backend/requirements.txt backend/.env.example frontend/src frontend/public frontend/package.json frontend/tailwind.config.js frontend/vite.config.js docs README.md requirements.txt .gitignore
git commit -m "feat: complete AI-powered study planner application"
```

### To publish to a new GitHub repository:
1. Create a new repository on GitHub named `AI-Study-Planner`.
2. Connect your repository:
   ```bash
   git remote add origin https://github.com/<your-username>/AI-Study-Planner.git
   git branch -M main
   git push -u origin main
   ```

