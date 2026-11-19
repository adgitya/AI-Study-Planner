from datetime import datetime, date, timedelta, timezone
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from app.models.all_models import (
    RevisionSchedule, Topic, Subject, User
)

STEP_OFFSETS = {
    1: 1,   # 1 day later
    2: 3,   # 3 days later
    3: 7,   # 7 days later
    4: 14   # 14 days later
}

class RevisionService:
    def schedule_revision(
        self,
        db: Session,
        user_id: int,
        subject_id: int,
        topic_id: int,
        step: int = 1,
        offset_days: Optional[int] = None
    ) -> RevisionSchedule:
        """Schedules a spaced revision entry for a topic."""
        days_ahead = offset_days if offset_days is not None else STEP_OFFSETS.get(step, 1)
        sched_date = (date.today() + timedelta(days=days_ahead)).strftime("%Y-%m-%d")

        # Check if an active pending revision for this topic and step already exists
        existing = db.query(RevisionSchedule).filter(
            RevisionSchedule.user_id == user_id,
            RevisionSchedule.topic_id == topic_id,
            RevisionSchedule.status == "Pending"
        ).first()

        if existing:
            existing.scheduled_date = sched_date
            existing.revision_step = step
            db.commit()
            db.refresh(existing)
            return existing

        rev = RevisionSchedule(
            user_id=user_id,
            subject_id=subject_id,
            topic_id=topic_id,
            revision_step=step,
            scheduled_date=sched_date,
            status="Pending"
        )
        db.add(rev)
        db.commit()
        db.refresh(rev)
        return rev

    def complete_revision(self, db: Session, user: User, revision_id: int) -> Dict[str, Any]:
        rev = db.query(RevisionSchedule).filter(
            RevisionSchedule.id == revision_id,
            RevisionSchedule.user_id == user.id
        ).first()

        if not rev:
            raise ValueError("Revision schedule not found")

        rev.status = "Completed"
        rev.completed_at = datetime.now(timezone.utc)
        db.commit()

        # If step < 4, automatically schedule next spaced repetition step
        next_step = rev.revision_step + 1
        next_rev = None
        if next_step <= 4:
            next_rev = self.schedule_revision(
                db=db,
                user_id=user.id,
                subject_id=rev.subject_id,
                topic_id=rev.topic_id,
                step=next_step
            )

        # Clear revision_required flag on topic if reached advanced step
        topic = db.query(Topic).filter(Topic.id == rev.topic_id).first()
        if topic and next_step > 2:
            topic.revision_required = False
            db.commit()

        return {
            "message": "Revision marked as completed",
            "completed_step": rev.revision_step,
            "next_step": next_step if next_step <= 4 else None,
            "next_scheduled_date": next_rev.scheduled_date if next_rev else None
        }

    def get_user_revisions(self, db: Session, user: User) -> List[Dict[str, Any]]:
        today_str = date.today().strftime("%Y-%m-%d")
        items = db.query(RevisionSchedule).filter(
            RevisionSchedule.user_id == user.id
        ).order_by(RevisionSchedule.scheduled_date.asc()).all()

        results = []
        for r in items:
            results.append({
                "id": r.id,
                "topic_id": r.topic_id,
                "subject_id": r.subject_id,
                "topic_name": r.topic.name if r.topic else "Unknown Topic",
                "subject_name": r.subject.name if r.subject else "Unknown Subject",
                "subject_color": r.subject.color if r.subject else "#4F46E5",
                "revision_step": r.revision_step,
                "scheduled_date": r.scheduled_date,
                "status": r.status,
                "completed_at": r.completed_at,
                "is_overdue": (r.status == "Pending" and r.scheduled_date < today_str)
            })
        return results

revision_service = RevisionService()

