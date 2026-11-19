import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { plansAPI, examsAPI, progressAPI, revisionAPI, subjectsAPI } from '../services/api';
import {
  Clock,
  Flame,
  GraduationCap,
  CheckCircle2,
  AlertCircle,
  Sparkles,
  Calendar,
  BookOpen,
  ArrowRight,
  Repeat,
  PlusCircle,
  Check,
  XCircle,
  PlayCircle
} from 'lucide-react';

export default function Dashboard() {
  const { user } = useAuth();
  const [loading, setLoading] = useState(true);
  const [todaySessions, setTodaySessions] = useState([]);
  const [exams, setExams] = useState([]);
  const [progress, setProgress] = useState(null);
  const [revisions, setRevisions] = useState([]);
  const [subjects, setSubjects] = useState([]);
  const [generating, setGenerating] = useState(false);

  const getLocalDateStr = (d = new Date()) => {
    const year = d.getFullYear();
    const month = String(d.getMonth() + 1).padStart(2, '0');
    const day = String(d.getDate()).padStart(2, '0');
    return `${year}-${month}-${day}`;
  };

  const fetchDashboardData = async () => {
    setLoading(true);
    try {
      const todayStr = getLocalDateStr();
      const [sessRes, examRes, progRes, revRes, subjRes] = await Promise.all([
        plansAPI.getDaily(todayStr),
        examsAPI.getAll(),
        progressAPI.getOverview(),
        revisionAPI.getAll(),
        subjectsAPI.getAll(),
      ]);

      setTodaySessions(sessRes.data);
      setExams(examRes.data);
      setProgress(progRes.data);
      setRevisions(revRes.data.filter(r => r.status === 'Pending'));
      setSubjects(subjRes.data);
    } catch (err) {
      console.error('Failed to load dashboard data:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDashboardData();
  }, []);

  const handleStatusUpdate = async (sessionId, newStatus) => {
    try {
      await plansAPI.updateSessionStatus(sessionId, { status: newStatus });
      // Refresh
      fetchDashboardData();
    } catch (err) {
      console.error('Failed to update session:', err);
    }
  };

  const handleGenerateToday = async () => {
    setGenerating(true);
    try {
      await plansAPI.generate({ plan_type: 'daily', regenerate: true });
      fetchDashboardData();
    } catch (err) {
      console.error('Failed to generate daily plan:', err);
    } finally {
      setGenerating(false);
    }
  };

  const handleCompleteRevision = async (revId) => {
    try {
      await revisionAPI.complete(revId);
      fetchDashboardData();
    } catch (err) {
      console.error('Failed to complete revision:', err);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[500px]">
        <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-brand-600"></div>
      </div>
    );
  }

  const urgentExams = exams.filter(e => e.is_urgent).slice(0, 3);

  return (
    <div className="space-y-6">
      {/* Welcome Banner */}
      <div className="p-6 rounded-3xl bg-gradient-to-r from-brand-600 via-indigo-600 to-purple-600 text-white shadow-xl shadow-brand-500/15 relative overflow-hidden">
        <div className="absolute right-0 top-0 bottom-0 w-96 bg-[radial-gradient(ellipse_at_top_right,_var(--tw-gradient-stops))] from-white/10 to-transparent pointer-events-none" />
        <div className="relative z-10 max-w-2xl">
          <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-white/20 backdrop-blur-md text-xs font-semibold mb-3">
            <Sparkles className="w-3.5 h-3.5" />
            <span>AI Powered Academic Assistant</span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-extrabold tracking-tight">
            Welcome back, {user?.full_name?.split(' ')[0] || 'Student'}!
          </h1>
          <p className="text-white/80 text-sm mt-1.5 leading-relaxed">
            {todaySessions.length > 0
              ? `You have ${todaySessions.filter(s => s.status === 'Pending').length} pending study session(s) scheduled for today. Let's make continuous progress!`
              : "No sessions scheduled for today yet. Generate a personalized daily study plan or jump into your weekly schedule."}
          </p>
          <div className="flex items-center gap-3 mt-4">
            <Link
              to="/planner"
              className="inline-flex items-center gap-2 px-4 py-2 rounded-xl bg-white text-brand-700 font-semibold text-xs shadow-md hover:bg-brand-50 transition-all"
            >
              <Calendar className="w-4 h-4" />
              <span>Open Study Planner</span>
            </Link>
            <Link
              to="/assistant"
              className="inline-flex items-center gap-2 px-4 py-2 rounded-xl bg-white/10 hover:bg-white/20 text-white font-semibold text-xs backdrop-blur-md transition-all"
            >
              <Sparkles className="w-4 h-4" />
              <span>Ask AI Assistant</span>
            </Link>
          </div>
        </div>
      </div>

      {/* Metric Cards Grid */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="p-4 sm:p-5 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-sm">
          <div className="flex items-center justify-between text-slate-500 dark:text-slate-400">
            <span className="text-xs font-semibold uppercase tracking-wider">Total Study Time</span>
            <div className="p-2 rounded-xl bg-brand-50 dark:bg-brand-950/50 text-brand-600">
              <Clock className="w-4 h-4" />
            </div>
          </div>
          <p className="text-2xl font-bold text-slate-900 dark:text-slate-100 mt-2">
            {progress?.total_study_hours || 0} <span className="text-sm font-normal text-slate-500">hrs</span>
          </p>
          <p className="text-xs text-slate-400 mt-1">Across all completed sessions</p>
        </div>

        <div className="p-4 sm:p-5 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-sm">
          <div className="flex items-center justify-between text-slate-500 dark:text-slate-400">
            <span className="text-xs font-semibold uppercase tracking-wider">Current Streak</span>
            <div className="p-2 rounded-xl bg-orange-50 dark:bg-orange-950/50 text-orange-500">
              <Flame className="w-4 h-4" />
            </div>
          </div>
          <p className="text-2xl font-bold text-slate-900 dark:text-slate-100 mt-2">
            {progress?.current_streak_days || 0} <span className="text-sm font-normal text-slate-500">days</span>
          </p>
          <p className="text-xs text-slate-400 mt-1">Daily consistency streak</p>
        </div>

        <div className="p-4 sm:p-5 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-sm">
          <div className="flex items-center justify-between text-slate-500 dark:text-slate-400">
            <span className="text-xs font-semibold uppercase tracking-wider">Completed Topics</span>
            <div className="p-2 rounded-xl bg-emerald-50 dark:bg-emerald-950/50 text-emerald-500">
              <CheckCircle2 className="w-4 h-4" />
            </div>
          </div>
          <p className="text-2xl font-bold text-slate-900 dark:text-slate-100 mt-2">
            {progress?.completed_topics || 0} <span className="text-sm font-normal text-slate-500">/ {progress?.total_topics || 0}</span>
          </p>
          <p className="text-xs text-slate-400 mt-1">{progress?.overall_completion_rate || 0}% overall syllabus done</p>
        </div>

        <div className="p-4 sm:p-5 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-sm">
          <div className="flex items-center justify-between text-slate-500 dark:text-slate-400">
            <span className="text-xs font-semibold uppercase tracking-wider">Upcoming Exams</span>
            <div className="p-2 rounded-xl bg-purple-50 dark:bg-purple-950/50 text-purple-600">
              <GraduationCap className="w-4 h-4" />
            </div>
          </div>
          <p className="text-2xl font-bold text-slate-900 dark:text-slate-100 mt-2">
            {exams.length}
          </p>
          <p className="text-xs text-slate-400 mt-1">{urgentExams.length} urgent (&lt; 7 days)</p>
        </div>
      </div>

      {/* Main Two-Column Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left 2 Cols: Today's Schedule */}
        <div className="lg:col-span-2 space-y-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <h2 className="text-base font-bold text-slate-900 dark:text-slate-100">Today's Study Schedule</h2>
              <span className="text-xs font-semibold px-2 py-0.5 rounded-full bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400">
                {new Date().toLocaleDateString(undefined, { weekday: 'short', month: 'short', day: 'numeric' })}
              </span>
            </div>
            {todaySessions.length === 0 && (
              <button
                onClick={handleGenerateToday}
                disabled={generating}
                className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-semibold bg-brand-600 text-white hover:bg-brand-700 transition-all disabled:opacity-50"
              >
                <Sparkles className="w-3.5 h-3.5" />
                <span>{generating ? 'Generating...' : 'Generate Today\'s Plan'}</span>
              </button>
            )}
          </div>

          {todaySessions.length === 0 ? (
            <div className="p-8 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 text-center">
              <div className="h-12 w-12 rounded-2xl bg-brand-50 dark:bg-brand-950/50 text-brand-600 flex items-center justify-center mx-auto mb-3">
                <Calendar className="w-6 h-6" />
              </div>
              <h3 className="font-bold text-sm text-slate-800 dark:text-slate-200">No Sessions Planned for Today</h3>
              <p className="text-xs text-slate-400 max-w-sm mx-auto mt-1 mb-4">
                You haven't scheduled any study blocks for today yet. Use the AI planner to generate a balanced timetable.
              </p>
              <button
                onClick={handleGenerateToday}
                disabled={generating}
                className="inline-flex items-center gap-2 px-4 py-2 rounded-xl bg-brand-600 hover:bg-brand-700 text-white text-xs font-semibold shadow-md shadow-brand-500/20"
              >
                <Sparkles className="w-4 h-4" />
                <span>{generating ? 'Generating Schedule...' : 'Generate Today\'s Study Plan'}</span>
              </button>
            </div>
          ) : (
            <div className="space-y-3">
              {todaySessions.map((session) => {
                const isCompleted = session.status === 'Completed';
                const isPartially = session.status === 'Partially Completed';
                const isSkipped = session.status === 'Skipped';

                return (
                  <div
                    key={session.id}
                    className={`p-4 rounded-2xl border transition-all ${
                      isCompleted
                        ? 'bg-emerald-50/50 dark:bg-emerald-950/10 border-emerald-200 dark:border-emerald-800/40'
                        : isPartially
                        ? 'bg-amber-50/50 dark:bg-amber-950/10 border-amber-200 dark:border-amber-800/40'
                        : isSkipped
                        ? 'bg-slate-50 dark:bg-slate-800/20 border-slate-200 dark:border-slate-800 opacity-60'
                        : 'bg-white dark:bg-slate-900 border-slate-200 dark:border-slate-800 hover:shadow-md'
                    }`}
                  >
                    <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                      <div className="flex items-start gap-3">
                        <div
                          className="w-2.5 h-10 rounded-full shrink-0"
                          style={{ backgroundColor: session.subject_color || '#4F46E5' }}
                        />
                        <div>
                          <div className="flex items-center gap-2 flex-wrap">
                            <span className="text-xs font-bold px-2 py-0.5 rounded-md bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300">
                              {session.start_time} - {session.end_time} ({session.duration_minutes}m)
                            </span>
                            <span className="text-xs font-semibold text-brand-600 dark:text-brand-400">
                              {session.subject_name}
                            </span>
                            <span className="text-[10px] font-medium px-2 py-0.5 rounded-full bg-brand-50 dark:bg-brand-950/50 text-brand-600">
                              {session.session_type}
                            </span>
                          </div>
                          <h4 className="font-bold text-sm text-slate-900 dark:text-slate-100 mt-1">
                            {session.topic_name}
                          </h4>
                          {session.ai_recommendation && (
                            <p className="text-xs text-slate-500 dark:text-slate-400 mt-1 flex items-center gap-1.5">
                              <Sparkles className="w-3.5 h-3.5 text-amber-500 shrink-0" />
                              <span>{session.ai_recommendation}</span>
                            </p>
                          )}
                        </div>
                      </div>

                      {/* Action buttons */}
                      <div className="flex items-center gap-1.5 self-end sm:self-center shrink-0">
                        {isCompleted ? (
                          <div className="flex items-center gap-1.5">
                            <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-xl text-xs font-semibold bg-emerald-100 dark:bg-emerald-950/50 text-emerald-700 dark:text-emerald-400">
                              <Check className="w-3.5 h-3.5" /> Completed
                            </span>
                            <button
                              onClick={() => handleStatusUpdate(session.id, 'Pending')}
                              className="text-[11px] text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 underline ml-1"
                              title="Revert status to Pending"
                            >
                              Undo
                            </button>
                          </div>
                        ) : isSkipped ? (
                          <div className="flex items-center gap-1.5">
                            <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-xl text-xs font-semibold bg-slate-100 dark:bg-slate-800 text-slate-500">
                              Skipped
                            </span>
                            <button
                              onClick={() => handleStatusUpdate(session.id, 'Pending')}
                              className="text-[11px] text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 underline ml-1"
                              title="Revert status to Pending"
                            >
                              Undo
                            </button>
                          </div>
                        ) : (
                          <>
                            <button
                              onClick={() => handleStatusUpdate(session.id, 'Completed')}
                              className="p-1.5 rounded-lg text-emerald-600 hover:bg-emerald-50 dark:hover:bg-emerald-950/30 transition-colors"
                              title="Mark as Completed"
                            >
                              <CheckCircle2 className="w-5 h-5" />
                            </button>
                            <button
                              onClick={() => handleStatusUpdate(session.id, 'Partially Completed')}
                              className="p-1.5 rounded-lg text-amber-500 hover:bg-amber-50 dark:hover:bg-amber-950/30 transition-colors"
                              title="Partially Completed"
                            >
                              <Clock className="w-5 h-5" />
                            </button>
                            <button
                              onClick={() => handleStatusUpdate(session.id, 'Skipped')}
                              className="p-1.5 rounded-lg text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors"
                              title="Skip"
                            >
                              <XCircle className="w-5 h-5" />
                            </button>
                          </>
                        )}
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>

        {/* Right 1 Col: Urgent Exams & Spaced Revisions */}
        <div className="space-y-6">
          {/* Urgent Examinations Card */}
          <div className="p-5 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-sm">
            <div className="flex items-center justify-between pb-3 border-b border-slate-100 dark:border-slate-800">
              <h3 className="font-bold text-sm flex items-center gap-2">
                <GraduationCap className="w-4 h-4 text-brand-600" />
                <span>Upcoming Exams</span>
              </h3>
              <Link to="/exams" className="text-xs text-brand-600 hover:underline font-semibold">
                View all
              </Link>
            </div>

            <div className="divide-y divide-slate-100 dark:divide-slate-800 mt-2">
              {exams.length === 0 ? (
                <div className="py-6 text-center text-xs text-slate-400">
                  <p>No exams registered yet.</p>
                  <Link to="/exams" className="text-brand-600 font-semibold mt-1 inline-block hover:underline">
                    + Add your first exam
                  </Link>
                </div>
              ) : (
                exams.slice(0, 4).map((exam) => (
                  <div key={exam.id} className="py-2.5 flex items-center justify-between gap-2">
                    <div>
                      <p className="font-semibold text-xs text-slate-800 dark:text-slate-200 truncate">{exam.title}</p>
                      <p className="text-[11px] text-slate-400">{exam.subject_name}</p>
                    </div>
                    <span
                      className={`px-2 py-0.5 rounded-md text-[11px] font-bold shrink-0 ${
                        exam.is_urgent
                          ? 'bg-red-50 dark:bg-red-950/40 text-red-600 dark:text-red-400 border border-red-200 dark:border-red-900/40'
                          : 'bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300'
                      }`}
                    >
                      {exam.days_remaining <= 0 ? 'Today!' : `${exam.days_remaining}d left`}
                    </span>
                  </div>
                ))
              )}
            </div>
          </div>

          {/* Pending Spaced Revisions */}
          <div className="p-5 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-sm">
            <div className="flex items-center justify-between pb-3 border-b border-slate-100 dark:border-slate-800">
              <h3 className="font-bold text-sm flex items-center gap-2">
                <Repeat className="w-4 h-4 text-indigo-500" />
                <span>Spaced Revisions Due</span>
              </h3>
              <Link to="/revisions" className="text-xs text-brand-600 hover:underline font-semibold">
                All Revisions
              </Link>
            </div>

            <div className="divide-y divide-slate-100 dark:divide-slate-800 mt-2">
              {revisions.length === 0 ? (
                <p className="py-6 text-center text-xs text-slate-400">
                  All active topics are up to date! Future revisions will appear here automatically as topics are completed.
                </p>
              ) : (
                revisions.slice(0, 3).map((rev) => (
                  <div key={rev.id} className="py-2.5 flex items-center justify-between gap-2">
                    <div className="min-w-0">
                      <p className="font-semibold text-xs text-slate-800 dark:text-slate-200 truncate">{rev.topic_name}</p>
                      <p className="text-[11px] text-slate-400">
                        {rev.subject_name} • Step {rev.revision_step}
                      </p>
                    </div>
                    <button
                      onClick={() => handleCompleteRevision(rev.id)}
                      className="px-2.5 py-1 rounded-lg text-xs font-semibold bg-brand-50 dark:bg-brand-950/40 text-brand-600 hover:bg-brand-100 dark:hover:bg-brand-900/60 transition-colors shrink-0"
                    >
                      Done
                    </button>
                  </div>
                ))
              )}
            </div>
          </div>

          {/* Subject Progress Mini Overview */}
          <div className="p-5 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-sm">
            <div className="flex items-center justify-between pb-3 border-b border-slate-100 dark:border-slate-800">
              <h3 className="font-bold text-sm flex items-center gap-2">
                <BookOpen className="w-4 h-4 text-emerald-500" />
                <span>Subjects Overview</span>
              </h3>
              <Link to="/subjects" className="text-xs text-brand-600 hover:underline font-semibold">
                Manage
              </Link>
            </div>

            <div className="space-y-3 mt-3">
              {subjects.length === 0 ? (
                <div className="text-center py-4 text-xs text-slate-400">
                  <p>No subjects added yet.</p>
                  <Link to="/subjects" className="text-brand-600 font-semibold mt-1 inline-block hover:underline">
                    + Add your first subject
                  </Link>
                </div>
              ) : (
                subjects.slice(0, 4).map((subj) => (
                  <div key={subj.id} className="space-y-1">
                    <div className="flex items-center justify-between text-xs">
                      <span className="font-medium text-slate-700 dark:text-slate-300">{subj.name}</span>
                      <span className="text-slate-400 font-semibold">{subj.progress_percentage}%</span>
                    </div>
                    <div className="w-full h-1.5 rounded-full bg-slate-100 dark:bg-slate-800 overflow-hidden">
                      <div
                        className="h-full rounded-full transition-all duration-500"
                        style={{
                          width: `${subj.progress_percentage}%`,
                          backgroundColor: subj.color || '#4F46E5',
                        }}
                      />
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

