import pytest
import os
import sys

# Ensure backend root is on sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
os.environ["TESTING"] = "true"

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from app.main import app
from app.core.database import Base, get_db
from app.models.all_models import User, StudentPreferences

# StaticPool with in-memory SQLite ensures single connection persistence across requests in tests
engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

@pytest.fixture(scope="session", autouse=True)
def setup_database():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

client = TestClient(app)

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"

def test_auth_workflow():
    # 1. Register User 1
    reg_resp = client.post("/api/v1/auth/register", json={
        "full_name": "Alice Turing",
        "email": "alice@example.com",
        "password": "Password123!",
        "confirm_password": "Password123!"
    })
    assert reg_resp.status_code == 201
    data = reg_resp.json()
    assert "access_token" in data
    assert data["user"]["email"] == "alice@example.com"
    token = data["access_token"]

    # 2. Login
    login_resp = client.post("/api/v1/auth/login", json={
        "email": "alice@example.com",
        "password": "Password123!"
    })
    assert login_resp.status_code == 200
    assert "access_token" in login_resp.json()

    # 3. Get /me
    me_resp = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me_resp.status_code == 200
    assert me_resp.json()["full_name"] == "Alice Turing"

def test_preferences_and_profile():
    # Login as Alice
    login_resp = client.post("/api/v1/auth/login", json={
        "email": "alice@example.com",
        "password": "Password123!"
    })
    token = login_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Get profile
    prof_resp = client.get("/api/v1/profile", headers=headers)
    assert prof_resp.status_code == 200
    assert prof_resp.json()["daily_study_hours"] == 4.0

    # Update profile
    upd_resp = client.put("/api/v1/profile", headers=headers, json={
        "daily_study_hours": 5.0,
        "preferred_start_time": "08:00",
        "preferred_end_time": "20:00",
        "preferred_study_days": "Monday,Tuesday,Wednesday,Thursday,Friday",
        "break_duration": 20,
        "academic_goals": "Score an A in Computer Networks and Operating Systems",
        "preferred_learning_style": "Kinesthetic"
    })
    assert upd_resp.status_code == 200
    assert upd_resp.json()["daily_study_hours"] == 5.0
    assert upd_resp.json()["break_duration"] == 20

def test_subjects_and_topics_crud():
    login_resp = client.post("/api/v1/auth/login", json={
        "email": "alice@example.com",
        "password": "Password123!"
    })
    token = login_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Create Subject
    subj_resp = client.post("/api/v1/subjects", headers=headers, json={
        "name": "Operating Systems",
        "description": "Processes, Threads, and Deadlocks",
        "color": "#6366F1",
        "difficulty": "Hard",
        "priority": "High"
    })
    assert subj_resp.status_code == 201
    subj_data = subj_resp.json()
    subject_id = subj_data["id"]

    # 2. Add Topic 1
    t1_resp = client.post("/api/v1/topics", headers=headers, json={
        "subject_id": subject_id,
        "name": "Deadlock Avoidance & Banker's Algorithm",
        "description": "Safe state and resource allocation graph",
        "difficulty": "Hard",
        "estimated_time_minutes": 90,
        "revision_required": False
    })
    assert t1_resp.status_code == 201
    topic_id = t1_resp.json()["id"]

    # 3. Add Topic 2
    t2_resp = client.post("/api/v1/topics", headers=headers, json={
        "subject_id": subject_id,
        "name": "CPU Scheduling Algorithms",
        "description": "Round Robin, SJF, and Multi-level queues",
        "difficulty": "Medium",
        "estimated_time_minutes": 60,
        "revision_required": False
    })
    assert t2_resp.status_code == 201

    # 4. Verify topics under subject
    list_resp = client.get(f"/api/v1/topics?subject_id={subject_id}", headers=headers)
    assert list_resp.status_code == 200
    assert len(list_resp.json()) == 2

def test_examination_management():
    login_resp = client.post("/api/v1/auth/login", json={
        "email": "alice@example.com",
        "password": "Password123!"
    })
    token = login_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Get subjects
    subj_list = client.get("/api/v1/subjects", headers=headers).json()
    subject_id = subj_list[0]["id"]

    # Create Exam in 10 days
    from datetime import datetime, timedelta
    exam_date = (datetime.now() + timedelta(days=10)).isoformat()

    exam_resp = client.post("/api/v1/exams", headers=headers, json={
        "subject_id": subject_id,
        "title": "Midterm Exam OS",
        "exam_date": exam_date,
        "priority": "High",
        "notes": "Covers chapters 1 to 5"
    })
    assert exam_resp.status_code == 201
    exam_data = exam_resp.json()
    assert exam_data["days_remaining"] >= 9
    assert exam_data["subject_name"] == "Operating Systems"

def test_plan_generation_and_sessions():
    login_resp = client.post("/api/v1/auth/login", json={
        "email": "alice@example.com",
        "password": "Password123!"
    })
    token = login_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Generate Weekly Plan
    plan_resp = client.post("/api/v1/plans/generate", headers=headers, json={
        "plan_type": "weekly",
        "regenerate": True
    })
    assert plan_resp.status_code == 200
    plan_data = plan_resp.json()
    assert plan_data["total_sessions"] > 0
    assert len(plan_data["sessions"]) > 0

    session_id = plan_data["sessions"][0]["id"]

    # Verify no overlapping sessions on any day
    sessions_by_day = {}
    for s in plan_data["sessions"]:
        day = s["session_date"]
        sessions_by_day.setdefault(day, []).append(s)

    for day, day_sessions in sessions_by_day.items():
        day_sessions.sort(key=lambda x: x["start_time"])
        for i in range(len(day_sessions) - 1):
            s1_end = day_sessions[i]["end_time"]
            s2_start = day_sessions[i + 1]["start_time"]
            assert s1_end <= s2_start, f"Overlapping sessions on {day}: {s1_end} > {s2_start}"

    # Mark session as Completed
    stat_resp = client.put(f"/api/v1/sessions/{session_id}/status", headers=headers, json={
        "status": "Completed",
        "actual_minutes": 60,
        "notes": "Understood the Banker's algorithm thoroughly"
    })
    assert stat_resp.status_code == 200
    assert stat_resp.json()["status"] == "Completed"

def test_adaptive_planning():
    login_resp = client.post("/api/v1/auth/login", json={
        "email": "alice@example.com",
        "password": "Password123!"
    })
    token = login_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Call /plans/adjust
    adj_resp = client.post("/api/v1/plans/adjust", headers=headers, json={
        "reason": "Test progress adjustment"
    })
    assert adj_resp.status_code == 200
    data = adj_resp.json()
    assert "explanation" in data
    assert "plan" in data

def test_progress_analytics():
    login_resp = client.post("/api/v1/auth/login", json={
        "email": "alice@example.com",
        "password": "Password123!"
    })
    token = login_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    prog_resp = client.get("/api/v1/progress", headers=headers)
    assert prog_resp.status_code == 200
    pdata = prog_resp.json()
    assert "total_study_hours" in pdata
    assert "weekly_hours_by_day" in pdata
    assert "subject_progress" in pdata
    assert "task_status_distribution" in pdata
    assert pdata["total_study_hours"] > 0

def test_ai_chatbot_and_quiz():
    login_resp = client.post("/api/v1/auth/login", json={
        "email": "alice@example.com",
        "password": "Password123!"
    })
    token = login_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Chatbot endpoint
    chat_resp = client.post("/api/v1/ai/chat", headers=headers, json={
        "content": "Which subject should I prioritize today for my examinations?"
    })
    assert chat_resp.status_code == 200
    chat_data = chat_resp.json()
    assert "assistant_message" in chat_data
    assert len(chat_data["assistant_message"]["content"]) > 10

    # 2. Quiz generation
    subj_list = client.get("/api/v1/subjects", headers=headers).json()
    subject_id = subj_list[0]["id"]
    topics_list = client.get(f"/api/v1/topics?subject_id={subject_id}", headers=headers).json()
    topic_id = topics_list[0]["id"]

    quiz_resp = client.post("/api/v1/ai/generate-quiz", headers=headers, json={
        "subject_id": subject_id,
        "topic_id": topic_id,
        "difficulty": "Medium",
        "num_questions": 3
    })
    assert quiz_resp.status_code == 200
    q_data = quiz_resp.json()
    assert "attempt_id" in q_data
    assert len(q_data["questions"]) == 3

    # 3. Submit quiz answers
    attempt_id = q_data["attempt_id"]
    answers = [
        {"question_id": q["id"], "selected_option": "A"}
        for q in q_data["questions"]
    ]
    sub_resp = client.post("/api/v1/ai/submit-quiz", headers=headers, json={
        "attempt_id": attempt_id,
        "answers": answers
    })
    assert sub_resp.status_code == 200
    res_data = sub_resp.json()
    assert "score_percentage" in res_data
    assert "questions" in res_data

def test_spaced_revisions():
    login_resp = client.post("/api/v1/auth/login", json={
        "email": "alice@example.com",
        "password": "Password123!"
    })
    token = login_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Fetch revisions
    rev_resp = client.get("/api/v1/revision", headers=headers)
    assert rev_resp.status_code == 200
    revs = rev_resp.json()
    if len(revs) > 0:
        rev_id = revs[0]["id"]
        comp_resp = client.post(f"/api/v1/revision/{rev_id}/complete", headers=headers)
        assert comp_resp.status_code == 200
        assert "completed_step" in comp_resp.json()

def test_partial_quiz_submission_and_empty_progress():
    login_resp = client.post("/api/v1/auth/login", json={
        "email": "alice@example.com",
        "password": "Password123!"
    })
    token = login_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    subj_list = client.get("/api/v1/subjects", headers=headers).json()
    subject_id = subj_list[0]["id"]
    topics_list = client.get(f"/api/v1/topics?subject_id={subject_id}", headers=headers).json()
    topic_id = topics_list[0]["id"]

    # Generate 3-question quiz
    quiz_resp = client.post("/api/v1/ai/generate-quiz", headers=headers, json={
        "subject_id": subject_id,
        "topic_id": topic_id,
        "difficulty": "Easy",
        "num_questions": 3
    })
    assert quiz_resp.status_code == 200
    q_data = quiz_resp.json()
    attempt_id = q_data["attempt_id"]

    # Only answer 1 question out of 3
    partial_answers = [
        {"question_id": q_data["questions"][0]["id"], "selected_option": "A"}
    ]
    sub_resp = client.post("/api/v1/ai/submit-quiz", headers=headers, json={
        "attempt_id": attempt_id,
        "answers": partial_answers
    })
    assert sub_resp.status_code == 200
    eval_data = sub_resp.json()
    # All 3 questions must be returned in results
    assert len(eval_data["questions"]) == 3
    # Check that unanswered questions have "Unanswered"
    unanswered = [q for q in eval_data["questions"] if q["selected_option"] == "Unanswered"]
    assert len(unanswered) == 2

def test_ai_different_questions_different_responses():
    login_resp = client.post("/api/v1/auth/login", json={
        "email": "alice@example.com",
        "password": "Password123!"
    })
    token = login_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Ask about Pomodoro technique
    r1 = client.post("/api/v1/ai/chat", headers=headers, json={"content": "Explain the Pomodoro technique with an example."})
    assert r1.status_code == 200
    msg1 = r1.json()["assistant_message"]["content"]
    assert "pomodoro" in msg1.lower()
    assert "25" in msg1

    # 2. Ask about Active recall vs passive learning
    r2 = client.post("/api/v1/ai/chat", headers=headers, json={"content": "What is the difference between active recall and passive learning?"})
    assert r2.status_code == 200
    msg2 = r2.json()["assistant_message"]["content"]
    assert "active recall" in msg2.lower()
    assert "passive" in msg2.lower()

    # 3. Ask about Binary search with C++ and Python
    r3 = client.post("/api/v1/ai/chat", headers=headers, json={"content": "Explain binary search with a simple C++ and Python example."})
    assert r3.status_code == 200
    msg3 = r3.json()["assistant_message"]["content"]
    assert "binary search" in msg3.lower()
    assert "cpp" in msg3.lower() or "c++" in msg3.lower()

    # 4. Ask about hours studied this week
    r4 = client.post("/api/v1/ai/chat", headers=headers, json={"content": "How many hours have I studied this week?"})
    assert r4.status_code == 200
    msg4 = r4.json()["assistant_message"]["content"]
    assert "hours" in msg4.lower()

    # 5. Ask for study routine based on available time
    r5 = client.post("/api/v1/ai/chat", headers=headers, json={"content": "Suggest a study routine based on my available time."})
    assert r5.status_code == 200
    msg5 = r5.json()["assistant_message"]["content"]
    assert "routine" in msg5.lower()

    # Verify that different questions receive completely different responses
    responses = [msg1, msg2, msg3, msg4, msg5]
    assert len(set(responses)) == 5, "Every question must receive a distinct, relevant answer!"

def test_scheduler_strict_constraints():
    login_resp = client.post("/api/v1/auth/login", json={
        "email": "alice@example.com",
        "password": "Password123!"
    })
    token = login_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Fetch preferences
    prof = client.get("/api/v1/profile", headers=headers).json()
    start_min = int(prof["preferred_start_time"].split(":")[0]) * 60 + int(prof["preferred_start_time"].split(":")[1])
    end_min = int(prof["preferred_end_time"].split(":")[0]) * 60 + int(prof["preferred_end_time"].split(":")[1])
    daily_limit = int(prof["daily_study_hours"] * 60)
    break_min = prof["break_duration"]

    # Generate plan
    plan_resp = client.post("/api/v1/plans/generate", headers=headers, json={
        "plan_type": "weekly",
        "regenerate": True
    })
    assert plan_resp.status_code == 200
    sessions = plan_resp.json()["sessions"]
    assert len(sessions) > 0

    sessions_by_day = {}
    for s in sessions:
        sessions_by_day.setdefault(s["session_date"], []).append(s)

    for day, day_sessions in sessions_by_day.items():
        total_day_mins = sum(s["duration_minutes"] for s in day_sessions)
        assert total_day_mins <= daily_limit, f"Day {day} exceeded daily limit: {total_day_mins} > {daily_limit}"

        day_sessions.sort(key=lambda x: x["start_time"])
        for i, sess in enumerate(day_sessions):
            sh, sm = map(int, sess["start_time"].split(":"))
            eh, em = map(int, sess["end_time"].split(":"))
            s_min = sh * 60 + sm
            e_min = eh * 60 + em

            assert s_min >= start_min, f"Session started earlier than preferred on {day}: {sess['start_time']}"
            assert e_min <= end_min, f"Session ended later than preferred on {day}: {sess['end_time']}"

            if i < len(day_sessions) - 1:
                next_sh, next_sm = map(int, day_sessions[i + 1]["start_time"].split(":"))
                next_s_min = next_sh * 60 + next_sm
                # Check no overlap and break respected
                assert next_s_min >= e_min + break_min, f"Break duration violated between sessions on {day}"

def test_user_data_isolation():
    # Register User 2 (Bob)
    reg_resp = client.post("/api/v1/auth/register", json={
        "full_name": "Bob Babbage",
        "email": "bob@example.com",
        "password": "Password123!",
        "confirm_password": "Password123!"
    })
    assert reg_resp.status_code == 201
    bob_token = reg_resp.json()["access_token"]
    bob_headers = {"Authorization": f"Bearer {bob_token}"}

    # Bob's subjects should be empty
    bob_subjs = client.get("/api/v1/subjects", headers=bob_headers).json()
    assert len(bob_subjs) == 0

    # Bob's progress should be 0 and efficiency rate should be 0.0%
    bob_prog = client.get("/api/v1/progress", headers=bob_headers).json()
    assert bob_prog["total_study_hours"] == 0.0
    assert bob_prog["total_topics"] == 0
    assert bob_prog["planned_vs_actual_hours"]["efficiency_rate"] == 0.0
