import React, { useState, useEffect } from 'react';
import { useLocation } from 'react-router-dom';
import { aiAPI, subjectsAPI, topicsAPI } from '../services/api';
import {
  BrainCircuit,
  Sparkles,
  CheckCircle2,
  XCircle,
  HelpCircle,
  ArrowRight,
  RotateCcw,
  BookOpen,
  Award,
  AlertCircle
} from 'lucide-react';

export default function QuizHub() {
  const location = useLocation();
  const [subjects, setSubjects] = useState([]);
  const [topics, setTopics] = useState([]);
  const [selectedSubjectId, setSelectedSubjectId] = useState(location.state?.subject_id || '');
  const [selectedTopicId, setSelectedTopicId] = useState(location.state?.topic_id || '');
  const [difficulty, setDifficulty] = useState('Medium');
  const [numQuestions, setNumQuestions] = useState(5);
  const [loading, setLoading] = useState(false);
  const [submitting, setSubmitting] = useState(false);

  // Active quiz state
  const [activeQuiz, setActiveQuiz] = useState(null);
  const [answers, setAnswers] = useState({}); // { question_id: 'A' }
  const [quizResult, setQuizResult] = useState(null);
  const [history, setHistory] = useState([]);

  useEffect(() => {
    subjectsAPI.getAll().then((res) => {
      setSubjects(res.data);
      if (!selectedSubjectId && res.data.length > 0) {
        setSelectedSubjectId(res.data[0].id);
      }
    }).catch(console.error);

    fetchHistory();
  }, []);

  useEffect(() => {
    if (selectedSubjectId) {
      topicsAPI.getAll(selectedSubjectId).then((res) => {
        setTopics(res.data);
        if (res.data.length > 0) {
          const currentValid = res.data.some(t => t.id === Number(selectedTopicId));
          if (!currentValid) {
            setSelectedTopicId(res.data[0].id);
          }
        } else {
          setSelectedTopicId('');
        }
      }).catch(console.error);
    } else {
      setTopics([]);
      setSelectedTopicId('');
    }
  }, [selectedSubjectId]);

  const fetchHistory = () => {
    aiAPI.getQuizHistory().then((res) => setHistory(res.data)).catch(console.error);
  };

  const handleStartQuiz = async (e) => {
    e.preventDefault();
    if (!selectedSubjectId || !selectedTopicId) return;

    setLoading(true);
    setQuizResult(null);
    setAnswers({});

    try {
      const res = await aiAPI.generateQuiz({
        subject_id: parseInt(selectedSubjectId, 10),
        topic_id: parseInt(selectedTopicId, 10),
        difficulty,
        num_questions: parseInt(numQuestions, 10),
      });
      setActiveQuiz(res.data);
    } catch (err) {
      alert(err.response?.data?.detail || 'Failed to generate quiz questions');
    } finally {
      setLoading(false);
    }
  };

  const handleSubmitQuiz = async () => {
    if (!activeQuiz) return;

    // Check that all questions are answered
    const unanswered = activeQuiz.questions.filter((q) => !answers[q.id]);
    if (unanswered.length > 0) {
      if (!window.confirm(`You still have ${unanswered.length} unanswered questions. Submit anyway?`)) {
        return;
      }
    }

    setSubmitting(true);
    try {
      const formattedAnswers = Object.entries(answers).map(([qid, opt]) => ({
        question_id: parseInt(qid, 10),
        selected_option: opt,
      }));

      const res = await aiAPI.submitQuiz({
        attempt_id: activeQuiz.attempt_id,
        answers: formattedAnswers,
      });

      setQuizResult(res.data);
      setActiveQuiz(null);
      fetchHistory();
    } catch (err) {
      alert('Failed to evaluate quiz');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="space-y-6 max-w-4xl mx-auto">
      {/* Title */}
      <div>
        <h2 className="text-xl font-bold text-slate-900 dark:text-slate-100 flex items-center gap-2">
          <BrainCircuit className="w-5 h-5 text-brand-600" />
          <span>AI Knowledge Quiz Hub</span>
        </h2>
        <p className="text-xs text-slate-500 dark:text-slate-400">
          Generate syllabus-aligned multiple choice questions to evaluate topic mastery and trigger spaced revision
        </p>
      </div>

      {/* Case 1: Quiz Result Screen */}
      {quizResult && (
        <div className="p-6 rounded-3xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-xl space-y-6">
          <div className="text-center pb-6 border-b border-slate-100 dark:border-slate-800">
            <div className={`inline-flex p-3 rounded-2xl mb-3 ${
              quizResult.score_percentage >= 70 ? 'bg-emerald-100 text-emerald-600' : 'bg-amber-100 text-amber-600'
            }`}>
              <Award className="w-8 h-8" />
            </div>
            <h3 className="text-2xl font-black text-slate-900 dark:text-slate-100">
              Score: {quizResult.score_percentage}%
            </h3>
            <p className="text-xs text-slate-500 mt-1">
              {quizResult.correct_answers} correct out of {quizResult.total_questions} questions ({quizResult.difficulty} Difficulty)
            </p>

            {quizResult.score_percentage < 70 ? (
              <div className="mt-4 p-3 rounded-xl bg-amber-50 dark:bg-amber-950/40 text-amber-700 dark:text-amber-300 text-xs inline-flex items-center gap-2">
                <AlertCircle className="w-4 h-4 shrink-0" />
                <span>Score under 70%: This topic has been automatically scheduled for spaced revision!</span>
              </div>
            ) : (
              <div className="mt-4 p-3 rounded-xl bg-emerald-50 dark:bg-emerald-950/40 text-emerald-700 dark:text-emerald-300 text-xs inline-flex items-center gap-2">
                <CheckCircle2 className="w-4 h-4 shrink-0" />
                <span>Great mastery! Advanced spaced repetition schedule registered.</span>
              </div>
            )}
          </div>

          {/* Detailed Question Review */}
          <div className="space-y-4">
            <h4 className="text-xs font-bold uppercase tracking-wider text-slate-400">Detailed Answer Review</h4>
            {quizResult.questions.map((q, idx) => (
              <div
                key={q.id}
                className={`p-4 rounded-2xl border text-xs space-y-2 ${
                  q.is_correct
                    ? 'bg-emerald-50/30 dark:bg-emerald-950/10 border-emerald-200 dark:border-emerald-800/40'
                    : 'bg-red-50/30 dark:bg-red-950/10 border-red-200 dark:border-red-800/40'
                }`}
              >
                <div className="flex items-start justify-between gap-2">
                  <p className="font-bold text-slate-900 dark:text-slate-100">
                    {idx + 1}. {q.question_text}
                  </p>
                  <span className={`px-2 py-0.5 rounded-full font-bold ${
                    q.is_correct ? 'bg-emerald-100 text-emerald-700' : 'bg-red-100 text-red-700'
                  }`}>
                    {q.is_correct ? 'Correct' : 'Incorrect'}
                  </span>
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-1.5 text-slate-600 dark:text-slate-400">
                  <p className={q.correct_option === 'A' ? 'font-bold text-emerald-600' : ''}>A: {q.option_a}</p>
                  <p className={q.correct_option === 'B' ? 'font-bold text-emerald-600' : ''}>B: {q.option_b}</p>
                  <p className={q.correct_option === 'C' ? 'font-bold text-emerald-600' : ''}>C: {q.option_c}</p>
                  <p className={q.correct_option === 'D' ? 'font-bold text-emerald-600' : ''}>D: {q.option_d}</p>
                </div>

                <p className="text-slate-500 pt-1 border-t border-slate-100 dark:border-slate-800">
                  <strong>Explanation:</strong> {q.explanation}
                </p>
              </div>
            ))}
          </div>

          <div className="text-center pt-2">
            <button
              onClick={() => {
                setQuizResult(null);
                setActiveQuiz(null);
              }}
              className="px-6 py-2.5 rounded-xl bg-brand-600 hover:bg-brand-700 text-white font-semibold text-xs shadow-md"
            >
              Take Another Quiz
            </button>
          </div>
        </div>
      )}

      {/* Case 2: Active Quiz Taking Mode */}
      {activeQuiz && !quizResult && (
        <div className="p-6 rounded-3xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-xl space-y-6">
          <div className="flex items-center justify-between pb-4 border-b border-slate-100 dark:border-slate-800">
            <div>
              <span className="text-xs font-semibold text-brand-600">{activeQuiz.subject_name}</span>
              <h3 className="font-bold text-base text-slate-900 dark:text-slate-100">{activeQuiz.topic_name}</h3>
            </div>
            <span className="text-xs px-2.5 py-1 rounded-full bg-slate-100 dark:bg-slate-800 font-bold">
              {activeQuiz.difficulty} Difficulty
            </span>
          </div>

          <div className="space-y-6">
            {activeQuiz.questions.map((q, idx) => (
              <div key={q.id} className="p-4 rounded-2xl bg-slate-50 dark:bg-slate-800/40 border border-slate-200 dark:border-slate-700/60 space-y-3">
                <p className="font-bold text-sm text-slate-900 dark:text-slate-100">
                  {idx + 1}. {q.question_text}
                </p>

                <div className="space-y-2">
                  {[
                    { key: 'A', text: q.option_a },
                    { key: 'B', text: q.option_b },
                    { key: 'C', text: q.option_c },
                    { key: 'D', text: q.option_d },
                  ].map((opt) => {
                    const isSelected = answers[q.id] === opt.key;
                    return (
                      <button
                        key={opt.key}
                        type="button"
                        onClick={() => setAnswers({ ...answers, [q.id]: opt.key })}
                        className={`w-full p-3 rounded-xl border text-left text-xs font-medium flex items-center gap-3 transition-all ${
                          isSelected
                            ? 'bg-brand-500 text-white border-brand-500 shadow-sm'
                            : 'bg-white dark:bg-slate-900 border-slate-200 dark:border-slate-800 hover:border-brand-300'
                        }`}
                      >
                        <span className={`w-6 h-6 rounded-lg flex items-center justify-center font-bold text-xs shrink-0 ${
                          isSelected ? 'bg-white/20 text-white' : 'bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300'
                        }`}>
                          {opt.key}
                        </span>
                        <span>{opt.text}</span>
                      </button>
                    );
                  })}
                </div>
              </div>
            ))}
          </div>

          <div className="flex items-center justify-between pt-4 border-t border-slate-100 dark:border-slate-800">
            <button
              onClick={() => setActiveQuiz(null)}
              className="px-4 py-2 rounded-xl text-xs font-semibold text-slate-500 hover:bg-slate-100 dark:hover:bg-slate-800"
            >
              Cancel Quiz
            </button>
            <button
              onClick={handleSubmitQuiz}
              disabled={submitting}
              className="px-6 py-2.5 rounded-xl bg-brand-600 hover:bg-brand-700 text-white text-xs font-bold shadow-md shadow-brand-500/20 disabled:opacity-50"
            >
              {submitting ? 'Evaluating...' : 'Submit Answers & View Score'}
            </button>
          </div>
        </div>
      )}

      {/* Case 3: Initial Quiz Config Form */}
      {!activeQuiz && !quizResult && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Generation Config Card (2 cols) */}
          <div className="lg:col-span-2 p-6 rounded-3xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-sm">
            <h3 className="font-bold text-sm text-slate-900 dark:text-slate-100 mb-4 flex items-center gap-2">
              <Sparkles className="w-4 h-4 text-brand-600" />
              <span>Configure AI Quiz</span>
            </h3>

            <form onSubmit={handleStartQuiz} className="space-y-4">
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-semibold mb-1">Subject</label>
                  <select
                    required
                    value={selectedSubjectId}
                    onChange={(e) => setSelectedSubjectId(e.target.value)}
                    className="w-full px-3 py-2 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-950 text-sm"
                  >
                    {subjects.map((s) => (
                      <option key={s.id} value={s.id}>{s.name}</option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="block text-xs font-semibold mb-1">Topic</label>
                  <select
                    required
                    value={selectedTopicId}
                    onChange={(e) => setSelectedTopicId(e.target.value)}
                    className="w-full px-3 py-2 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-950 text-sm"
                  >
                    {topics.map((t) => (
                      <option key={t.id} value={t.id}>{t.name}</option>
                    ))}
                  </select>
                </div>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-semibold mb-1">Difficulty</label>
                  <select
                    value={difficulty}
                    onChange={(e) => setDifficulty(e.target.value)}
                    className="w-full px-3 py-2 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-950 text-sm"
                  >
                    <option value="Easy">Easy</option>
                    <option value="Medium">Medium</option>
                    <option value="Hard">Hard</option>
                  </select>
                </div>

                <div>
                  <label className="block text-xs font-semibold mb-1">Number of Questions</label>
                  <select
                    value={numQuestions}
                    onChange={(e) => setNumQuestions(e.target.value)}
                    className="w-full px-3 py-2 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-950 text-sm"
                  >
                    <option value="3">3 Questions (Quick Test)</option>
                    <option value="5">5 Questions (Standard)</option>
                    <option value="10">10 Questions (Comprehensive)</option>
                  </select>
                </div>
              </div>

              <p className="text-xs text-slate-400 bg-slate-50 dark:bg-slate-800/40 p-3 rounded-xl leading-relaxed">
                Quizzes are evaluated automatically. Scores under 70% automatically trigger spaced revision entries to ensure continuous knowledge retention.
              </p>

              <button
                type="submit"
                disabled={loading || subjects.length === 0 || topics.length === 0}
                className="w-full py-2.5 px-4 rounded-xl bg-brand-600 hover:bg-brand-700 text-white font-semibold text-sm shadow-md shadow-brand-500/25 flex items-center justify-center gap-2 disabled:opacity-50"
              >
                <Sparkles className="w-4 h-4" />
                <span>{loading ? 'Synthesizing Quiz Questions...' : 'Generate & Start Quiz'}</span>
              </button>
            </form>
          </div>

          {/* Past Attempts History (1 col) */}
          <div className="p-6 rounded-3xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-sm space-y-3">
            <h3 className="font-bold text-sm text-slate-900 dark:text-slate-100 flex items-center gap-2">
              <Award className="w-4 h-4 text-amber-500" />
              <span>Past Quiz Attempts</span>
            </h3>

            {history.length === 0 ? (
              <p className="text-xs text-slate-400 py-6 text-center">No quizzes attempted yet.</p>
            ) : (
              <div className="space-y-2 max-h-72 overflow-y-auto">
                {history.map((att) => (
                  <div key={att.id} className="p-2.5 rounded-xl border border-slate-100 dark:border-slate-800 text-xs">
                    <div className="flex items-center justify-between font-bold">
                      <span className="truncate">{att.topic_name}</span>
                      <span className={att.score_percentage >= 70 ? 'text-emerald-600' : 'text-amber-500'}>
                        {att.score_percentage}%
                      </span>
                    </div>
                    <p className="text-[11px] text-slate-400 mt-0.5">
                      {att.subject_name} • {att.difficulty}
                    </p>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

