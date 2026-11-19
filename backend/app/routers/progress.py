from fastapi import APIRouter, Depends
from datetime import datetime, date, timedelta
from typing import Dict, Any, List
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.all_models import (
    User, StudySession, Topic, Subject, ProgressRecord,
    SessionStatus, TopicStatus
)
from app.schemas.all_schemas import ProgressOverview

router = APIRouter(prefix="/progress", tags=["Progress & Analytics"])

@router.get("", response_model=ProgressOverview)
def get_progress_overview(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    today = date.today()
    today_str = today.strftime("%Y-%m-%d")

    # 1. Total study hours from ProgressRecords
    all_records = db.query(ProgressRecord).filter(ProgressRecord.user_id == current_user.id).all()
    total_minutes = sum(r.duration_minutes for r in all_records)
    total_study_hours = round(total_minutes / 60.0, 1)

    # 2. Daily study hours (today)
    today_minutes = sum(r.duration_minutes for r in all_records if r.study_date == today_str)
    daily_study_hours = round(today_minutes / 60.0, 1)

    # 3. Weekly study hours (last 7 days)
    seven_days_ago = (today - timedelta(days=6)).strftime("%Y-%m-%d")
    weekly_minutes = sum(r.duration_minutes for r in all_records if r.study_date >= seven_days_ago)
    weekly_study_hours = round(weekly_minutes / 60.0, 1)

    # 4. Topic counts
    all_topics = db.query(Topic).join(Subject).filter(Subject.user_id == current_user.id).all()
    total_topics = len(all_topics)
    completed_topics = sum(1 for t in all_topics if t.status == TopicStatus.COMPLETED.value)
    pending_topics = total_topics - completed_topics
    overall_completion_rate = round((completed_topics / total_topics * 100), 1) if total_topics > 0 else 0.0

    # 5. Streak calculation (consecutive days ending yesterday or today with completed sessions)
    study_dates_set = {r.study_date for r in all_records if r.duration_minutes > 0}
    streak = 0
    check_day = today
    # If student didn't study yet today, check starting from yesterday
    if today_str not in study_dates_set:
        check_day = today - timedelta(days=1)

    while check_day.strftime("%Y-%m-%d") in study_dates_set:
        streak += 1
        check_day -= timedelta(days=1)

    # 6. Weekly hours by day (past 7 days including today)
    weekly_hours_by_day = []
    total_planned_week = 0
    total_actual_week = 0

    for i in range(6, -1, -1):
        d = today - timedelta(days=i)
        d_str = d.strftime("%Y-%m-%d")
        day_label = d.strftime("%a")

        planned_mins = db.query(func.sum(StudySession.duration_minutes)).filter(
            StudySession.user_id == current_user.id,
            StudySession.session_date == d_str
        ).scalar() or 0

        actual_mins = sum(r.duration_minutes for r in all_records if r.study_date == d_str)

        planned_h = round(planned_mins / 60.0, 1)
        actual_h = round(actual_mins / 60.0, 1)

        total_planned_week += planned_h
        total_actual_week += actual_h

        weekly_hours_by_day.append({
            "day": day_label,
            "date": d_str,
            "planned": planned_h,
            "actual": actual_h
        })

    planned_vs_actual = {
        "planned_hours": round(total_planned_week, 1),
        "actual_hours": round(total_actual_week, 1),
        "efficiency_rate": (
            round((total_actual_week / total_planned_week * 100), 1)
            if total_planned_week > 0
            else (0.0 if total_actual_week == 0 else 100.0)
        )
    }

    # 7. Subject-wise progress
    subjects = db.query(Subject).filter(Subject.user_id == current_user.id).all()
    subject_progress = []
    for s in subjects:
        s_topics = [t for t in all_topics if t.subject_id == s.id]
        s_total = len(s_topics)
        s_comp = sum(1 for t in s_topics if t.status == TopicStatus.COMPLETED.value)
        s_pct = round((s_comp / s_total * 100), 1) if s_total > 0 else 0.0

        s_mins = db.query(func.sum(ProgressRecord.duration_minutes)).join(StudySession).filter(
            ProgressRecord.user_id == current_user.id,
            StudySession.subject_id == s.id
        ).scalar() or 0

        subject_progress.append({
            "subject_id": s.id,
            "subject": s.name,
            "color": s.color or "#4F46E5",
            "progress": s_pct,
            "completed": s_comp,
            "total": s_total,
            "hours_spent": round(s_mins / 60.0, 1)
        })

    # 8. Productivity trend (last 14 days)
    productivity_trend = []
    for i in range(13, -1, -1):
        d = today - timedelta(days=i)
        d_str = d.strftime("%Y-%m-%d")
        day_records = [r for r in all_records if r.study_date == d_str]
        hours = round(sum(r.duration_minutes for r in day_records) / 60.0, 1)
        sessions_count = len(day_records)
        productivity_trend.append({
            "date": d.strftime("%b %d"),
            "hours": hours,
            "sessions": sessions_count
        })

    # 9. Task status distribution
    sessions_all = db.query(StudySession).filter(StudySession.user_id == current_user.id).all()
    status_counts = {
        SessionStatus.COMPLETED.value: 0,
        SessionStatus.PARTIALLY_COMPLETED.value: 0,
        SessionStatus.PENDING.value: 0,
        SessionStatus.NOT_COMPLETED.value: 0,
        SessionStatus.SKIPPED.value: 0
    }
    for s in sessions_all:
        if s.status in status_counts:
            status_counts[s.status] += 1

    task_status_distribution = [
        {"name": "Completed", "value": status_counts[SessionStatus.COMPLETED.value], "color": "#10B981"},
        {"name": "Partially Completed", "value": status_counts[SessionStatus.PARTIALLY_COMPLETED.value], "color": "#F59E0B"},
        {"name": "Pending", "value": status_counts[SessionStatus.PENDING.value], "color": "#6366F1"},
        {"name": "Not Completed", "value": status_counts[SessionStatus.NOT_COMPLETED.value], "color": "#EF4444"},
        {"name": "Skipped", "value": status_counts[SessionStatus.SKIPPED.value], "color": "#9CA3AF"}
    ]

    return ProgressOverview(
        total_study_hours=total_study_hours,
        weekly_study_hours=weekly_study_hours,
        daily_study_hours=daily_study_hours,
        total_topics=total_topics,
        completed_topics=completed_topics,
        pending_topics=pending_topics,
        overall_completion_rate=overall_completion_rate,
        current_streak_days=streak,
        planned_vs_actual_hours=planned_vs_actual,
        weekly_hours_by_day=weekly_hours_by_day,
        subject_progress=subject_progress,
        productivity_trend=productivity_trend,
        task_status_distribution=task_status_distribution
    )

