from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.all_models import User, StudentPreferences
from app.schemas.all_schemas import PreferencesResponse, PreferencesUpdate

router = APIRouter(prefix="/profile", tags=["Profile & Preferences"])

@router.get("", response_model=PreferencesResponse)
def get_profile(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    prefs = db.query(StudentPreferences).filter(StudentPreferences.user_id == current_user.id).first()
    if not prefs:
        prefs = StudentPreferences(user_id=current_user.id)
        db.add(prefs)
        db.commit()
        db.refresh(prefs)

    return PreferencesResponse(
        id=prefs.id,
        user_id=current_user.id,
        full_name=current_user.full_name,
        email=current_user.email,
        daily_study_hours=prefs.daily_study_hours,
        preferred_start_time=prefs.preferred_start_time,
        preferred_end_time=prefs.preferred_end_time,
        preferred_study_days=prefs.preferred_study_days,
        break_duration=prefs.break_duration,
        academic_goals=prefs.academic_goals,
        preferred_learning_style=prefs.preferred_learning_style
    )

@router.put("", response_model=PreferencesResponse)
def update_profile(
    pref_in: PreferencesUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if pref_in.full_name:
        current_user.full_name = pref_in.full_name.strip()
        db.commit()

    prefs = db.query(StudentPreferences).filter(StudentPreferences.user_id == current_user.id).first()
    if not prefs:
        prefs = StudentPreferences(user_id=current_user.id)
        db.add(prefs)

    prefs.daily_study_hours = pref_in.daily_study_hours
    prefs.preferred_start_time = pref_in.preferred_start_time
    prefs.preferred_end_time = pref_in.preferred_end_time
    prefs.preferred_study_days = pref_in.preferred_study_days
    prefs.break_duration = pref_in.break_duration
    prefs.academic_goals = pref_in.academic_goals
    prefs.preferred_learning_style = pref_in.preferred_learning_style

    db.commit()
    db.refresh(prefs)

    return PreferencesResponse(
        id=prefs.id,
        user_id=current_user.id,
        full_name=current_user.full_name,
        email=current_user.email,
        daily_study_hours=prefs.daily_study_hours,
        preferred_start_time=prefs.preferred_start_time,
        preferred_end_time=prefs.preferred_end_time,
        preferred_study_days=prefs.preferred_study_days,
        break_duration=prefs.break_duration,
        academic_goals=prefs.academic_goals,
        preferred_learning_style=prefs.preferred_learning_style
    )

