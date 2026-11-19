from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Optional
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.all_models import User, Subject, Topic, TopicStatus
from app.schemas.all_schemas import TopicCreate, TopicUpdate, TopicResponse
from app.services.revision_service import revision_service

router = APIRouter(prefix="/topics", tags=["Topics"])

@router.get("", response_model=List[TopicResponse])
def get_topics(
    subject_id: Optional[int] = None,
    status_filter: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    query = db.query(Topic).join(Subject).filter(Subject.user_id == current_user.id)
    if subject_id:
        query = query.filter(Topic.subject_id == subject_id)
    if status_filter:
        query = query.filter(Topic.status == status_filter)

    return query.order_by(Topic.id.desc()).all()

@router.post("", response_model=TopicResponse, status_code=status.HTTP_201_CREATED)
def create_topic(
    topic_in: TopicCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    subject = db.query(Subject).filter(
        Subject.id == topic_in.subject_id,
        Subject.user_id == current_user.id
    ).first()
    if not subject:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Subject not found")

    topic = Topic(
        subject_id=subject.id,
        name=topic_in.name.strip(),
        description=topic_in.description.strip() if topic_in.description else "",
        difficulty=topic_in.difficulty,
        estimated_time_minutes=topic_in.estimated_time_minutes,
        revision_required=topic_in.revision_required,
        status=TopicStatus.PENDING.value
    )
    db.add(topic)
    db.commit()
    db.refresh(topic)
    return topic

@router.get("/{topic_id}", response_model=TopicResponse)
def get_topic(
    topic_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    topic = db.query(Topic).join(Subject).filter(
        Topic.id == topic_id,
        Subject.user_id == current_user.id
    ).first()
    if not topic:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Topic not found")
    return topic

@router.put("/{topic_id}", response_model=TopicResponse)
def update_topic(
    topic_id: int,
    topic_in: TopicUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    topic = db.query(Topic).join(Subject).filter(
        Topic.id == topic_id,
        Subject.user_id == current_user.id
    ).first()
    if not topic:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Topic not found")

    old_status = topic.status

    if topic_in.name is not None:
        topic.name = topic_in.name.strip()
    if topic_in.description is not None:
        topic.description = topic_in.description.strip()
    if topic_in.difficulty is not None:
        topic.difficulty = topic_in.difficulty
    if topic_in.estimated_time_minutes is not None:
        topic.estimated_time_minutes = topic_in.estimated_time_minutes
    if topic_in.actual_time_spent_minutes is not None:
        topic.actual_time_spent_minutes = topic_in.actual_time_spent_minutes
        topic.last_studied_date = datetime.now(timezone.utc)
    if topic_in.completion_percentage is not None:
        topic.completion_percentage = topic_in.completion_percentage
        if topic.completion_percentage == 100:
            topic.status = TopicStatus.COMPLETED.value
        elif topic.completion_percentage > 0 and topic.status == TopicStatus.PENDING.value:
            topic.status = TopicStatus.IN_PROGRESS.value
    if topic_in.status is not None:
        topic.status = topic_in.status
        if topic.status == TopicStatus.COMPLETED.value:
            topic.completion_percentage = 100
            topic.last_studied_date = datetime.now(timezone.utc)
    if topic_in.revision_required is not None:
        topic.revision_required = topic_in.revision_required

    db.commit()
    db.refresh(topic)

    # If newly marked completed, automatically trigger spaced revision cycle
    if old_status != TopicStatus.COMPLETED.value and topic.status == TopicStatus.COMPLETED.value:
        revision_service.schedule_revision(
            db=db,
            user_id=current_user.id,
            subject_id=topic.subject_id,
            topic_id=topic.id,
            step=1,
            offset_days=1
        )

    return topic

@router.delete("/{topic_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_topic(
    topic_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    topic = db.query(Topic).join(Subject).filter(
        Topic.id == topic_id,
        Subject.user_id == current_user.id
    ).first()
    if not topic:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Topic not found")

    db.delete(topic)
    db.commit()
    return None

