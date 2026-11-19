import os
import json
import logging
from typing import Dict, Any, List, Optional
from app.core.config import settings

logger = logging.getLogger(__name__)

# Fallback recommendations if LLM is unavailable
FALLBACK_TIPS = [
    "Break this topic into 25-minute Pomodoro intervals for optimal focus.",
    "Practice active recall by closing your notes and writing down key concepts.",
    "Formulate 3 self-test questions before starting your deep study session.",
    "Use the Feynman technique: explain this topic simply as if teaching someone else.",
    "Review summary flashcards and solve at least 2 practice problems."
]

class AIService:
    def __init__(self):
        self.api_key = settings.OPENAI_API_KEY
        self.model = settings.OPENAI_MODEL
        self.client = None
        if self.api_key:
            try:
                from openai import OpenAI
                self.client = OpenAI(api_key=self.api_key)
            except Exception as e:
                logger.warning(f"Could not initialize OpenAI client: {e}")

    def is_available(self) -> bool:
        return bool(self.client and self.api_key)

    def _call_llm_json(self, system_prompt: str, user_prompt: str) -> Optional[Dict[str, Any]]:
        """Safely call LLM expecting JSON output with timeout and error fallback."""
        if not self.is_available():
            return None
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt + "\nAlways output valid strictly parseable JSON."},
                    {"role": "user", "content": user_prompt}
                ],
                response_format={"type": "json_object"},
                temperature=0.7,
                timeout=25.0
            )
            raw_content = response.choices[0].message.content
            return json.loads(raw_content)
        except Exception as e:
            logger.error(f"OpenAI API call error: {e}")
            return None

    def _call_llm_text(self, system_prompt: str, messages: List[Dict[str, str]]) -> Optional[str]:
        """Safely call LLM for conversational text output."""
        if not self.is_available():
            return None

        try:
            full_messages = [{"role": "system", "content": system_prompt}] + messages
            response = self.client.chat.completions.create(
                model=self.model,
                messages=full_messages,
                temperature=0.7,
                timeout=25.0
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"OpenAI Chat API error: {e}")
            return None

    def personalize_study_plan(
        self,
        student_profile: Dict[str, Any],
        draft_sessions: List[Dict[str, Any]],
        upcoming_exams: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Enhances draft schedule with actionable tips and strategic overview."""
        system_prompt = (
            "You are an expert academic advisor and cognitive learning scientist. "
            "Analyze the student's scheduled study sessions, upcoming exams, and learning preferences. "
            "Return a JSON object with: \n"
            "- 'ai_summary': A motivating 2-3 sentence overview of this schedule.\n"
            "- 'strategy_notes': An array of 3-4 specific academic study tips tailored to their goals and upcoming exams.\n"
            "- 'session_recommendations': An array of objects each having 'session_index' (integer matching input) and 'recommendation' (concise 1-sentence tactical tip)."
        )

        user_prompt = json.dumps({
            "student_profile": student_profile,
            "upcoming_exams": upcoming_exams,
            "draft_sessions": [
                {
                    "index": i,
                    "date": s.get("session_date"),
                    "start": s.get("start_time"),
                    "subject": s.get("subject_name"),
                    "topic": s.get("topic_name"),
                    "type": s.get("session_type"),
                    "duration_minutes": s.get("duration_minutes")
                }
                for i, s in enumerate(draft_sessions)
            ]
        }, indent=2)

        result = self._call_llm_json(system_prompt, user_prompt)
        if result and "ai_summary" in result:
            return result
        
        # Rule-based fallback if LLM is unavailable
        strategy_notes = [
            "Prioritize subjects with exams in the next 14 days during your peak focus hours.",
            "Use active recall and spaced revision for high-difficulty topics.",
            f"Adhere strictly to {student_profile.get('break_duration', 15)}-minute breaks to prevent cognitive fatigue.",
            "Complete practice questions immediately following theoretical learning."
        ]
        
        session_recs = []
        for i, s in enumerate(draft_sessions):
            stype = s.get("session_type", "Learning")
            tip = (
                "Work through practical problem sets and past paper questions."
                if stype == "Practice" else
                "Review flashcards, summary sheets, and test yourself on definitions."
                if stype == "Revision" else
                "Take notes in your own words and identify key underlying principles."
            )
            session_recs.append({"session_index": i, "recommendation": tip})

        return {
            "ai_summary": "Your study plan has been optimized based on exam deadlines, topic difficulties, and daily study limits.",
            "strategy_notes": strategy_notes,
            "session_recommendations": session_recs
        }

    def generate_chat_response(
        self,
        student_context: Dict[str, Any],
        conversation_history: List[Dict[str, str]],
        user_message: str
    ) -> str:
        """Context-aware AI Study Assistant response."""
        system_prompt = (
            "You are the AI Study Assistant for the 'AI Study Planner' platform. "
            "You provide empathetic, scientifically grounded academic guidance, exam strategy, and subject explanations.\n"
            "CRITICAL INSTRUCTIONS:\n"
            "1. You MUST use the provided student context (enrolled subjects, topics, progress, upcoming exams) accurately.\n"
            "2. Never fabricate nonexistent exams, subjects, or progress metrics.\n"
            "3. If the student asks about what to study today or how to prepare, refer directly to their exams and pending topics.\n"
            "4. Keep explanations clear, engaging, and structured with bullet points where appropriate.\n"
            f"STUDENT DATABASE CONTEXT:\n{json.dumps(student_context, indent=2)}"
        )

        messages = conversation_history[-6:] + [{"role": "user", "content": user_message}]
        llm_reply = self._call_llm_text(system_prompt, messages)
        if llm_reply:
            return llm_reply

        # High-utility deterministic fallback assistant
        return self._fallback_chat_reply(user_message, student_context)

    def _fallback_chat_reply(self, message: str, context: Dict[str, Any]) -> str:
        msg = message.lower()
        exams = context.get("upcoming_exams", [])
        subjects = context.get("subjects", [])
        pending_topics = context.get("pending_topics", [])

        if "exam" in msg or "prioritize" in msg or "prepare" in msg:
            if exams:
                nearest = sorted(exams, key=lambda x: x.get("days_remaining", 999))[0]
                return (
                    f"Based on your upcoming schedule, your most urgent examination is **{nearest.get('title')}** "
                    f"in **{nearest.get('days_remaining')} days**. I recommend prioritizing high-difficulty topics "
                    f"in {nearest.get('subject_name')} first, followed by spaced revision and mock questions."
                )
            else:
                return "You currently have no scheduled examinations. Focus on mastering your core subject topics with steady daily sessions."

        if "miss" in msg or "yesterday" in msg or "adjust" in msg:
            return (
                "Don't worry about missed sessions! Consistency beats perfection. "
                "Use the **'Adjust My Study Plan'** button on your dashboard to intelligently redistribute "
                "unfinished tasks across the upcoming days without overloading yourself."
            )

        if "consistency" in msg or "routine" in msg:
            return (
                "Here are 3 research-backed tips for study consistency:\n"
                "1. **Anchor to a fixed time:** Study at your configured preferred start time every day.\n"
                "2. **The 5-minute rule:** If you feel resistance, commit to studying for just 5 minutes.\n"
                "3. **Respect breaks:** Protect your break time to avoid mental burnout."
            )

        return (
            f"Hello! I am your AI Study Assistant. You currently have {len(subjects)} active subjects "
            f"and {len(exams)} upcoming exams. How can I help you plan your schedule, explain a concept, or review a strategy today?"
        )

    def generate_quiz(
        self,
        subject_name: str,
        topic_name: str,
        topic_description: str,
        difficulty: str,
        num_questions: int
    ) -> List[Dict[str, Any]]:
        """Generates multiple choice questions."""
        system_prompt = (
            "You are an academic test maker. Generate high quality multiple choice questions. "
            "Return a JSON object with key 'questions', which is an array of objects. "
            "Each question object must strictly have:\n"
            "- 'question_text': string\n"
            "- 'option_a': string\n"
            "- 'option_b': string\n"
            "- 'option_c': string\n"
            "- 'option_d': string\n"
            "- 'correct_option': string ('A', 'B', 'C', or 'D')\n"
            "- 'explanation': string explaining why that option is correct."
        )

        user_prompt = (
            f"Generate {num_questions} {difficulty}-difficulty multiple-choice questions for the following academic topic:\n"
            f"Subject: {subject_name}\n"
            f"Topic: {topic_name}\n"
            f"Details: {topic_description or 'Standard curriculum concept'}\n"
        )

        result = self._call_llm_json(system_prompt, user_prompt)
        if result and "questions" in result and len(result["questions"]) > 0:
            return result["questions"]

        # Educational fallback questions if LLM is offline
        return self._generate_fallback_quiz(subject_name, topic_name, difficulty, num_questions)

    def _generate_fallback_quiz(self, subject: str, topic: str, difficulty: str, count: int) -> List[Dict[str, Any]]:
        questions = [
            {
                "question_text": f"What is the foundational objective when analyzing '{topic}' in {subject}?",
                "option_a": "To systematically break down problem constraints into manageable components.",
                "option_b": "To eliminate the need for any formal algorithmic structure.",
                "option_c": "To bypass verification and rely strictly on heuristic intuition.",
                "option_d": "To increase computational redundancy without performance gain.",
                "correct_option": "A",
                "explanation": "Systematic decomposition of problem constraints is the primary goal in rigorous study of this topic."
            },
            {
                "question_text": f"Which approach yields the best long-term retention for '{topic}'?",
                "option_a": "Cramming the night before the examination.",
                "option_b": "Active recall combined with spaced repetition intervals.",
                "option_c": "Passive re-reading of textbooks without note-taking.",
                "option_d": "Memorizing without understanding foundational principles.",
                "correct_option": "B",
                "explanation": "Active recall and spaced repetition are experimentally proven to maximize memory consolidation."
            },
            {
                "question_text": f"When evaluating trade-offs in {topic}, what metric is typically critical?",
                "option_a": "Time and space complexity efficiency.",
                "option_b": "Total line count of notes written.",
                "option_c": "Random variable substitution.",
                "option_d": "Ignoring edge cases to optimize average execution.",
                "correct_option": "A",
                "explanation": "Time and space efficiency are standard engineering and academic evaluation criteria."
            },
            {
                "question_text": f"In a standard examination on {topic}, how should edge cases typically be handled?",
                "option_a": "They should be ignored unless explicitly stated.",
                "option_b": "They should be identified early, validated, and explicitly guarded against.",
                "option_c": "Assumed to never occur in realistic environments.",
                "option_d": "Substituted with arbitrary null values.",
                "correct_option": "B",
                "explanation": "Rigorous academic solutions require early identification and proper handling of edge conditions."
            },
            {
                "question_text": f"What is the primary indicator that mastery in {topic} has been achieved?",
                "option_a": "Ability to accurately explain and apply concepts to novel unseen problems.",
                "option_b": "Having read the textbook chapter once.",
                "option_c": "Spending more than 10 hours without practicing.",
                "option_d": "Re-reading highlighted notes.",
                "correct_option": "A",
                "explanation": "Mastery is demonstrated by successful transfer and application to unfamiliar problem sets."
            }
        ]
        return questions[:count]

ai_service = AIService()

