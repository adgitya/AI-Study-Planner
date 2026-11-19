from datetime import datetime, date, timedelta, timezone
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from app.models.all_models import (
    User, StudentPreferences, Subject, Topic, Examination, StudySession,
    DifficultyLevel, PriorityLevel, SessionStatus, SessionType, TopicStatus
)
from app.services.ai_service import ai_service
import logging

logger = logging.getLogger(__name__)

class PlannerService:
    def _parse_time_minutes(self, time_str: str) -> int:
        """Converts HH:MM string to minutes from midnight."""
        try:
            parts = time_str.split(":")
            return int(parts[0]) * 60 + int(parts[1])
        except Exception:
            return 9 * 60  # default 09:00

    def _format_minutes_time(self, minutes: int) -> str:
        """Converts minutes from midnight to HH:MM string."""
        h = (minutes // 60) % 24
        m = minutes % 60
        return f"{h:02d}:{m:02d}"

    def calculate_topic_urgency(self, topic: Topic, exams: List[Examination], ref_date: date) -> float:
        """Computes a deterministic priority score for a topic."""
        score = 0.0

        # Topic difficulty weight
        diff = topic.difficulty.capitalize() if topic.difficulty else "Medium"
        if diff == "Hard":
            score += 25.0
        elif diff == "Medium":
            score += 15.0
        else:
            score += 5.0

        # Revision required weight
        if topic.revision_required:
            score += 30.0

        # In progress gets continuation boost
        if topic.status == TopicStatus.IN_PROGRESS.value:
            score += 10.0

        # Associated Subject Exam urgency
        subject_exams = [e for e in exams if e.subject_id == topic.subject_id]
        if subject_exams:
            min_days = 999
            for exam in subject_exams:
                exam_d = exam.exam_date.date() if isinstance(exam.exam_date, datetime) else exam.exam_date
                delta = (exam_d - ref_date).days
                if delta >= 0 and delta < min_days:
                    min_days = delta

            if min_days <= 3:
                score += 60.0
            elif min_days <= 7:
                score += 40.0
            elif min_days <= 14:
                score += 25.0
            elif min_days <= 30:
                score += 15.0

        # Subject general priority
        subj_prio = topic.subject.priority.capitalize() if (topic.subject and topic.subject.priority) else "Medium"
        if subj_prio == "High" or subj_prio == "Urgent":
            score += 15.0

        return score

    def generate_plan(
        self,
        db: Session,
        user: User,
        plan_type: str = "weekly",  # "daily" or "weekly"
        target_date_str: Optional[str] = None,
        focus_subject_ids: Optional[List[int]] = None,
        regenerate: bool = False
    ) -> Dict[str, Any]:
        """Generates a non-overlapping, workload-balanced study schedule."""
        # 1. Load preferences
        prefs = db.query(StudentPreferences).filter(StudentPreferences.user_id == user.id).first()
        if not prefs:
            prefs = StudentPreferences(user_id=user.id)
            db.add(prefs)
            db.commit()
            db.refresh(prefs)

        daily_limit_minutes = int(prefs.daily_study_hours * 60)
        start_min = self._parse_time_minutes(prefs.preferred_start_time)
        end_min = self._parse_time_minutes(prefs.preferred_end_time)
        break_min = max(5, prefs.break_duration)
        allowed_days = [d.strip().capitalize() for d in prefs.preferred_study_days.split(",") if d.strip()]

        # 2. Determine date range
        today = date.today()
        if target_date_str:
            try:
                start_date = datetime.strptime(target_date_str, "%Y-%m-%d").date()
            except ValueError:
                start_date = today
        else:
            start_date = today

        num_days = 1 if plan_type == "daily" else 7
        end_date = start_date + timedelta(days=num_days - 1)

        # 3. If regenerate is True, clean up pending future sessions in that window
        if regenerate:
            db.query(StudySession).filter(
                StudySession.user_id == user.id,
                StudySession.session_date >= start_date.strftime("%Y-%m-%d"),
                StudySession.session_date <= end_date.strftime("%Y-%m-%d"),
                StudySession.status == SessionStatus.PENDING.value
            ).delete()
            db.commit()

        # 4. Fetch candidate topics and exams
        query = db.query(Topic).join(Subject).filter(
            Subject.user_id == user.id,
            Topic.status != TopicStatus.COMPLETED.value
        )
        if focus_subject_ids:
            query = query.filter(Subject.id.in_(focus_subject_ids))
        uncompleted_topics = query.all()

        exams = db.query(Examination).filter(Examination.user_id == user.id).all()

        if not uncompleted_topics:
            return {
                "plan_type": plan_type,
                "start_date": start_date.strftime("%Y-%m-%d"),
                "end_date": end_date.strftime("%Y-%m-%d"),
                "total_sessions": 0,
                "total_study_minutes": 0,
                "sessions": [],
                "ai_summary": "All topics are currently marked as completed! Add new topics or subjects to generate fresh study schedules.",
                "strategy_notes": ["Maintain your knowledge with periodic spaced quizzes."]
            }

        # 5. Score topics by urgency
        scored_topics = []
        for t in uncompleted_topics:
            urgency = self.calculate_topic_urgency(t, exams, start_date)
            scored_topics.append({"topic": t, "urgency": urgency})

        # Sort highest urgency first
        scored_topics.sort(key=lambda x: x["urgency"], reverse=True)

        # 6. Schedule sessions across days
        generated_sessions: List[StudySession] = []
        topic_idx = 0
        total_candidates = len(scored_topics)

        for day_offset in range(num_days):
            current_date = start_date + timedelta(days=day_offset)
            weekday_name = current_date.strftime("%A")

            # Check if this day is allowed
            if weekday_name not in allowed_days and len(allowed_days) > 0:
                continue

            date_str = current_date.strftime("%Y-%m-%d")

            # Check already scheduled minutes for this date to avoid overlaps
            existing_sessions = db.query(StudySession).filter(
                StudySession.user_id == user.id,
                StudySession.session_date == date_str
            ).all()

            existing_minutes = sum(s.duration_minutes for s in existing_sessions)
            remaining_day_minutes = max(0, daily_limit_minutes - existing_minutes)
            if remaining_day_minutes < 30:
                continue

            # Start cursor from the end of the last existing session or preferred_start_time
            current_time_cursor = start_min
            if existing_sessions:
                max_end_time = max(self._parse_time_minutes(s.end_time) for s in existing_sessions)
                current_time_cursor = max(current_time_cursor, max_end_time + break_min)

            daily_scheduled_so_far = 0

            while daily_scheduled_so_far + 45 <= remaining_day_minutes and current_time_cursor + 45 <= end_min:
                candidate = scored_topics[topic_idx % total_candidates]["topic"]
                topic_idx += 1

                # Determine session length (45 to 60 mins)
                session_len = min(60, remaining_day_minutes - daily_scheduled_so_far)
                if current_time_cursor + session_len > end_min:
                    session_len = end_min - current_time_cursor

                if session_len < 30:
                    break

                sess_start_str = self._format_minutes_time(current_time_cursor)
                sess_end_str = self._format_minutes_time(current_time_cursor + session_len)

                # Determine session type
                if candidate.revision_required:
                    sess_type = SessionType.REVISION.value
                elif candidate.actual_time_spent_minutes > 0:
                    sess_type = SessionType.PRACTICE.value
                else:
                    sess_type = SessionType.LEARNING.value

                new_session = StudySession(
                    user_id=user.id,
                    subject_id=candidate.subject_id,
                    topic_id=candidate.id,
                    session_date=date_str,
                    start_time=sess_start_str,
                    end_time=sess_end_str,
                    duration_minutes=session_len,
                    priority=candidate.subject.priority if candidate.subject else PriorityLevel.MEDIUM.value,
                    session_type=sess_type,
                    status=SessionStatus.PENDING.value,
                    plan_type=plan_type,
                    ai_recommendation="",
                    notes=f"Scheduled for {candidate.name}"
                )

                db.add(new_session)
                generated_sessions.append(new_session)

                daily_scheduled_so_far += session_len
                current_time_cursor += session_len + break_min

        db.commit()

        # 7. Enrich with AI personalization
        exam_dicts = [
            {
                "title": e.title,
                "subject_name": e.subject.name if e.subject else "",
                "days_remaining": max(0, ((e.exam_date.date() if isinstance(e.exam_date, datetime) else e.exam_date) - start_date).days)
            }
            for e in exams
        ]
        
        student_profile_dict = {
            "daily_study_hours": prefs.daily_study_hours,
            "break_duration": prefs.break_duration,
            "learning_style": prefs.preferred_learning_style,
            "goals": prefs.academic_goals
        }

        draft_list = [
            {
                "session_date": s.session_date,
                "start_time": s.start_time,
                "duration_minutes": s.duration_minutes,
                "subject_name": s.subject.name if s.subject else "",
                "topic_name": s.topic.name if s.topic else "",
                "session_type": s.session_type
            }
            for s in generated_sessions
        ]

        ai_enhancement = ai_service.personalize_study_plan(student_profile_dict, draft_list, exam_dicts)

        # Update sessions with AI recommendations
        recommendations = ai_enhancement.get("session_recommendations", [])
        for rec in recommendations:
            idx = rec.get("session_index")
            if idx is not None and 0 <= idx < len(generated_sessions):
                generated_sessions[idx].ai_recommendation = rec.get("recommendation", "")

        db.commit()

        # Convert to serializable objects
        return {
            "plan_type": plan_type,
            "start_date": start_date.strftime("%Y-%m-%d"),
            "end_date": end_date.strftime("%Y-%m-%d"),
            "total_sessions": len(generated_sessions),
            "total_study_minutes": sum(s.duration_minutes for s in generated_sessions),
            "sessions": [
                {
                    "id": s.id,
                    "user_id": s.user_id,
                    "subject_id": s.subject_id,
                    "topic_id": s.topic_id,
                    "subject_name": s.subject.name if s.subject else "",
                    "subject_color": s.subject.color if s.subject else "#4F46E5",
                    "topic_name": s.topic.name if s.topic else "",
                    "session_date": s.session_date,
                    "start_time": s.start_time,
                    "end_time": s.end_time,
                    "duration_minutes": s.duration_minutes,
                    "priority": s.priority,
                    "session_type": s.session_type,
                    "status": s.status,
                    "ai_recommendation": s.ai_recommendation,
                    "notes": s.notes,
                    "plan_type": s.plan_type,
                    "created_at": s.created_at
                }
                for s in generated_sessions
            ],
            "ai_summary": ai_enhancement.get("ai_summary", "Plan successfully generated."),
            "strategy_notes": ai_enhancement.get("strategy_notes", [])
        }

planner_service = PlannerService()

