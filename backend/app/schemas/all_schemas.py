from pydantic import BaseModel, EmailStr, Field, ConfigDict
from typing import List, Optional, Any
from datetime import datetime

# --- AUTH SCHEMAS ---
class UserRegister(BaseModel):
    full_name: str = Field(..., min_length=2, max_length=100)
    email: EmailStr
    password: str = Field(..., min_length=6, max_length=100)
    confirm_password: str = Field(..., min_length=6, max_length=100)

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    full_name: str
    email: str
    created_at: datetime

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse

class TokenPayload(BaseModel):
    sub: Optional[str] = None


# --- PREFERENCES / PROFILE SCHEMAS ---
class PreferencesBase(BaseModel):
    daily_study_hours: float = Field(default=4.0, ge=0.5, le=18.0)
    preferred_start_time: str = Field(default="09:00", pattern=r"^\d{2}:\d{2}$")
    preferred_end_time: str = Field(default="21:00", pattern=r"^\d{2}:\d{2}$")
    preferred_study_days: str = Field(default="Monday,Tuesday,Wednesday,Thursday,Friday,Saturday,Sunday")
    break_duration: int = Field(default=15, ge=5, le=60)
    academic_goals: str = Field(default="Master key concepts and excel in examinations")
    preferred_learning_style: str = Field(default="Visual")

class PreferencesUpdate(PreferencesBase):
    full_name: Optional[str] = None

class PreferencesResponse(PreferencesBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    user_id: int
    full_name: Optional[str] = None
    email: Optional[str] = None


# --- TOPIC SCHEMAS ---
class TopicBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = ""
    difficulty: str = Field(default="Medium")  # Easy, Medium, Hard
    estimated_time_minutes: int = Field(default=60, ge=10, le=600)
    revision_required: bool = False

class TopicCreate(TopicBase):
    subject_id: int

class TopicUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    difficulty: Optional[str] = None
    estimated_time_minutes: Optional[int] = None
    actual_time_spent_minutes: Optional[int] = None
    completion_percentage: Optional[int] = Field(None, ge=0, le=100)
    status: Optional[str] = None
    revision_required: Optional[bool] = None

class TopicResponse(TopicBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    subject_id: int
    actual_time_spent_minutes: int
    completion_percentage: int
    status: str
    last_studied_date: Optional[datetime] = None
    created_at: datetime


# --- SUBJECT SCHEMAS ---
class SubjectBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = ""
    color: str = Field(default="#4F46E5")
    difficulty: str = Field(default="Medium")
    priority: str = Field(default="Medium")

class SubjectCreate(SubjectBase):
    pass

class SubjectUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    color: Optional[str] = None
    difficulty: Optional[str] = None
    priority: Optional[str] = None

class SubjectResponse(SubjectBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    user_id: int
    topics_count: Optional[int] = 0
    completed_topics_count: Optional[int] = 0
    progress_percentage: Optional[int] = 0
    created_at: datetime

class SubjectDetailResponse(SubjectResponse):
    topics: List[TopicResponse] = []


# --- EXAMINATION SCHEMAS ---
class ExaminationBase(BaseModel):
    subject_id: int
    title: str = Field(..., min_length=1, max_length=255)
    exam_date: datetime
    priority: str = Field(default="High")
    notes: Optional[str] = ""

class ExaminationCreate(ExaminationBase):
    pass

class ExaminationUpdate(BaseModel):
    subject_id: Optional[int] = None
    title: Optional[str] = None
    exam_date: Optional[datetime] = None
    priority: Optional[str] = None
    notes: Optional[str] = None

class ExaminationResponse(ExaminationBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    user_id: int
    subject_name: Optional[str] = ""
    subject_color: Optional[str] = ""
    days_remaining: int
    is_urgent: bool
    created_at: datetime


# --- STUDY SESSION & PLAN SCHEMAS ---
class StudySessionBase(BaseModel):
    session_date: str
    start_time: str
    end_time: str
    duration_minutes: int
    priority: str = "Medium"
    session_type: str = "Learning"
    status: str = "Pending"
    ai_recommendation: Optional[str] = ""
    notes: Optional[str] = ""
    plan_type: str = "daily"

class StudySessionResponse(StudySessionBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    user_id: int
    subject_id: Optional[int] = None
    topic_id: Optional[int] = None
    subject_name: Optional[str] = None
    subject_color: Optional[str] = None
    topic_name: Optional[str] = None
    created_at: datetime

class SessionStatusUpdate(BaseModel):
    status: str  # Pending, Completed, Partially Completed, Not Completed, Skipped
    actual_minutes: Optional[int] = None
    notes: Optional[str] = None

class PlanGenerateRequest(BaseModel):
    plan_type: str = Field(default="weekly")  # daily or weekly
    target_date: Optional[str] = None         # YYYY-MM-DD
    focus_subject_ids: Optional[List[int]] = None
    regenerate: bool = False

class PlanAdjustRequest(BaseModel):
    reason: Optional[str] = "Adjustment based on latest session progress"

class PlanResponse(BaseModel):
    plan_type: str
    start_date: str
    end_date: str
    total_sessions: int
    total_study_minutes: int
    sessions: List[StudySessionResponse]
    ai_summary: Optional[str] = None
    strategy_notes: Optional[List[str]] = []


# --- PROGRESS SCHEMAS ---
class ProgressOverview(BaseModel):
    total_study_hours: float
    weekly_study_hours: float
    daily_study_hours: float
    total_topics: int
    completed_topics: int
    pending_topics: int
    overall_completion_rate: float
    current_streak_days: int
    planned_vs_actual_hours: dict
    weekly_hours_by_day: List[dict]
    subject_progress: List[dict]
    productivity_trend: List[dict]
    task_status_distribution: List[dict]


# --- AI CHAT SCHEMAS ---
class ChatMessageCreate(BaseModel):
    content: str
    conversation_id: Optional[int] = None

class ChatMessageResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    sender: str
    content: str
    created_at: datetime

class ChatConversationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    title: str
    created_at: datetime
    messages: List[ChatMessageResponse] = []


# --- AI QUIZ SCHEMAS ---
class QuizGenerateRequest(BaseModel):
    subject_id: int
    topic_id: int
    difficulty: str = "Medium"
    num_questions: int = Field(default=5, ge=3, le=10)

class QuizQuestionSchema(BaseModel):
    id: Optional[int] = None
    question_text: str
    option_a: str
    option_b: str
    option_c: str
    option_d: str
    correct_option: Optional[str] = None
    explanation: Optional[str] = None

class QuizSubmitAnswer(BaseModel):
    question_id: int
    selected_option: str  # A, B, C, D

class QuizSubmitRequest(BaseModel):
    attempt_id: int
    answers: List[QuizSubmitAnswer]

class QuizQuestionResult(BaseModel):
    id: int
    question_text: str
    option_a: str
    option_b: str
    option_c: str
    option_d: str
    correct_option: str
    selected_option: str
    explanation: str
    is_correct: bool

class QuizAttemptResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    subject_id: int
    topic_id: int
    subject_name: Optional[str] = None
    topic_name: Optional[str] = None
    total_questions: int
    correct_answers: int
    score_percentage: float
    difficulty: str
    created_at: datetime
    questions: List[QuizQuestionResult] = []


# --- REVISION SCHEMAS ---
class RevisionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    topic_id: int
    subject_id: int
    topic_name: Optional[str] = None
    subject_name: Optional[str] = None
    subject_color: Optional[str] = None
    revision_step: int
    scheduled_date: str
    status: str
    completed_at: Optional[datetime] = None
    is_overdue: bool

class RevisionCompleteRequest(BaseModel):
    notes: Optional[str] = None


# --- NOTIFICATION SCHEMAS ---
class NotificationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    title: str
    message: str
    type: str
    is_read: bool
    created_at: datetime
