from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import List, Optional
from datetime import datetime, date, timedelta, timezone
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.all_models import (
    User, StudySession, Topic, Subject, ProgressRecord,
    SessionStatus, TopicStatus
)
from app.schemas.all_schemas import (
    PlanGenerateRequest, PlanResponse, StudySessionResponse,
    SessionStatusUpdate, PlanAdjustRequest
)
from app.services.planner_service import planner_service
from app.services.adaptive_service import adaptive_service
from app.services.revision_service import revision_service

router = APIRouter(tags=["Study Plans & Sessions"])

@router.post("/plans/generate", response_model=PlanResponse)
def generate_study_plan(
    req: PlanGenerateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    plan_data = planner_service.generate_plan(
        db=db,
        user=current_user,
        plan_type=req.plan_type,
        target_date_str=req.target_date,
        focus_subject_ids=req.focus_subject_ids,
        regenerate=req.regenerate
    )
    return plan_data

@router.get("/plans/daily", response_model=List[StudySessionResponse])
def get_daily_plan(
    target_date: Optional[str] = Query(None, description="Date in YYYY-MM-DD format"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    date_str = target_date if target_date else date.today().strftime("%Y-%m-%d")
    sessions = db.query(StudySession).filter(
        StudySession.user_id == current_user.id,
        StudySession.session_date == date_str
    ).order_by(StudySession.start_time.asc()).all()

    results = []
    for s in sessions:
        results.append(StudySessionResponse(
            id=s.id,
            user_id=s.user_id,
            subject_id=s.subject_id,
            topic_id=s.topic_id,
            subject_name=s.subject.name if s.subject else "General",
            subject_color=s.subject.color if s.subject else "#4F46E5",
            topic_name=s.topic.name if s.topic else "General Study",
            session_date=s.session_date,
            start_time=s.start_time,
            end_time=s.end_time,
            duration_minutes=s.duration_minutes,
            priority=s.priority,
            session_type=s.session_type,
            status=s.status,
            ai_recommendation=s.ai_recommendation or "",
            notes=s.notes or "",
            plan_type=s.plan_type,
            created_at=s.created_at
        ))
    return results

@router.get("/plans/weekly", response_model=List[StudySessionResponse])
def get_weekly_plan(
    start_date_str: Optional[str] = Query(None, description="Start date in YYYY-MM-DD format"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if start_date_str:
        try:
            start_d = datetime.strptime(start_date_str, "%Y-%m-%d").date()
        except ValueError:
            start_d = date.today()
    else:
        start_d = date.today()

    end_d = start_d + timedelta(days=6)

    sessions = db.query(StudySession).filter(
        StudySession.user_id == current_user.id,
        StudySession.session_date >= start_d.strftime("%Y-%m-%d"),
        StudySession.session_date <= end_d.strftime("%Y-%m-%d")
    ).order_by(StudySession.session_date.asc(), StudySession.start_time.asc()).all()

    results = []
    for s in sessions:
        results.append(StudySessionResponse(
            id=s.id,
            user_id=s.user_id,
            subject_id=s.subject_id,
            topic_id=s.topic_id,
            subject_name=s.subject.name if s.subject else "General",
            subject_color=s.subject.color if s.subject else "#4F46E5",
            topic_name=s.topic.name if s.topic else "General Study",
            session_date=s.session_date,
            start_time=s.start_time,
            end_time=s.end_time,
            duration_minutes=s.duration_minutes,
            priority=s.priority,
            session_type=s.session_type,
            status=s.status,
            ai_recommendation=s.ai_recommendation or "",
            notes=s.notes or "",
            plan_type=s.plan_type,
            created_at=s.created_at
        ))
    return results

@router.post("/plans/adjust")
def adjust_study_plan(
    req: PlanAdjustRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    result = adaptive_service.adjust_study_plan(db=db, user=current_user, reason=req.reason)
    return result

@router.put("/sessions/{session_id}/status", response_model=StudySessionResponse)
def update_session_status(
    session_id: int,
    status_in: SessionStatusUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    session = db.query(StudySession).filter(
        StudySession.id == session_id,
        StudySession.user_id == current_user.id
    ).first()
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Study session not found")

    session.status = status_in.status
    if status_in.notes:
        session.notes = status_in.notes

    actual_duration = status_in.actual_minutes if status_in.actual_minutes is not None else session.duration_minutes

    # If completed or partially completed, log a ProgressRecord and update Topic stats
    if status_in.status in [SessionStatus.COMPLETED.value, SessionStatus.PARTIALLY_COMPLETED.value]:
        # Record progress
        prog = ProgressRecord(
            user_id=current_user.id,
            session_id=session.id,
            study_date=session.session_date,
            duration_minutes=actual_duration,
            status=status_in.status,
            notes=status_in.notes or ""
        )
        db.add(prog)

        if session.topic_id:
            topic = db.query(Topic).filter(Topic.id == session.topic_id).first()
            if topic:
                topic.actual_time_spent_minutes += actual_duration
                topic.last_studied_date = datetime.now(timezone.utc)

                # Update completion percentage
                est = topic.estimated_time_minutes or 60
                calc_pct = min(100, int((topic.actual_time_spent_minutes / est) * 100))
                if status_in.status == SessionStatus.COMPLETED.value and calc_pct >= 90:
                    topic.completion_percentage = 100
                    topic.status = TopicStatus.COMPLETED.value
                    # Trigger spaced revision step 1
                    revision_service.schedule_revision(
                        db=db,
                        user_id=current_user.id,
                        subject_id=topic.subject_id,
                        topic_id=topic.id,
                        step=1,
                        offset_days=1
                    )
                else:
                    topic.completion_percentage = max(topic.completion_percentage, calc_pct)
                    if topic.status == TopicStatus.PENDING.value:
                        topic.status = TopicStatus.IN_PROGRESS.value

    db.commit()
    db.refresh(session)

    return StudySessionResponse(
        id=session.id,
        user_id=session.user_id,
        subject_id=session.subject_id,
        topic_id=session.topic_id,
        subject_name=session.subject.name if session.subject else "General",
        subject_color=session.subject.color if session.subject else "#4F46E5",
        topic_name=session.topic.name if session.topic else "General Study",
        session_date=session.session_date,
        start_time=session.start_time,
        end_time=session.end_time,
        duration_minutes=session.duration_minutes,
        priority=session.priority,
        session_type=session.session_type,
        status=session.status,
        ai_recommendation=session.ai_recommendation or "",
        notes=session.notes or "",
        plan_type=session.plan_type,
        created_at=session.created_at
    )

