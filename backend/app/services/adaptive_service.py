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
        1. Identifies missed past sessions and partially completed sessions.
        2. Calculates unfinished workload without marking future sessions as missed.
        3. Preserves completed sessions and historical records.
        4. Redistributes pending workload across upcoming available days (exact 7-day window).
        5. Respects student availability, daily limits, and adjustment reasons.
        """
        today = date.today()
        today_str = today.strftime("%Y-%m-%d")
        now_time_str = datetime.now().strftime("%H:%M")

        # 1. Fetch potential missed sessions up to today
        all_past_and_today = db.query(StudySession).filter(
            StudySession.user_id == user.id,
            StudySession.session_date <= today_str
        ).all()

        missed_sessions = []
        partially_completed_sessions = []

        for s in all_past_and_today:
            if s.session_date < today_str:
                # Strictly past sessions
                if s.status in [SessionStatus.PENDING.value, SessionStatus.NOT_COMPLETED.value, SessionStatus.SKIPPED.value]:
                    missed_sessions.append(s)
                elif s.status == SessionStatus.PARTIALLY_COMPLETED.value:
                    partially_completed_sessions.append(s)
            elif s.session_date == today_str:
                # Sessions scheduled for today: only missed if already marked as such or end_time has passed
                if s.status in [SessionStatus.NOT_COMPLETED.value, SessionStatus.SKIPPED.value]:
                    missed_sessions.append(s)
                elif s.status == SessionStatus.PENDING.value and s.end_time and s.end_time <= now_time_str:
                    missed_sessions.append(s)
                elif s.status == SessionStatus.PARTIALLY_COMPLETED.value:
                    partially_completed_sessions.append(s)

        missed_topics_count = len(missed_sessions)
        missed_minutes = sum(s.duration_minutes for s in missed_sessions)
        
        # Partially completed sessions account for remaining half of duration
        partial_minutes = sum(max(15, s.duration_minutes // 2) for s in partially_completed_sessions)
        total_reallocated_minutes = missed_minutes + partial_minutes

        # Mark overdue pending sessions as NOT_COMPLETED so history reflects reality
        reason_tag = f" [Auto-flagged as missed by adaptive scheduler: {reason}]" if reason else " [Auto-flagged as missed by adaptive scheduler]"
        for s in missed_sessions:
            if s.status == SessionStatus.PENDING.value:
                s.status = SessionStatus.NOT_COMPLETED.value
                s.notes = (s.notes or "") + reason_tag

        db.commit()

        # Collect topic IDs needing immediate priority reallocation
        reallocated_topic_ids = list({
            s.topic_id for s in (missed_sessions + partially_completed_sessions) if s.topic_id
        })

        # 2. Fetch student preferences
        prefs = db.query(StudentPreferences).filter(StudentPreferences.user_id == user.id).first()
        daily_hours = prefs.daily_study_hours if prefs else 4.0
        allowed_days = [d.strip().capitalize() for d in (prefs.preferred_study_days or "").split(",") if d.strip()]
        if not allowed_days:
            allowed_days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

        # 3. Clean up ONLY future PENDING sessions across the exact 7-day window (today to today + 6 days)
        # Completed sessions and past records remain untouched
        end_window = today + timedelta(days=6)
        end_window_str = end_window.strftime("%Y-%m-%d")

        db.query(StudySession).filter(
            StudySession.user_id == user.id,
            StudySession.session_date >= today_str,
            StudySession.session_date <= end_window_str,
            StudySession.status == SessionStatus.PENDING.value
        ).delete()
        db.commit()

        # 4. Generate refreshed weekly plan starting from today, prioritizing missed topics
        refreshed_plan = planner_service.generate_plan(
            db=db,
            user=user,
            plan_type="weekly",
            target_date_str=today_str,
            priority_topic_ids=reallocated_topic_ids,
            regenerate=False
        )

        # 5. Check if workload fits into available capacity
        days_in_window = sum(1 for i in range(7) if (today + timedelta(days=i)).strftime("%A") in allowed_days)
        total_capacity_minutes = int(days_in_window * daily_hours * 60)
        scheduled_minutes = refreshed_plan.get("total_study_minutes", 0)

        # 6. Formulate human-readable explanation
        explanation_points = []
        if reason:
            explanation_points.append(f"Reason considered: '{reason}'.")

        if missed_topics_count > 0 or len(partially_completed_sessions) > 0:
            details = []
            if missed_topics_count > 0:
                details.append(f"{missed_topics_count} missed session(s) ({missed_minutes} mins)")
            if partially_completed_sessions:
                details.append(f"{len(partially_completed_sessions)} partially completed session(s) ({partial_minutes} mins)")

            explanation_points.append(
                f"Recovered {' and '.join(details)}. "
                f"Workload was redistributed across upcoming days within your {daily_hours} hrs/day limit without extending past your preferred end time."
            )
        else:
            explanation_points.append(
                "All recent sessions were up to date. Upcoming schedule was re-aligned with current examination deadlines and spaced revision requirements."
            )

        if total_reallocated_minutes > 0 and scheduled_minutes >= total_capacity_minutes:
            explanation_points.append(
                "Warning: Your pending workload is near your maximum weekly study capacity. Consider temporarily increasing daily hours in Profile if an exam is approaching."
            )
        else:
            explanation_points.append(
                "Priority topics with approaching examinations received primary focus slots."
            )

        return {
            "message": "Study plan successfully adjusted",
            "reason": reason,
            "missed_sessions_reallocated": missed_topics_count,
            "partially_completed_reallocated": len(partially_completed_sessions),
            "reallocated_minutes": total_reallocated_minutes,
            "explanation": " ".join(explanation_points),
            "plan": refreshed_plan
        }

adaptive_service = AdaptivePlannerService()
