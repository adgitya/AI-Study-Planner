import enum
from datetime import datetime, timezone
from sqlalchemy import (
    Column, Integer, String, Float, Boolean, DateTime, ForeignKey, Text, Enum as SQLEnum
)
from sqlalchemy.orm import relationship
from app.core.database import Base

def utc_now():
    return datetime.now(timezone.utc)

class DifficultyLevel(str, enum.Enum):
    EASY = "Easy"
    MEDIUM = "Medium"
    HARD = "Hard"

class PriorityLevel(str, enum.Enum):
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"
    URGENT = "Urgent"

class SessionStatus(str, enum.Enum):
    PENDING = "Pending"
    COMPLETED = "Completed"
    PARTIALLY_COMPLETED = "Partially Completed"
    NOT_COMPLETED = "Not Completed"
    SKIPPED = "Skipped"

class SessionType(str, enum.Enum):
    LEARNING = "Learning"
    PRACTICE = "Practice"
    REVISION = "Revision"
    MOCK_TEST = "Mock Test"
    BREAK = "Break"

class TopicStatus(str, enum.Enum):
    PENDING = "Pending"
    IN_PROGRESS = "In Progress"
    COMPLETED = "Completed"

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    full_name = Column(String(255), nullable=False)
    hashed_password = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=utc_now)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now)

    # Relationships
    preferences = relationship("StudentPreferences", back_populates="user", uselist=False, cascade="all, delete-orphan")
    subjects = relationship("Subject", back_populates="user", cascade="all, delete-orphan")
    examinations = relationship("Examination", back_populates="user", cascade="all, delete-orphan")
    study_sessions = relationship("StudySession", back_populates="user", cascade="all, delete-orphan")
    progress_records = relationship("ProgressRecord", back_populates="user", cascade="all, delete-orphan")
    quiz_attempts = relationship("QuizAttempt", back_populates="user", cascade="all, delete-orphan")
    revision_schedules = relationship("RevisionSchedule", back_populates="user", cascade="all, delete-orphan")
    chat_conversations = relationship("ChatConversation", back_populates="user", cascade="all, delete-orphan")
    notifications = relationship("Notification", back_populates="user", cascade="all, delete-orphan")


class StudentPreferences(Base):
    __tablename__ = "student_preferences"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    daily_study_hours = Column(Float, default=4.0)
    preferred_start_time = Column(String(10), default="09:00")
    preferred_end_time = Column(String(10), default="21:00")
    preferred_study_days = Column(String(100), default="Monday,Tuesday,Wednesday,Thursday,Friday,Saturday,Sunday")
    break_duration = Column(Integer, default=15)  # minutes
    academic_goals = Column(Text, default="Prepare thoroughly for semester exams and master core concepts")
    preferred_learning_style = Column(String(50), default="Visual")  # Visual, Auditory, Read/Write, Kinesthetic

    user = relationship("User", back_populates="preferences")


class Subject(Base):
    __tablename__ = "subjects"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, default="")
    color = Column(String(50), default="#4F46E5")  # Indigo default
    difficulty = Column(String(20), default=DifficultyLevel.MEDIUM.value)
    priority = Column(String(20), default=PriorityLevel.MEDIUM.value)
    created_at = Column(DateTime, default=utc_now)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now)

    user = relationship("User", back_populates="subjects")
    topics = relationship("Topic", back_populates="subject", cascade="all, delete-orphan")
    examinations = relationship("Examination", back_populates="subject", cascade="all, delete-orphan")
    study_sessions = relationship("StudySession", back_populates="subject", cascade="all, delete-orphan")


class Topic(Base):
    __tablename__ = "topics"

    id = Column(Integer, primary_key=True, index=True)
    subject_id = Column(Integer, ForeignKey("subjects.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, default="")
    difficulty = Column(String(20), default=DifficultyLevel.MEDIUM.value)
    estimated_time_minutes = Column(Integer, default=60)
    actual_time_spent_minutes = Column(Integer, default=0)
    completion_percentage = Column(Integer, default=0)
    status = Column(String(20), default=TopicStatus.PENDING.value)
    last_studied_date = Column(DateTime, nullable=True)
    revision_required = Column(Boolean, default=False)
    created_at = Column(DateTime, default=utc_now)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now)

    subject = relationship("Subject", back_populates="topics")
    study_sessions = relationship("StudySession", back_populates="topic", cascade="all, delete-orphan")
    revision_schedules = relationship("RevisionSchedule", back_populates="topic", cascade="all, delete-orphan")
    quiz_attempts = relationship("QuizAttempt", back_populates="topic", cascade="all, delete-orphan")


class Examination(Base):
    __tablename__ = "examinations"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    subject_id = Column(Integer, ForeignKey("subjects.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    exam_date = Column(DateTime, nullable=False)
    priority = Column(String(20), default=PriorityLevel.HIGH.value)
    notes = Column(Text, default="")
    created_at = Column(DateTime, default=utc_now)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now)

    user = relationship("User", back_populates="examinations")
    subject = relationship("Subject", back_populates="examinations")


class StudySession(Base):
    __tablename__ = "study_sessions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    subject_id = Column(Integer, ForeignKey("subjects.id", ondelete="SET NULL"), nullable=True)
    topic_id = Column(Integer, ForeignKey("topics.id", ondelete="SET NULL"), nullable=True)
    session_date = Column(String(10), nullable=False, index=True)  # YYYY-MM-DD
    start_time = Column(String(10), nullable=False)               # HH:MM (24h)
    end_time = Column(String(10), nullable=False)                 # HH:MM (24h)
    duration_minutes = Column(Integer, default=60)
    priority = Column(String(20), default=PriorityLevel.MEDIUM.value)
    session_type = Column(String(30), default=SessionType.LEARNING.value)
    status = Column(String(30), default=SessionStatus.PENDING.value)
    ai_recommendation = Column(Text, default="")
    notes = Column(Text, default="")
    plan_type = Column(String(20), default="daily")  # daily or weekly
    created_at = Column(DateTime, default=utc_now)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now)

    user = relationship("User", back_populates="study_sessions")
    subject = relationship("Subject", back_populates="study_sessions")
    topic = relationship("Topic", back_populates="study_sessions")
    progress_records = relationship("ProgressRecord", back_populates="session", cascade="all, delete-orphan")


class ProgressRecord(Base):
    __tablename__ = "progress_records"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    session_id = Column(Integer, ForeignKey("study_sessions.id", ondelete="CASCADE"), nullable=True)
    study_date = Column(String(10), nullable=False, index=True)  # YYYY-MM-DD
    duration_minutes = Column(Integer, default=0)
    status = Column(String(30), default=SessionStatus.COMPLETED.value)
    notes = Column(Text, default="")
    created_at = Column(DateTime, default=utc_now)

    user = relationship("User", back_populates="progress_records")
    session = relationship("StudySession", back_populates="progress_records")


class QuizAttempt(Base):
    __tablename__ = "quiz_attempts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    subject_id = Column(Integer, ForeignKey("subjects.id", ondelete="CASCADE"), nullable=False)
    topic_id = Column(Integer, ForeignKey("topics.id", ondelete="CASCADE"), nullable=False)
    total_questions = Column(Integer, default=5)
    correct_answers = Column(Integer, default=0)
    score_percentage = Column(Float, default=0.0)
    difficulty = Column(String(20), default=DifficultyLevel.MEDIUM.value)
    created_at = Column(DateTime, default=utc_now)

    user = relationship("User", back_populates="quiz_attempts")
    subject = relationship("Subject")
    topic = relationship("Topic", back_populates="quiz_attempts")
    questions = relationship("QuizQuestion", back_populates="attempt", cascade="all, delete-orphan")


class QuizQuestion(Base):
    __tablename__ = "quiz_questions"

    id = Column(Integer, primary_key=True, index=True)
    quiz_attempt_id = Column(Integer, ForeignKey("quiz_attempts.id", ondelete="CASCADE"), nullable=False, index=True)
    question_text = Column(Text, nullable=False)
    option_a = Column(String(500), nullable=False)
    option_b = Column(String(500), nullable=False)
    option_c = Column(String(500), nullable=False)
    option_d = Column(String(500), nullable=False)
    correct_option = Column(String(5), nullable=False)  # A, B, C, D
    selected_option = Column(String(5), default="")     # A, B, C, D
    explanation = Column(Text, default="")
    is_correct = Column(Boolean, default=False)

    attempt = relationship("QuizAttempt", back_populates="questions")


class RevisionSchedule(Base):
    __tablename__ = "revision_schedules"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    subject_id = Column(Integer, ForeignKey("subjects.id", ondelete="CASCADE"), nullable=False)
    topic_id = Column(Integer, ForeignKey("topics.id", ondelete="CASCADE"), nullable=False)
    revision_step = Column(Integer, default=1)  # 1 (1d), 2 (3d), 3 (7d), 4 (14d)
    scheduled_date = Column(String(10), nullable=False, index=True)  # YYYY-MM-DD
    status = Column(String(20), default="Pending")  # Pending, Completed, Rescheduled
    completed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=utc_now)

    user = relationship("User", back_populates="revision_schedules")
    subject = relationship("Subject")
    topic = relationship("Topic", back_populates="revision_schedules")


class ChatConversation(Base):
    __tablename__ = "chat_conversations"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String(255), default="Study Planning Assistance")
    created_at = Column(DateTime, default=utc_now)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now)

    user = relationship("User", back_populates="chat_conversations")
    messages = relationship("ChatMessage", back_populates="conversation", cascade="all, delete-orphan", order_by="ChatMessage.id")


class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(Integer, ForeignKey("chat_conversations.id", ondelete="CASCADE"), nullable=False, index=True)
    sender = Column(String(20), nullable=False)  # "user" or "assistant"
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=utc_now)

    conversation = relationship("ChatConversation", back_populates="messages")


class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    type = Column(String(50), default="session_reminder")  # session_reminder, exam_alert, revision_reminder, task_alert
    is_read = Column(Boolean, default=False)
    scheduled_for = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=utc_now)

    user = relationship("User", back_populates="notifications")

