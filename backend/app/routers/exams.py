from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from datetime import datetime, date
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.all_models import User, Subject, Examination
from app.schemas.all_schemas import ExaminationCreate, ExaminationUpdate, ExaminationResponse

router = APIRouter(prefix="/exams", tags=["Examinations"])

@router.get("", response_model=List[ExaminationResponse])
def get_examinations(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    exams = db.query(Examination).filter(
        Examination.user_id == current_user.id
    ).order_by(Examination.exam_date.asc()).all()

    today = date.today()
    results = []
    for e in exams:
        ed = e.exam_date.date() if isinstance(e.exam_date, datetime) else e.exam_date
        delta = (ed - today).days
        is_urgent = (0 <= delta <= 7) or (e.priority == "Urgent")

        results.append(ExaminationResponse(
            id=e.id,
            user_id=e.user_id,
            subject_id=e.subject_id,
            title=e.title,
            exam_date=e.exam_date,
            priority=e.priority,
            notes=e.notes or "",
            subject_name=e.subject.name if e.subject else "General",
            subject_color=e.subject.color if e.subject else "#4F46E5",
            days_remaining=delta,
            is_urgent=is_urgent,
            created_at=e.created_at
        ))
    return results

@router.post("", response_model=ExaminationResponse, status_code=status.HTTP_201_CREATED)
def create_examination(
    exam_in: ExaminationCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    subject = db.query(Subject).filter(
        Subject.id == exam_in.subject_id,
        Subject.user_id == current_user.id
    ).first()
    if not subject:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Subject not found")

    exam = Examination(
        user_id=current_user.id,
        subject_id=exam_in.subject_id,
        title=exam_in.title.strip(),
        exam_date=exam_in.exam_date,
        priority=exam_in.priority,
        notes=exam_in.notes.strip() if exam_in.notes else ""
    )
    db.add(exam)
    db.commit()
    db.refresh(exam)

    today = date.today()
    ed = exam.exam_date.date() if isinstance(exam.exam_date, datetime) else exam.exam_date
    delta = (ed - today).days

    return ExaminationResponse(
        id=exam.id,
        user_id=exam.user_id,
        subject_id=exam.subject_id,
        title=exam.title,
        exam_date=exam.exam_date,
        priority=exam.priority,
        notes=exam.notes,
        subject_name=subject.name,
        subject_color=subject.color,
        days_remaining=delta,
        is_urgent=(0 <= delta <= 7) or (exam.priority == "Urgent"),
        created_at=exam.created_at
    )

@router.put("/{exam_id}", response_model=ExaminationResponse)
def update_examination(
    exam_id: int,
    exam_in: ExaminationUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    exam = db.query(Examination).filter(
        Examination.id == exam_id,
        Examination.user_id == current_user.id
    ).first()
    if not exam:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Examination not found")

    if exam_in.subject_id is not None:
        subject = db.query(Subject).filter(
            Subject.id == exam_in.subject_id,
            Subject.user_id == current_user.id
        ).first()
        if not subject:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Subject not found")
        exam.subject_id = exam_in.subject_id

    if exam_in.title is not None:
        exam.title = exam_in.title.strip()
    if exam_in.exam_date is not None:
        exam.exam_date = exam_in.exam_date
    if exam_in.priority is not None:
        exam.priority = exam_in.priority
    if exam_in.notes is not None:
        exam.notes = exam_in.notes.strip()

    db.commit()
    db.refresh(exam)

    today = date.today()
    ed = exam.exam_date.date() if isinstance(exam.exam_date, datetime) else exam.exam_date
    delta = (ed - today).days

    return ExaminationResponse(
        id=exam.id,
        user_id=exam.user_id,
        subject_id=exam.subject_id,
        title=exam.title,
        exam_date=exam.exam_date,
        priority=exam.priority,
        notes=exam.notes or "",
        subject_name=exam.subject.name if exam.subject else "",
        subject_color=exam.subject.color if exam.subject else "#4F46E5",
        days_remaining=delta,
        is_urgent=(0 <= delta <= 7) or (exam.priority == "Urgent"),
        created_at=exam.created_at
    )

@router.delete("/{exam_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_examination(
    exam_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    exam = db.query(Examination).filter(
        Examination.id == exam_id,
        Examination.user_id == current_user.id
    ).first()
    if not exam:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Examination not found")

    db.delete(exam)
    db.commit()
    return None

