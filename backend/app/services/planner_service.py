from datetime import datetime, date, timedelta
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from app.models.all_models import (
    User, StudentPreferences, Subject, Topic, Examination, StudySession,
    DifficultyLevel, PriorityLevel, SessionStatus, SessionType, TopicStatus
)
from app.services.ai_service import ai_service
import logging

logger = logging.getLogger(__name__)

class PlannerService:
    def _parse_time_minutes(self, time_str: str) -> int:
        """Converts HH:MM string to minutes from midnight."""
        try:
            parts = time_str.split(":")
            h = int(parts[0])
            m = int(parts[1])
            return max(0, min(24 * 60 - 1, h * 60 + m))
        except Exception:
            return 9 * 60  # default 09:00

    def _format_minutes_time(self, minutes: int) -> str:
        """Converts minutes from midnight to HH:MM string."""
        h = (minutes // 60) % 24
        m = minutes % 60
        return f"{h:02d}:{m:02d}"

    def calculate_topic_urgency(self, topic: Topic, exams: List[Examination], ref_date: date) -> float:
        """
        Computes a deterministic priority score for a topic:
        - Topic difficulty (Hard=25, Medium=15, Easy=5)
        - Revision required boost (+30)
        - In-progress continuation boost (+10)
        - Upcoming Examination urgency (excludes past exams!)
        - Subject priority (Urgent/High=20, Medium=10, Low=5)
        - Remaining workload factor
        """
        score = 0.0

        # 1. Topic difficulty weight
        diff = (topic.difficulty or "Medium").capitalize()
        if diff == "Hard":
            score += 25.0
        elif diff == "Medium":
            score += 15.0
        else:
            score += 5.0

        # 2. Revision requirement
        if topic.revision_required:
            score += 30.0

        # 3. Continuation of active work
        if topic.status == TopicStatus.IN_PROGRESS.value:
            score += 10.0

        # 4. Associated upcoming exams (strictly upcoming: delta >= 0)
        subject_exams = [e for e in exams if e.subject_id == topic.subject_id]
        min_days = 9999
        for exam in subject_exams:
            exam_d = exam.exam_date.date() if isinstance(exam.exam_date, datetime) else exam.exam_date
            delta = (exam_d - ref_date).days
            if delta >= 0 and delta < min_days:
                min_days = delta

        if min_days <= 3:
            score += 60.0
        elif min_days <= 7:
            score += 40.0
        elif min_days <= 14:
            score += 25.0
        elif min_days <= 30:
            score += 15.0

        # 5. Subject priority
        subj_prio = (topic.subject.priority or "Medium").capitalize() if topic.subject else "Medium"
        if subj_prio in ["High", "Urgent"]:
            score += 20.0
        elif subj_prio == "Medium":
            score += 10.0
        else:
            score += 5.0

        # 6. Unfinished ratio weight (topics with higher remaining work need more attention)
        est = topic.estimated_time_minutes or 60
        pct = topic.completion_percentage or 0
        rem_ratio = max(0.1, 1.0 - (pct / 100.0))
        score += rem_ratio * 15.0

        return score

    def _find_available_slots(
        self,
        start_min: int,
        end_min: int,
        break_min: int,
        existing_intervals: List[tuple]
    ) -> List[tuple]:
        """
        Finds free time slots [slot_start, slot_end] in minutes between start_min and end_min,
        accounting for existing busy intervals and required breaks.
        """
        # Sort existing intervals
        sorted_busy = sorted(existing_intervals, key=lambda x: x[0])
        free_slots = []
        cursor = start_min

        for b_start, b_end in sorted_busy:
            # If there is enough gap before this busy interval for at least a 30-min session
            if b_start - cursor >= 30:
                slot_end = min(end_min, b_start)
                if slot_end - cursor >= 30:
                    free_slots.append((cursor, slot_end))
            # Move cursor past this busy interval plus a break
            cursor = max(cursor, b_end + break_min)

        if end_min - cursor >= 30:
            free_slots.append((cursor, end_min))

        return free_slots

    def generate_plan(
        self,
        db: Session,
        user: User,
        plan_type: str = "weekly",  # "daily" or "weekly"
        target_date_str: Optional[str] = None,
        focus_subject_ids: Optional[List[int]] = None,
        priority_topic_ids: Optional[List[int]] = None,
        regenerate: bool = False
    ) -> Dict[str, Any]:
        """
        Generates a non-overlapping, workload-balanced study schedule.
        Guarantees database safety: generates and validates replacement in memory
        before removing any previous schedule records.
        """
        # 1. Load preferences and normalize
        prefs = db.query(StudentPreferences).filter(StudentPreferences.user_id == user.id).first()
        if not prefs:
            prefs = StudentPreferences(user_id=user.id)
            db.add(prefs)
            db.commit()
            db.refresh(prefs)

        daily_limit_minutes = max(30, int(prefs.daily_study_hours * 60))
        start_min = self._parse_time_minutes(prefs.preferred_start_time)
        end_min = self._parse_time_minutes(prefs.preferred_end_time)
        break_min = max(5, prefs.break_duration)

        # Validate time window; if inverted or too narrow, expand safely
        if start_min >= end_min or (end_min - start_min) < 60:
            start_min = 9 * 60
            end_min = min(24 * 60 - 1, start_min + daily_limit_minutes + 120)

        # Allowed study days
        raw_days = (prefs.preferred_study_days or "").split(",")
        allowed_days = [d.strip().capitalize() for d in raw_days if d.strip()]
        if not allowed_days:
            allowed_days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

        # 2. Determine exact date range
        today = date.today()
        if target_date_str:
            try:
                start_date = datetime.strptime(target_date_str, "%Y-%m-%d").date()
            except ValueError:
                start_date = today
        else:
            start_date = today

        num_days = 1 if plan_type == "daily" else 7
        end_date = start_date + timedelta(days=num_days - 1)

        # 3. Fetch candidate topics and filter out 100% completed topics (unless revision is due)
        query = db.query(Topic).join(Subject).filter(Subject.user_id == user.id)
        if focus_subject_ids:
            query = query.filter(Subject.id.in_(focus_subject_ids))
        all_topics = query.all()

        # Eligible topics: uncompleted OR explicitly requiring revision
        candidate_topics = [
            t for t in all_topics
            if t.status != TopicStatus.COMPLETED.value or t.revision_required
        ]

        # Upcoming exams strictly on or after start_date
        all_exams = db.query(Examination).filter(Examination.user_id == user.id).all()
        upcoming_exams = []
        for e in all_exams:
            ed = e.exam_date.date() if isinstance(e.exam_date, datetime) else e.exam_date
            if ed >= start_date:
                upcoming_exams.append(e)

        # Handle empty topics state
        if not candidate_topics:
            return {
                "plan_type": plan_type,
                "start_date": start_date.strftime("%Y-%m-%d"),
                "end_date": end_date.strftime("%Y-%m-%d"),
                "total_sessions": 0,
                "total_study_minutes": 0,
                "sessions": [],
                "ai_summary": "All topics are currently completed! Add new topics or subjects in the Subjects tab to generate your next study timetable.",
                "strategy_notes": ["Maintain your mastery through spaced revision quizzes in the Quiz Hub."]
            }

        # 4. Calculate remaining workload and urgency for each candidate topic
        topic_workload: Dict[int, int] = {}
        scored_topics = []

        for t in candidate_topics:
            # Calculate remaining minutes based on completion percentage and time spent
            pct = t.completion_percentage or 0
            est_mins = t.estimated_time_minutes or 60
            spent_mins = t.actual_time_spent_minutes or 0

            if t.revision_required:
                # Revisions are concise, high-focus sessions (30-45 mins)
                rem_mins = 45
            else:
                pct_rem = max(0.1, 1.0 - (pct / 100.0))
                calc_rem = int(est_mins * pct_rem)
                rem_mins = max(30, min(est_mins, calc_rem))

            topic_workload[t.id] = rem_mins
            urgency = self.calculate_topic_urgency(t, upcoming_exams, start_date)

            # Extra urgency boost if specifically designated as priority (e.g. from adaptive rescheduling)
            if priority_topic_ids and t.id in priority_topic_ids:
                urgency += 40.0

            scored_topics.append({
                "topic": t,
                "urgency": urgency,
                "subject_id": t.subject_id
            })

        # Sort topics by urgency descending
        scored_topics.sort(key=lambda x: x["urgency"], reverse=True)

        # Organize topics into subject buckets to interleave fairly
        topics_by_subject: Dict[int, List[Topic]] = {}
        for item in scored_topics:
            sid = item["subject_id"]
            topics_by_subject.setdefault(sid, []).append(item["topic"])

        subject_ids_ordered = list(topics_by_subject.keys())

        # 5. Build candidate timetable in-memory with non-overlapping slot allocation
        candidate_sessions: List[StudySession] = []
        topic_scheduled_count: Dict[int, int] = {t.id: 0 for t in candidate_topics}
        subject_turn_idx = 0

        for day_offset in range(num_days):
            current_date = start_date + timedelta(days=day_offset)
            weekday_name = current_date.strftime("%A")

            # Check if student studies on this weekday
            if weekday_name not in allowed_days:
                continue

            date_str = current_date.strftime("%Y-%m-%d")

            # Query existing sessions on this date
            existing_query = db.query(StudySession).filter(
                StudySession.user_id == user.id,
                StudySession.session_date == date_str
            )
            # If regenerate is true, we will replace only PENDING sessions
            if regenerate:
                existing_query = existing_query.filter(StudySession.status != SessionStatus.PENDING.value)
            
            existing_sessions = existing_query.all()
            existing_intervals = [
                (self._parse_time_minutes(s.start_time), self._parse_time_minutes(s.end_time))
                for s in existing_sessions
            ]
            already_spent_minutes = sum(s.duration_minutes for s in existing_sessions)
            remaining_day_budget = max(0, daily_limit_minutes - already_spent_minutes)

            if remaining_day_budget < 30:
                continue

            # Find non-overlapping free slots within preferred hours
            free_slots = self._find_available_slots(start_min, end_min, break_min, existing_intervals)
            scheduled_today = 0

            for slot_start, slot_end in free_slots:
                cursor = slot_start

                while cursor + 30 <= slot_end and (scheduled_today + 30) <= remaining_day_budget:
                    # Pick topic fairly by interleaving subjects
                    selected_topic = None
                    attempts = 0
                    num_subjs = len(subject_ids_ordered)

                    while attempts < num_subjs and not selected_topic:
                        target_sid = subject_ids_ordered[subject_turn_idx % num_subjs]
                        subject_turn_idx += 1
                        attempts += 1

                        # Find a topic under target_sid that still has remaining workload
                        for cand in topics_by_subject[target_sid]:
                            if topic_workload[cand.id] > 0:
                                selected_topic = cand
                                break

                    # If all topics have completed their remaining quota, pick the highest urgency topic with lowest scheduled count
                    if not selected_topic:
                        candidates_sorted = sorted(
                            candidate_topics,
                            key=lambda t: (topic_scheduled_count[t.id], -self.calculate_topic_urgency(t, upcoming_exams, current_date))
                        )
                        selected_topic = candidates_sorted[0]

                    # Determine session duration (between 30 and 60 minutes)
                    slot_rem = slot_end - cursor
                    daily_rem = remaining_day_budget - scheduled_today
                    need_rem = max(30, topic_workload[selected_topic.id])

                    session_len = min(60, need_rem, slot_rem, daily_rem)
                    if session_len < 30:
                        break

                    sess_start_str = self._format_minutes_time(cursor)
                    sess_end_str = self._format_minutes_time(cursor + session_len)

                    # Determine session type
                    if selected_topic.revision_required:
                        sess_type = SessionType.REVISION.value
                    elif (selected_topic.actual_time_spent_minutes or 0) > 0 or (selected_topic.completion_percentage or 0) > 40:
                        sess_type = SessionType.PRACTICE.value
                    else:
                        sess_type = SessionType.LEARNING.value

                    new_sess = StudySession(
                        user_id=user.id,
                        subject_id=selected_topic.subject_id,
                        topic_id=selected_topic.id,
                        session_date=date_str,
                        start_time=sess_start_str,
                        end_time=sess_end_str,
                        duration_minutes=session_len,
                        priority=selected_topic.subject.priority if selected_topic.subject else PriorityLevel.MEDIUM.value,
                        session_type=sess_type,
                        status=SessionStatus.PENDING.value,
                        plan_type=plan_type,
                        ai_recommendation="",
                        notes=f"Scheduled for {selected_topic.name}"
                    )

                    candidate_sessions.append(new_sess)
                    scheduled_today += session_len
                    topic_workload[selected_topic.id] = max(0, topic_workload[selected_topic.id] - session_len)
                    topic_scheduled_count[selected_topic.id] += 1

                    cursor += session_len + break_min

        # 6. Validate generated schedule strictly before modifying the database
        by_date_sessions: Dict[str, List[StudySession]] = {}
        for s in candidate_sessions:
            by_date_sessions.setdefault(s.session_date, []).append(s)

        for d_str, day_sess in by_date_sessions.items():
            # Check overlap among generated sessions
            day_sess.sort(key=lambda x: self._parse_time_minutes(x.start_time))
            for i in range(len(day_sess) - 1):
                cur_end = self._parse_time_minutes(day_sess[i].end_time)
                nxt_start = self._parse_time_minutes(day_sess[i + 1].start_time)
                if cur_end > nxt_start:
                    logger.error(f"Validation failure: Overlap detected on {d_str} between {day_sess[i]} and {day_sess[i+1]}")
                    raise ValueError(f"Schedule overlap detected on {d_str}")

            # Check daily duration limit
            total_day = sum(s.duration_minutes for s in day_sess)
            if total_day > daily_limit_minutes:
                logger.error(f"Validation failure: Day {d_str} total {total_day} exceeds limit {daily_limit_minutes}")
                raise ValueError(f"Daily study hour limit exceeded on {d_str}")

        # 7. Database Transaction: Atomic replacement of pending sessions
        try:
            if regenerate:
                db.query(StudySession).filter(
                    StudySession.user_id == user.id,
                    StudySession.session_date >= start_date.strftime("%Y-%m-%d"),
                    StudySession.session_date <= end_date.strftime("%Y-%m-%d"),
                    StudySession.status == SessionStatus.PENDING.value
                ).delete()

            for s in candidate_sessions:
                db.add(s)

            db.commit()

            # Refresh objects to get generated IDs and relationships
            for s in candidate_sessions:
                db.refresh(s)

        except Exception as e:
            db.rollback()
            logger.error(f"Failed to persist generated plan: {e}")
            raise e

        # 8. Enrich with AI personalization (strategic overview & per-session tips)
        exam_dicts = [
            {
                "title": e.title,
                "subject_name": e.subject.name if e.subject else "",
                "days_remaining": max(0, ((e.exam_date.date() if isinstance(e.exam_date, datetime) else e.exam_date) - start_date).days)
            }
            for e in upcoming_exams
        ]

        student_profile_dict = {
            "daily_study_hours": prefs.daily_study_hours,
            "break_duration": prefs.break_duration,
            "learning_style": prefs.preferred_learning_style,
            "goals": prefs.academic_goals
        }

        draft_list = [
            {
                "session_date": s.session_date,
                "start_time": s.start_time,
                "duration_minutes": s.duration_minutes,
                "subject_name": s.subject.name if s.subject else "",
                "topic_name": s.topic.name if s.topic else "",
                "session_type": s.session_type
            }
            for s in candidate_sessions
        ]

        ai_enhancement = ai_service.personalize_study_plan(student_profile_dict, draft_list, exam_dicts)

        # Apply recommendations
        recommendations = ai_enhancement.get("session_recommendations", [])
        for rec in recommendations:
            idx = rec.get("session_index")
            if idx is not None and 0 <= idx < len(candidate_sessions):
                candidate_sessions[idx].ai_recommendation = rec.get("recommendation", "")

        try:
            db.commit()
        except Exception:
            db.rollback()

        return {
            "plan_type": plan_type,
            "start_date": start_date.strftime("%Y-%m-%d"),
            "end_date": end_date.strftime("%Y-%m-%d"),
            "total_sessions": len(candidate_sessions),
            "total_study_minutes": sum(s.duration_minutes for s in candidate_sessions),
            "sessions": [
                {
                    "id": s.id,
                    "user_id": s.user_id,
                    "subject_id": s.subject_id,
                    "topic_id": s.topic_id,
                    "subject_name": s.subject.name if s.subject else "",
                    "subject_color": s.subject.color if s.subject else "#4F46E5",
                    "topic_name": s.topic.name if s.topic else "",
                    "session_date": s.session_date,
                    "start_time": s.start_time,
                    "end_time": s.end_time,
                    "duration_minutes": s.duration_minutes,
                    "priority": s.priority,
                    "session_type": s.session_type,
                    "status": s.status,
                    "ai_recommendation": s.ai_recommendation,
                    "notes": s.notes,
                    "plan_type": s.plan_type,
                    "created_at": s.created_at
                }
                for s in candidate_sessions
            ],
            "ai_summary": ai_enhancement.get("ai_summary", "Plan successfully generated."),
            "strategy_notes": ai_enhancement.get("strategy_notes", [])
        }

planner_service = PlannerService()
