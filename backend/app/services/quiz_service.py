from typing import Dict, Any, List
from datetime import datetime, date, timedelta, timezone
from sqlalchemy.orm import Session
from app.models.all_models import (
    User, Subject, Topic, QuizAttempt, QuizQuestion, RevisionSchedule
)
from app.services.ai_service import ai_service
from app.services.revision_service import revision_service

class QuizService:
    def create_quiz(
        self,
        db: Session,
        user: User,
        subject_id: int,
        topic_id: int,
        difficulty: str = "Medium",
        num_questions: int = 5
    ) -> Dict[str, Any]:
        subject = db.query(Subject).filter(Subject.id == subject_id, Subject.user_id == user.id).first()
        topic = db.query(Topic).filter(Topic.id == topic_id, Topic.subject_id == subject_id).first()

        if not subject or not topic:
            raise ValueError("Subject or Topic not found for current user")

        # Call AI or fallback to generate questions
        raw_questions = ai_service.generate_quiz(
            subject_name=subject.name,
            topic_name=topic.name,
            topic_description=topic.description or "",
            difficulty=difficulty,
            num_questions=num_questions
        )

        # Create QuizAttempt
        attempt = QuizAttempt(
            user_id=user.id,
            subject_id=subject.id,
            topic_id=topic.id,
            total_questions=len(raw_questions),
            correct_answers=0,
            score_percentage=0.0,
            difficulty=difficulty
        )
        db.add(attempt)
        db.commit()
        db.refresh(attempt)

        created_questions = []
        for q in raw_questions:
            qq = QuizQuestion(
                quiz_attempt_id=attempt.id,
                question_text=q.get("question_text", "Conceptual Question"),
                option_a=q.get("option_a", "Option A"),
                option_b=q.get("option_b", "Option B"),
                option_c=q.get("option_c", "Option C"),
                option_d=q.get("option_d", "Option D"),
                correct_option=q.get("correct_option", "A").upper().strip(),
                explanation=q.get("explanation", "Standard conceptual rationale.")
            )
            db.add(qq)
            created_questions.append(qq)

        db.commit()

        return {
            "attempt_id": attempt.id,
            "subject_id": subject.id,
            "topic_id": topic.id,
            "subject_name": subject.name,
            "topic_name": topic.name,
            "difficulty": difficulty,
            "total_questions": len(created_questions),
            "questions": [
                {
                    "id": q.id,
                    "question_text": q.question_text,
                    "option_a": q.option_a,
                    "option_b": q.option_b,
                    "option_c": q.option_c,
                    "option_d": q.option_d
                }
                for q in created_questions
            ]
        }

    def evaluate_quiz(
        self,
        db: Session,
        user: User,
        attempt_id: int,
        answers: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        attempt = db.query(QuizAttempt).filter(
            QuizAttempt.id == attempt_id,
            QuizAttempt.user_id == user.id
        ).first()

        if not attempt:
            raise ValueError("Quiz attempt not found")

        questions = db.query(QuizQuestion).filter(QuizQuestion.quiz_attempt_id == attempt.id).all()
        ans_map = {ans.get("question_id"): (ans.get("selected_option") or "").strip().upper() for ans in answers}

        correct_count = 0
        results = []

        for question in questions:
            selected = ans_map.get(question.id, "")
            question.selected_option = selected if selected else None
            is_correct = bool(selected and selected == question.correct_option)
            question.is_correct = is_correct
            if is_correct:
                correct_count += 1

            results.append({
                "id": question.id,
                "question_text": question.question_text,
                "option_a": question.option_a,
                "option_b": question.option_b,
                "option_c": question.option_c,
                "option_d": question.option_d,
                "correct_option": question.correct_option,
                "selected_option": question.selected_option or "Unanswered",
                "explanation": question.explanation,
                "is_correct": is_correct
            })

        total = len(questions) or 1
        score_pct = round((correct_count / total) * 100, 1)

        attempt.correct_answers = correct_count
        attempt.score_percentage = score_pct

        # Adaptive learning feedback loop:
        # If score is under 70%, flag topic for revision
        topic = db.query(Topic).filter(Topic.id == attempt.topic_id).first()
        if topic:
            if score_pct < 70.0:
                topic.revision_required = True
                # Trigger an immediate revision schedule entry 1 day out
                revision_service.schedule_revision(db, user.id, topic.subject_id, topic.id, step=1, offset_days=1)
            else:
                # If good score, schedule standard spaced revision if not already scheduled
                revision_service.schedule_revision(db, user.id, topic.subject_id, topic.id, step=2, offset_days=3)

        db.commit()

        return {
            "id": attempt.id,
            "subject_id": attempt.subject_id,
            "topic_id": attempt.topic_id,
            "subject_name": attempt.subject.name if attempt.subject else "",
            "topic_name": attempt.topic.name if attempt.topic else "",
            "total_questions": total,
            "correct_answers": correct_count,
            "score_percentage": score_pct,
            "difficulty": attempt.difficulty,
            "created_at": attempt.created_at,
            "questions": results
        }

quiz_service = QuizService()

