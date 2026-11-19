from datetime import datetime, date, timedelta, timezone
from typing import List, Dict, Any
from sqlalchemy.orm import Session
from app.models.all_models import (
    Notification, User, StudySession, Examination, RevisionSchedule, SessionStatus
)
from app.core.database import SessionLocal
import logging

logger = logging.getLogger(__name__)

class NotificationService:
    def create_notification(
        self,
        db: Session,
        user_id: int,
        title: str,
        message: str,
        ntype: str = "general"
    ) -> Notification:
        # Prevent exact duplicate unread notifications
        existing = db.query(Notification).filter(
            Notification.user_id == user_id,
            Notification.title == title,
            Notification.is_read == False
        ).first()

        if existing:
            return existing

        notif = Notification(
            user_id=user_id,
            title=title,
            message=message,
            type=ntype
        )
        db.add(notif)
        db.commit()
        db.refresh(notif)
        return notif

    def run_scheduled_checks(self):
        """Executed periodically by APScheduler to generate reminders without spamming."""
        db = SessionLocal()
        try:
            today = date.today()
            today_str = today.strftime("%Y-%m-%d")

            # 1. Upcoming exam alerts (exams in <= 7 days)
            exams = db.query(Examination).all()
            for exam in exams:
                exam_date = exam.exam_date.date() if isinstance(exam.exam_date, datetime) else exam.exam_date
                days_left = (exam_date - today).days
                if 0 <= days_left <= 7:
                    title = f"Exam Alert: {exam.title}"
                    msg = f"Your examination for {exam.subject.name if exam.subject else 'Subject'} is in {days_left} day(s) ({exam_date.strftime('%b %d')})."
                    self.create_notification(db, exam.user_id, title, msg, "exam_alert")

            # 2. Daily sessions reminder
            sessions_today = db.query(StudySession).filter(
                StudySession.session_date == today_str,
                StudySession.status == SessionStatus.PENDING.value
            ).all()

            user_session_counts = {}
            for s in sessions_today:
                user_session_counts[s.user_id] = user_session_counts.get(s.user_id, 0) + 1

            for uid, count in user_session_counts.items():
                title = "Today's Study Schedule"
                msg = f"You have {count} study session(s) scheduled for today. Keep up your momentum!"
                self.create_notification(db, uid, title, msg, "session_reminder")

            # 3. Pending revisions reminder
            pending_revs = db.query(RevisionSchedule).filter(
                RevisionSchedule.scheduled_date <= today_str,
                RevisionSchedule.status == "Pending"
            ).all()

            for rev in pending_revs:
                title = f"Spaced Revision Due: {rev.topic.name if rev.topic else 'Topic'}"
                msg = f"A spaced revision session (Step {rev.revision_step}) is scheduled for today in {rev.subject.name if rev.subject else 'Subject'}."
                self.create_notification(db, rev.user_id, title, msg, "revision_reminder")

        except Exception as e:
            logger.error(f"Error in notification scheduled checks: {e}")
        finally:
            db.close()

notification_service = NotificationService()

