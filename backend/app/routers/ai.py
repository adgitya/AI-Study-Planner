from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Dict, Any, Optional
from datetime import datetime, date
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.all_models import (
    User, Subject, Topic, Examination, StudySession,
    ChatConversation, ChatMessage, QuizAttempt, QuizQuestion,
    TopicStatus
)
from app.schemas.all_schemas import (
    ChatMessageCreate, ChatConversationResponse,
    QuizGenerateRequest, QuizSubmitRequest, QuizAttemptResponse
)
from app.services.ai_service import ai_service
from app.services.quiz_service import quiz_service

router = APIRouter(prefix="/ai", tags=["AI & Assistant"])

@router.post("/chat")
def chat_with_assistant(
    chat_in: ChatMessageCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # 1. Fetch or create conversation
    conv = None
    if chat_in.conversation_id:
        conv = db.query(ChatConversation).filter(
            ChatConversation.id == chat_in.conversation_id,
            ChatConversation.user_id == current_user.id
        ).first()

    if not conv:
        conv = ChatConversation(user_id=current_user.id, title=chat_in.content[:40] + "...")
        db.add(conv)
        db.commit()
        db.refresh(conv)

    # 2. Record student message
    user_msg = ChatMessage(conversation_id=conv.id, sender="user", content=chat_in.content)
    db.add(user_msg)
    db.commit()

    # 3. Assemble verified student context from database
    subjects = db.query(Subject).filter(Subject.user_id == current_user.id).all()
    exams = db.query(Examination).filter(Examination.user_id == current_user.id).all()
    pending_topics = db.query(Topic).join(Subject).filter(
        Subject.user_id == current_user.id,
        Topic.status != TopicStatus.COMPLETED.value
    ).all()

    today = date.today()
    exam_context = []
    for e in exams:
        ed = e.exam_date.date() if isinstance(e.exam_date, datetime) else e.exam_date
        exam_context.append({
            "title": e.title,
            "subject_name": e.subject.name if e.subject else "General",
            "days_remaining": (ed - today).days,
            "priority": e.priority
        })

    student_context = {
        "student_name": current_user.full_name,
        "daily_study_hours": current_user.preferences.daily_study_hours if current_user.preferences else 4.0,
        "learning_style": current_user.preferences.preferred_learning_style if current_user.preferences else "Visual",
        "academic_goals": current_user.preferences.academic_goals if current_user.preferences else "",
        "subjects": [s.name for s in subjects],
        "upcoming_exams": exam_context,
        "pending_topics": [t.name for t in pending_topics[:15]]
    }

    # 4. History
    history_records = db.query(ChatMessage).filter(ChatMessage.conversation_id == conv.id).order_by(ChatMessage.id.asc()).all()
    conv_history = [{"role": "assistant" if m.sender == "assistant" else "user", "content": m.content} for m in history_records[:-1]]

    # 5. Generate contextual response
    assistant_reply = ai_service.generate_chat_response(
        student_context=student_context,
        conversation_history=conv_history,
        user_message=chat_in.content
    )

    # 6. Record assistant message
    ai_msg = ChatMessage(conversation_id=conv.id, sender="assistant", content=assistant_reply)
    db.add(ai_msg)
    db.commit()
    db.refresh(ai_msg)

    return {
        "conversation_id": conv.id,
        "user_message": {
            "id": user_msg.id,
            "sender": user_msg.sender,
            "content": user_msg.content,
            "created_at": user_msg.created_at
        },
        "assistant_message": {
            "id": ai_msg.id,
            "sender": ai_msg.sender,
            "content": ai_msg.content,
            "created_at": ai_msg.created_at
        }
    }

@router.get("/conversations", response_model=List[ChatConversationResponse])
def get_conversations(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    convs = db.query(ChatConversation).filter(
        ChatConversation.user_id == current_user.id
    ).order_by(ChatConversation.id.desc()).all()
    return convs

@router.delete("/conversations/{conversation_id}", status_code=status.HTTP_204_NO_CONTENT)
def clear_conversation(
    conversation_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    conv = db.query(ChatConversation).filter(
        ChatConversation.id == conversation_id,
        ChatConversation.user_id == current_user.id
    ).first()
    if not conv:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found")
    db.delete(conv)
    db.commit()
    return None

@router.post("/generate-quiz")
def generate_quiz(
    req: QuizGenerateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        quiz_data = quiz_service.create_quiz(
            db=db,
            user=current_user,
            subject_id=req.subject_id,
            topic_id=req.topic_id,
            difficulty=req.difficulty,
            num_questions=req.num_questions
        )
        return quiz_data
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.post("/submit-quiz", response_model=QuizAttemptResponse)
def submit_quiz(
    req: QuizSubmitRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        answers_dict = [{"question_id": a.question_id, "selected_option": a.selected_option} for a in req.answers]
        result = quiz_service.evaluate_quiz(
            db=db,
            user=current_user,
            attempt_id=req.attempt_id,
            answers=answers_dict
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.get("/quiz-history", response_model=List[QuizAttemptResponse])
def get_quiz_history(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    attempts = db.query(QuizAttempt).filter(
        QuizAttempt.user_id == current_user.id
    ).order_by(QuizAttempt.id.desc()).all()

    results = []
    for a in attempts:
        q_results = [
            {
                "id": q.id,
                "question_text": q.question_text,
                "option_a": q.option_a,
                "option_b": q.option_b,
                "option_c": q.option_c,
                "option_d": q.option_d,
                "correct_option": q.correct_option,
                "selected_option": q.selected_option or "",
                "explanation": q.explanation or "",
                "is_correct": q.is_correct
            }
            for q in a.questions
        ]
        results.append(QuizAttemptResponse(
            id=a.id,
            subject_id=a.subject_id,
            topic_id=a.topic_id,
            subject_name=a.subject.name if a.subject else "",
            topic_name=a.topic.name if a.topic else "",
            total_questions=a.total_questions,
            correct_answers=a.correct_answers,
            score_percentage=a.score_percentage,
            difficulty=a.difficulty,
            created_at=a.created_at,
            questions=q_results
        ))
    return results

