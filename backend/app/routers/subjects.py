from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.all_models import User, Subject, Topic, TopicStatus
from app.schemas.all_schemas import (
    SubjectCreate, SubjectUpdate, SubjectResponse, SubjectDetailResponse
)

router = APIRouter(prefix="/subjects", tags=["Subjects"])

@router.get("", response_model=List[SubjectResponse])
def get_subjects(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    subjects = db.query(Subject).filter(Subject.user_id == current_user.id).order_by(Subject.id.desc()).all()
    results = []
    for s in subjects:
        total_topics = len(s.topics)
        completed = sum(1 for t in s.topics if t.status == TopicStatus.COMPLETED.value)
        progress = int((completed / total_topics) * 100) if total_topics > 0 else 0

        results.append(SubjectResponse(
            id=s.id,
            user_id=s.user_id,
            name=s.name,
            description=s.description or "",
            color=s.color or "#4F46E5",
            difficulty=s.difficulty,
            priority=s.priority,
            topics_count=total_topics,
            completed_topics_count=completed,
            progress_percentage=progress,
            created_at=s.created_at
        ))
    return results

@router.post("", response_model=SubjectResponse, status_code=status.HTTP_201_CREATED)
def create_subject(
    subj_in: SubjectCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    subject = Subject(
        user_id=current_user.id,
        name=subj_in.name.strip(),
        description=subj_in.description.strip() if subj_in.description else "",
        color=subj_in.color or "#4F46E5",
        difficulty=subj_in.difficulty,
        priority=subj_in.priority
    )
    db.add(subject)
    db.commit()
    db.refresh(subject)
    return SubjectResponse(
        id=subject.id,
        user_id=subject.user_id,
        name=subject.name,
        description=subject.description,
        color=subject.color,
        difficulty=subject.difficulty,
        priority=subject.priority,
        topics_count=0,
        completed_topics_count=0,
        progress_percentage=0,
        created_at=subject.created_at
    )

@router.get("/{subject_id}", response_model=SubjectDetailResponse)
def get_subject_detail(
    subject_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    subject = db.query(Subject).filter(Subject.id == subject_id, Subject.user_id == current_user.id).first()
    if not subject:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Subject not found")

    total_topics = len(subject.topics)
    completed = sum(1 for t in subject.topics if t.status == TopicStatus.COMPLETED.value)
    progress = int((completed / total_topics) * 100) if total_topics > 0 else 0

    return SubjectDetailResponse(
        id=subject.id,
        user_id=subject.user_id,
        name=subject.name,
        description=subject.description or "",
        color=subject.color,
        difficulty=subject.difficulty,
        priority=subject.priority,
        topics_count=total_topics,
        completed_topics_count=completed,
        progress_percentage=progress,
        created_at=subject.created_at,
        topics=subject.topics
    )

@router.put("/{subject_id}", response_model=SubjectResponse)
def update_subject(
    subject_id: int,
    subj_in: SubjectUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    subject = db.query(Subject).filter(Subject.id == subject_id, Subject.user_id == current_user.id).first()
    if not subject:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Subject not found")

    if subj_in.name is not None:
        subject.name = subj_in.name.strip()
    if subj_in.description is not None:
        subject.description = subj_in.description.strip()
    if subj_in.color is not None:
        subject.color = subj_in.color
    if subj_in.difficulty is not None:
        subject.difficulty = subj_in.difficulty
    if subj_in.priority is not None:
        subject.priority = subj_in.priority

    db.commit()
    db.refresh(subject)

    total_topics = len(subject.topics)
    completed = sum(1 for t in subject.topics if t.status == TopicStatus.COMPLETED.value)
    progress = int((completed / total_topics) * 100) if total_topics > 0 else 0

    return SubjectResponse(
        id=subject.id,
        user_id=subject.user_id,
        name=subject.name,
        description=subject.description,
        color=subject.color,
        difficulty=subject.difficulty,
        priority=subject.priority,
        topics_count=total_topics,
        completed_topics_count=completed,
        progress_percentage=progress,
        created_at=subject.created_at
    )

@router.delete("/{subject_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_subject(
    subject_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    subject = db.query(Subject).filter(Subject.id == subject_id, Subject.user_id == current_user.id).first()
    if not subject:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Subject not found")

    db.delete(subject)
    db.commit()
    return None

