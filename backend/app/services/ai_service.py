import os
import json
import logging
import re
from typing import Dict, Any, List, Optional, Tuple
from app.core.config import settings

logger = logging.getLogger(__name__)

class AIService:
    """Google Gemini-backed AI service with rule-based fallbacks."""

    def __init__(self):
        self.model = (
            os.getenv("GEMINI_MODEL")
            or getattr(settings, "GEMINI_MODEL", None)
            or "gemini-2.5-flash"
        )
        self._last_checked_key: Optional[str] = None
        self._cached_client = None

    def _get_client(self):
        """Create or reuse a Google Gemini client."""
        current_key = (
            os.getenv("GEMINI_API_KEY")
            or getattr(settings, "GEMINI_API_KEY", None)
            or ""
        ).strip()

        if not current_key:
            self._cached_client = None
            self._last_checked_key = None
            return None, "missing_key"

        if current_key != self._last_checked_key or self._cached_client is None:
            try:
                from google import genai
                self._cached_client = genai.Client(api_key=current_key)
                self._last_checked_key = current_key
            except ImportError:
                logger.exception(
                    "Google GenAI SDK is not installed. Install it with: pip install google-genai"
                )
                return None, "sdk_not_installed"
            except Exception:
                logger.exception("Failed to initialize Gemini client")
                return None, "client_init_failed"

        return self._cached_client, None

    def is_available(self) -> bool:
        client, error = self._get_client()
        return client is not None and error is None

    @staticmethod
    def _classify_api_error(error: Exception) -> str:
        message = str(error).lower()
        if any(term in message for term in ("429", "quota", "resource_exhausted", "rate limit")):
            return "quota_exceeded"
        if any(term in message for term in ("401", "403", "api key", "unauthenticated", "permission denied")):
            return "invalid_key"
        if "timeout" in message or "deadline" in message:
            return "timeout"
        if "404" in message or "not found" in message:
            return "model_unavailable"
        return "api_error"

    @staticmethod
    def _history_to_gemini_contents(messages: List[Dict[str, str]]):
        """Convert ChatGPT-style history into Gemini Content objects."""
        from google.genai import types

        contents = []
        for message in messages:
            role = message.get("role", "user")
            text = message.get("content", "")
            if not text:
                continue
            if role == "system":
                # System instructions are passed separately in GenerateContentConfig.
                continue
            gemini_role = "model" if role in ("assistant", "model") else "user"
            contents.append(
                types.Content(
                    role=gemini_role,
                    parts=[types.Part.from_text(text=text)]
                )
            )
        return contents

    def _call_llm_json(
        self, system_prompt: str, user_prompt: str
    ) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
        """Call Gemini and require a JSON response."""
        client, error_code = self._get_client()
        if client is None:
            return None, error_code

        try:
            from google.genai import types

            response = client.models.generate_content(
                model=self.model,
                contents=user_prompt,
                config=types.GenerateContentConfig(
                    system_instruction=(
                        system_prompt
                        + "\\nReturn only valid JSON. Do not include Markdown fences."
                    ),
                    response_mime_type="application/json",
                    temperature=0.7,
                    max_output_tokens=8192,
                ),
            )
            raw_content = response.text
            if not raw_content:
                return None, "empty_response"
            parsed = json.loads(raw_content)
            if not isinstance(parsed, dict):
                return None, "invalid_json"
            return parsed, None
        except json.JSONDecodeError:
            logger.exception("Gemini returned invalid JSON")
            return None, "invalid_json"
        except Exception as exc:
            logger.exception("Gemini JSON generation failed")
            return None, self._classify_api_error(exc)

    def _call_llm_text(
        self, system_prompt: str, messages: List[Dict[str, str]]
    ) -> Tuple[Optional[str], Optional[str]]:
        """Call Gemini for conversational text."""
        client, error_code = self._get_client()
        if client is None:
            return None, error_code

        try:
            from google.genai import types

            contents = self._history_to_gemini_contents(messages)
            if not contents:
                return None, "empty_prompt"

            response = client.models.generate_content(
                model=self.model,
                contents=contents,
                config=types.GenerateContentConfig(
                    system_instruction=system_prompt,
                    temperature=0.7,
                    max_output_tokens=8192,
                ),
            )
            content = response.text
            if not content or not content.strip():
                return None, "empty_response"
            return content.strip(), None
        except Exception as exc:
            logger.exception("Gemini chat generation failed")
            return None, self._classify_api_error(exc)

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
            "Return a JSON object with: \\n"
            "- 'ai_summary': A motivating 2-3 sentence overview of this schedule.\\n"
            "- 'strategy_notes': An array of 3-4 specific academic study tips tailored to their goals and upcoming exams.\\n"
            "- 'session_recommendations': An array of objects each having 'session_index' (integer matching input) and 'recommendation' (concise 1-sentence tactical tip)."
        )

        user_prompt = json.dumps({
            "student_profile": student_profile,
            "upcoming_exams": upcoming_exams,
            "draft_sessions": [
                {
                    "index": i,
                    "date": session.get("session_date"),
                    "start": session.get("start_time"),
                    "subject": session.get("subject_name"),
                    "topic": session.get("topic_name"),
                    "type": session.get("session_type"),
                    "duration_minutes": session.get("duration_minutes")
                }
                for i, session in enumerate(draft_sessions)
            ]
        }, indent=2)

        result, _ = self._call_llm_json(system_prompt, user_prompt)
        if result and "ai_summary" in result:
            return result

        # Preserve the existing deterministic fallback behavior.
        strategy_notes = [
            f"Adhere strictly to {student_profile.get('break_duration', 15)}-minute breaks to prevent cognitive fatigue."
        ]
        if upcoming_exams:
            nearest = sorted(upcoming_exams, key=lambda x: x.get("days_remaining", 999))[0]
            strategy_notes.insert(
                0,
                f"Focus intensely on {nearest.get('subject_name', 'your upcoming exam')} "
                f"with exam in {nearest.get('days_remaining')} day(s)."
            )
            strategy_notes.append(
                "Prioritize past exam papers and timed active recall in high-difficulty subjects."
            )
        else:
            strategy_notes.insert(
                0, "Build strong conceptual foundations by taking notes in your own words."
            )
            strategy_notes.append(
                "Use spaced repetition quizzes to test retention across all active topics."
            )

        session_recommendations = []
        for i, session in enumerate(draft_sessions):
            session_type = session.get("session_type", "Learning")
            topic_name = session.get("topic_name", "this topic")
            if session_type == "Revision":
                tip = f"Review key formulas, flashcards, and definitions for {topic_name} without checking notes first."
            elif session_type == "Practice":
                tip = f"Solve 3-5 challenging application exercises on {topic_name} under timed conditions."
            else:
                tip = f"Break {topic_name} into foundational principles and create a mind map or concept summary."
            session_recommendations.append(
                {"session_index": i, "recommendation": tip}
            )

        return {
            "ai_summary": (
                f"Your schedule is structured with {len(draft_sessions)} session(s) targeting "
                "core subjects and upcoming exam milestones within your daily study limit."
            ),
            "strategy_notes": strategy_notes,
            "session_recommendations": session_recommendations
        }

    def generate_chat_response(
        self,
        student_context: Dict[str, Any],
        conversation_history: List[Dict[str, str]],
        user_message: str
    ) -> Tuple[str, str, Optional[str]]:
        """Return (response_text, mode ['gemini' | 'fallback'], error_detail)."""
        system_prompt = (
            "You are the AI Study Assistant for the AI Study Planner platform. "
            "Provide empathetic, accurate academic guidance, exam strategy, and subject explanations.\\n"
            "Use the supplied student context accurately. Never invent subjects, exams, or progress. "
            "Answer the user's actual question directly. For technical topics, explain step by step "
            "and include code examples when requested. If information is missing, say so.\\n"
            f"STUDENT DATABASE CONTEXT:\\n{json.dumps(student_context, indent=2)}"
        )

        messages = conversation_history[-10:] + [
            {"role": "user", "content": user_message}
        ]
        llm_reply, error_code = self._call_llm_text(system_prompt, messages)

        if llm_reply:
            return llm_reply, "gemini", None

        fallback_reply = self._fallback_chat_reply(user_message, student_context)
        return fallback_reply, "fallback", error_code

    def _fallback_chat_reply(self, message: str, context: Dict[str, Any]) -> str:
        """
        Comprehensive Academic Knowledge Engine for offline or fallback operation.
        Intelligently answers arbitrary questions across learning techniques, programming,
        mathematics, prioritization, study routines, and concentration.
        """
        msg = message.lower()
        student_name = context.get("student_name", "Student")
        first_name = student_name.split()[0] if student_name else "there"
        exams = context.get("upcoming_exams", [])
        subjects = context.get("subjects", [])
        pending_topics = context.get("pending_topics", [])
        daily_hours = context.get("daily_study_hours", 4.0)
        studied_hours_week = context.get("studied_hours_this_week", 0.0)
        streak = context.get("current_streak_days", 0)
        pref_start = context.get("preferred_start_time", "09:00")
        pref_end = context.get("preferred_end_time", "21:00")

        # 1. Pomodoro Technique
        if "pomodoro" in msg:
            return (
                "### The Pomodoro Technique for Students\n\n"
                "The **Pomodoro Technique** is a time-management method designed to maintain high cognitive focus while preventing mental fatigue:\n\n"
                "1. **Choose a Single Topic:** Select one specific topic (e.g., *Dynamic Programming*).\n"
                "2. **Set a 25-Minute Timer:** Work with zero distractions. Close extra browser tabs and place your phone out of reach.\n"
                "3. **Take a 5-Minute Break:** Stand up, stretch, hydrate, and relax your eyes.\n"
                "4. **Complete 4 Cycles:** After four 25-minute Pomodoros (100 mins of deep work), take an extended **15–30 minute break**.\n\n"
                "**Practical Example:**\n"
                "- **09:00 – 09:25:** Read theory & definitions\n"
                "- *09:25 – 09:30: Quick water break*\n"
                "- **09:30 – 09:55:** Solve 2 practice problems\n"
                "- *09:55 – 10:00: Quick walk/stretch*\n\n"
                f"With your daily target of **{daily_hours} hours**, completing approximately **6 to 8 Pomodoros** per day will maximize your academic productivity!"
            )

        # 2. Active Recall vs. Passive Learning & Feynman Technique
        if "active recall" in msg or "passive" in msg or "feynman" in msg or "retention" in msg:
            return (
                "### Active Recall vs. Passive Learning\n\n"
                "| Dimension | Passive Learning | Active Recall (Recommended) |\n"
                "| :--- | :--- | :--- |\n"
                "| **Method** | Re-reading notes, highlighting text, watching lectures passively | Closing notes, self-testing, solving problems from memory |\n"
                "| **Brain Activation** | Recognition memory (creates an 'illusion of competence') | Retrieval practice (strengthens neural pathways and long-term consolidation) |\n"
                "| **Long-Term Retention** | Low (~10–20% after one week) | High (~70–80% after one week) |\n\n"
                "**How to apply Active Recall right now:**\n"
                "1. **The Blank Page Method:** Read a topic for 15 minutes. Close the book and write down everything you remember on a blank sheet.\n"
                "2. **The Feynman Technique:** Explain the concept in plain English as if teaching a 10-year-old. Wherever you struggle, re-open your notes to fill the knowledge gap.\n"
                "3. **Use the Quiz Hub:** Take quick quizzes in this app to test your understanding before your exams!"
            )

        # 3. Binary Search / Programming / Coding Examples
        if "binary search" in msg:
            return (
                "### Binary Search Algorithm\n\n"
                "**Binary Search** is an efficient algorithm for searching an element in a **sorted array**. "
                "It works by repeatedly dividing the search interval in half with a time complexity of **$O(\\log N)$**.\n\n"
                "```cpp\n"
                "// C++ Implementation of Binary Search\n"
                "#include <iostream>\n"
                "#include <vector>\n\n"
                "int binarySearch(const std::vector<int>& arr, int target) {\n"
                "    int left = 0;\n"
                "    int right = arr.size() - 1;\n\n"
                "    while (left <= right) {\n"
                "        int mid = left + (right - left) / 2; // Prevents integer overflow\n"
                "        if (arr[mid] == target) return mid;     // Found target index\n"
                "        if (arr[mid] < target)  left = mid + 1; // Search right half\n"
                "        else                    right = mid - 1;// Search left half\n"
                "    }\n"
                "    return -1; // Target not found\n"
                "}\n"
                "```\n\n"
                "```python\n"
                "# Python Implementation\n"
                "def binary_search(arr, target):\n"
                "    left, right = 0, len(arr) - 1\n"
                "    while left <= right:\n"
                "        mid = left + (right - left) // 2\n"
                "        if arr[mid] == target:\n"
                "            return mid\n"
                "        elif arr[mid] < target:\n"
                "            left = mid + 1\n"
                "        else:\n"
                "            right = mid - 1\n"
                "    return -1\n"
                "```\n\n"
                "**Complexity:** Time: $O(\\log N)$, Space: $O(1)$ iterative."
            )

        # 4. Programming / C++ / Python General
        if "c++" in msg or "python" in msg or "code" in msg or "programming" in msg or "algorithm" in msg:
            return (
                "### Programming & Algorithmic Study Strategy\n\n"
                "When preparing for computer science and coding subjects:\n\n"
                "1. **Master Core Data Structures First:** Arrays, Linked Lists, Stacks, Queues, Trees, and Hash Maps.\n"
                "2. **Trace Code on Paper:** Step through loop variables and pointers by hand with small test cases before running code.\n"
                "3. **Analyze Edge Cases:** Null pointers, empty arrays, single-element collections, and integer boundary conditions.\n"
                "4. **Understand Space-Time Tradeoffs:** Always state the Big-O time and space complexity for your solutions.\n\n"
                "Feel free to ask for implementations or breakdowns of specific algorithms (e.g., QuickSort, BFS/DFS, Dynamic Programming, or Dijkstra)!"
            )

        # 5. Hours Studied / Weekly Progress
        if "how many hours" in msg or "hours studied" in msg or "my progress" in msg or "studied this week" in msg:
            weekly_goal = round(daily_hours * 7, 1)
            pct = round((studied_hours_week / weekly_goal * 100), 1) if weekly_goal > 0 else 0
            return (
                f"### Weekly Progress Summary for {first_name}\n\n"
                f"- **Hours Studied This Week:** **{studied_hours_week} hrs**\n"
                f"- **Weekly Target:** **{weekly_goal} hrs** ({daily_hours} hrs/day across 7 days)\n"
                f"- **Goal Completion:** **{pct}%**\n"
                f"- **Active Study Streak:** **{streak} day(s)** 🔥\n\n"
                f"Check your **Progress tab** to view your daily breakdown chart and subject-wise completion rates!"
            )

        # 6. Prioritization / What to Study Today
        if "prioritize" in msg or "what should i study" in msg or "priority" in msg or "which subject" in msg:
            if exams:
                nearest = sorted(exams, key=lambda x: x.get("days_remaining", 999))[0]
                topics_str = ", ".join(pending_topics[:4]) if pending_topics else "your core chapters"
                return (
                    f"### Recommended Study Priority for Today\n\n"
                    f"Based on your database schedule, your highest priority is **{nearest.get('title')}** "
                    f"({nearest.get('subject_name')}) with examination in **{nearest.get('days_remaining')} day(s)**.\n\n"
                    f"**Suggested Focus Strategy:**\n"
                    f"1. **Primary Block (Morning/Peak):** Allocate your first 2 hours to pending topics: *{topics_str}*.\n"
                    f"2. **Secondary Block:** Active problem-solving and past paper questions for {nearest.get('subject_name')}.\n"
                    f"3. **Spaced Revision:** Dedicate 30 minutes to review yesterday's material.\n\n"
                    f"Open your **Planner** to generate or view your optimized daily study timetable."
                )
            elif subjects:
                subjs_list = ", ".join(subjects[:3])
                return (
                    f"### Recommended Study Focus\n\n"
                    f"You have no immediate exams scheduled. Focus on making steady progress across: **{subjs_list}**.\n\n"
                    f"1. Work on high-difficulty topics first during your preferred window ({pref_start} – {pref_end}).\n"
                    f"2. Spend 45 minutes on theory, 15 minutes on practice, and take regular breaks.\n"
                    f"3. Mark topics as completed in the **Subjects** tab to keep your progress analytics updated."
                )
            else:
                return (
                    f"Hello {first_name}! You haven't added any subjects or examinations yet. "
                    "Head over to the **Subjects** page to add your courses and topics, and I will create a tailored priority timetable for you!"
                )

        # 7. Examination Preparation
        if "exam" in msg or "examination" in msg or "prepare" in msg:
            if exams:
                nearest = sorted(exams, key=lambda x: x.get("days_remaining", 999))[0]
                days_left = nearest.get('days_remaining', 0)
                return (
                    f"### Examination Preparation Plan: {nearest.get('title')}\n\n"
                    f"Target Subject: **{nearest.get('subject_name')}** | Days Remaining: **{days_left}**\n\n"
                    "**Recommended 3-Phase Countdown:**\n"
                    "1. **Phase 1 (Concepts & Notes):** Finish any incomplete topics and summarize key formulas onto single cheat sheets.\n"
                    "2. **Phase 2 (Past Papers & Timed Practice):** Solve past examination questions under strictly timed conditions.\n"
                    "3. **Phase 3 (Review & Refinement):** Use the Quiz Hub for active recall on weak spots and review error logs.\n\n"
                    "Make sure to keep your daily study sessions aligned with your exam schedule!"
                )
            else:
                return (
                    "To prepare effectively for exams:\n"
                    "1. Break your syllabus into discrete, manageable topics.\n"
                    "2. Add your upcoming exam dates in the **Examinations** page so the planner can prioritize your workload automatically.\n"
                    "3. Practice active recall rather than passive re-reading."
                )

        # 8. Study Routine / Schedule Routine
        if "routine" in msg or "schedule" in msg or "routine based" in msg or "daily routine" in msg:
            return (
                f"### Personalized Study Routine for {first_name}\n\n"
                f"Configured Availability: **{daily_hours} hours/day** | Window: **{pref_start} to {pref_end}**\n\n"
                f"**Optimized Daily Flow:**\n"
                f"- **{pref_start} – 10:30:** Deep Work Block 1 (Most challenging topic while mental energy is peak)\n"
                f"- *10:30 – 10:45: Mindful Break (15 mins)*\n"
                f"- **10:45 – 12:00:** Deep Work Block 2 (Practice exercises & problem solving)\n"
                f"- *Afternoon:* Classes, rest, and physical activity\n"
                f"- **18:00 – 19:00:** Review & Spaced Repetition (Flashcards, quiz hub, and summary notes)\n\n"
                "Visit your **Planner** page to generate a daily or weekly timetable following this structure!"
            )

        # 9. Concentration & Focus
        if "concentration" in msg or "focus" in msg or "distraction" in msg or "burnout" in msg:
            return (
                "### Strategies for Deep Concentration and Focus\n\n"
                "1. **Environment Design:** Keep your study desk free of phones, notifications, and clutter. Visual simplicity fosters mental clarity.\n"
                "2. **The 5-Minute Rule:** When facing procrastination, tell yourself you will only study for 5 minutes. Starting overcomes the activation barrier.\n"
                "3. **Hydration and Lighting:** Drink water every hour and study under cool, bright light to sustain alertness.\n"
                "4. **Batch Distractions:** Write intrusive thoughts on a 'later pad' to review after your study block instead of switching tasks immediately.\n"
                "5. **Respect Your Breaks:** True breaks involve stepping away from screens (walking, stretching, resting your eyes)."
            )

        # 10. General Academic Assistant Guidance
        active_subjs = f"{len(subjects)} active subject(s)" if subjects else "no enrolled subjects yet"
        active_exams = f"{len(exams)} upcoming exam(s)" if exams else "no scheduled exams"

        return (
            f"Hello {first_name}! I am your AI Study Assistant.\n\n"
            f"You currently have **{active_subjs}** and **{active_exams}** on your dashboard. "
            f"Your daily target is **{daily_hours} hours**.\n\n"
            "I can help you with:\n"
            "- **Exam Strategy:** Ask *'Which subjects and topics should I prioritize?'*\n"
            "- **Concept Explanations:** Ask *'Explain binary search with C++ and Python examples'*\n"
            "- **Learning Science:** Ask *'Explain the Pomodoro technique'*, or *'What is active recall vs passive learning?'*\n"
            "- **Time Management:** Ask *'Suggest a study routine based on my available time'* or *'How many hours have I studied this week?'*\n\n"
            "How can I assist your study session today?"
        )

    def generate_quiz(
        self,
        subject_name: str,
        topic_name: str,
        topic_description: str,
        difficulty: str,
        num_questions: int
    ) -> List[Dict[str, Any]]:
        """Generates multiple-choice questions using Gemini or educational fallback."""
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

        result, _ = self._call_llm_json(system_prompt, user_prompt)
        if result and "questions" in result and len(result["questions"]) > 0:
            return result["questions"]

        # Educational fallback questions
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
