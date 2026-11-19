from datetime import datetime, date, timedelta
from typing import Dict, Any, List
from sqlalchemy.orm import Session
from app.models.all_models import (
    User, StudentPreferences, Subject, Topic, Examination, StudySession,
    SessionStatus, TopicStatus
)
from app.services.planner_service import planner_service
import logging

logger = logging.getLogger(__name__)

class AdaptivePlannerService:
    def adjust_study_plan(self, db: Session, user: User, reason: str = "") -> Dict[str, Any]:
        """
        Continuously adapts future schedule:
        1. Identifies missed/uncompleted/partially completed past sessions.
        2. Recalculates topic priorities and actual duration needs.
        3. Redistributes pending workload across upcoming available days without violating daily hours limit.
        4. Provides a transparent explanation of schedule adjustments.
        """
        today = date.today()
        today_str = today.strftime("%Y-%m-%d")
        now_time_str = datetime.now().strftime("%H:%M")

        # 1. Fetch past pending or not completed sessions up to today
        # Note: Only sessions that are in the past (before today) or scheduled earlier today are considered missed
        all_potential_missed = db.query(StudySession).filter(
            StudySession.user_id == user.id,
            StudySession.session_date <= today_str,
            StudySession.status.in_([SessionStatus.PENDING.value, SessionStatus.NOT_COMPLETED.value, SessionStatus.SKIPPED.value])
        ).all()

        missed_sessions = []
        for s in all_potential_missed:
            if s.session_date < today_str:
                missed_sessions.append(s)
            elif s.session_date == today_str:
                if s.status in [SessionStatus.NOT_COMPLETED.value, SessionStatus.SKIPPED.value]:
                    missed_sessions.append(s)
                elif s.status == SessionStatus.PENDING.value and s.end_time and s.end_time <= now_time_str:
                    missed_sessions.append(s)

        missed_topics_count = len(missed_sessions)
        missed_minutes = sum(s.duration_minutes for s in missed_sessions)

        # Mark overdue pending sessions as NOT_COMPLETED so history reflects reality
        for s in missed_sessions:
            if s.status == SessionStatus.PENDING.value:
                s.status = SessionStatus.NOT_COMPLETED.value
                s.notes = (s.notes or "") + " [Auto-flagged as missed by adaptive scheduler]"
        db.commit()

        # 2. Fetch student preferences
        prefs = db.query(StudentPreferences).filter(StudentPreferences.user_id == user.id).first()
        daily_hours = prefs.daily_study_hours if prefs else 4.0

        # 3. Clean up future pending sessions to regenerate an optimal balanced plan
        tomorrow_str = (today + timedelta(days=1)).strftime("%Y-%m-%d")
        next_week_str = (today + timedelta(days=7)).strftime("%Y-%m-%d")

        db.query(StudySession).filter(
            StudySession.user_id == user.id,
            StudySession.session_date >= today_str,
            StudySession.session_date <= next_week_str,
            StudySession.status == SessionStatus.PENDING.value
        ).delete()
        db.commit()

        # 4. Generate refreshed weekly plan starting from today
        refreshed_plan = planner_service.generate_plan(
            db=db,
            user=user,
            plan_type="weekly",
            target_date_str=today_str,
            regenerate=False
        )

        # 5. Formulate human-readable explanation
        explanation_points = []
        if missed_topics_count > 0:
            explanation_points.append(
                f"Identified {missed_topics_count} missed or uncompleted sessions ({missed_minutes} mins). "
                f"Workload was redistributed across upcoming days within your {daily_hours} hrs/day limit."
            )
        else:
            explanation_points.append("All recent sessions were up to date. Upcoming schedule was re-aligned with current exam priorities.")

        explanation_points.append(
            "Priority topics with approaching examinations and pending revisions received primary morning and peak focus slots."
        )

        return {
            "message": "Study plan successfully adjusted",
            "missed_sessions_reallocated": missed_topics_count,
            "reallocated_minutes": missed_minutes,
            "explanation": " ".join(explanation_points),
            "plan": refreshed_plan
        }

adaptive_service = AdaptivePlannerService()

