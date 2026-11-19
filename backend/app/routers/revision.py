from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Optional
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.all_models import User
from app.schemas.all_schemas import RevisionResponse, RevisionCompleteRequest
from app.services.revision_service import revision_service

router = APIRouter(prefix="/revision", tags=["Spaced Revision"])

@router.get("", response_model=List[RevisionResponse])
def get_revisions(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return revision_service.get_user_revisions(db, current_user)

@router.post("/{revision_id}/complete")
def complete_revision(
    revision_id: int,
    req: Optional[RevisionCompleteRequest] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        res = revision_service.complete_revision(db, current_user, revision_id)
        return res
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

