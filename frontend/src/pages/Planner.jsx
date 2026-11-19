import React, { useState, useEffect } from 'react';
import { plansAPI, subjectsAPI } from '../services/api';
import {
  Calendar as CalendarIcon,
  Sparkles,
  ChevronLeft,
  ChevronRight,
  Clock,
  CheckCircle2,
  AlertCircle,
  Repeat,
  BookOpen,
  Filter,
  Check,
  XCircle,
  RefreshCw
} from 'lucide-react';

export default function Planner() {
  const [viewMode, setViewMode] = useState('weekly'); // 'daily' or 'weekly'
  const [currentDate, setCurrentDate] = useState(new Date());
  const [sessions, setSessions] = useState([]);
  const [subjects, setSubjects] = useState([]);
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);
  const [aiNotes, setAiNotes] = useState([]);
  const [aiSummary, setAiSummary] = useState('');
  const [showGenModal, setShowGenModal] = useState(false);
  const [genPlanType, setGenPlanType] = useState('weekly');
  const [selectedSubjects, setSelectedSubjects] = useState([]);

  const formatDateStr = (d) => {
    const year = d.getFullYear();
    const month = String(d.getMonth() + 1).padStart(2, '0');
    const day = String(d.getDate()).padStart(2, '0');
    return `${year}-${month}-${day}`;
  };

  const fetchSchedule = async () => {
    setLoading(true);
    try {
      const dateStr = formatDateStr(currentDate);
      if (viewMode === 'daily') {
        const res = await plansAPI.getDaily(dateStr);
        setSessions(res.data);
      } else {
        const res = await plansAPI.getWeekly(dateStr);
        setSessions(res.data);
      }
    } catch (err) {
      console.error('Failed to fetch schedule:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchSchedule();
  }, [viewMode, currentDate]);

  useEffect(() => {
    subjectsAPI.getAll().then((res) => setSubjects(res.data)).catch(console.error);
  }, []);

  const handleGeneratePlan = async () => {
    setGenerating(true);
    try {
      const res = await plansAPI.generate({
        plan_type: genPlanType,
        target_date: formatDateStr(currentDate),
        focus_subject_ids: selectedSubjects.length > 0 ? selectedSubjects : null,
        regenerate: true
      });
      setAiSummary(res.data.ai_summary);
      setAiNotes(res.data.strategy_notes || []);
      setShowGenModal(false);
      fetchSchedule();
    } catch (err) {
      console.error('Failed to generate plan:', err);
    } finally {
      setGenerating(false);
    }
  };

  const handleUpdateStatus = async (sessionId, status) => {
    try {
      await plansAPI.updateSessionStatus(sessionId, { status });
      fetchSchedule();
    } catch (err) {
      console.error(err);
    }
  };

  const navigateDate = (delta) => {
    const next = new Date(currentDate);
    next.setDate(next.getDate() + (viewMode === 'weekly' ? delta * 7 : delta));
    setCurrentDate(next);
  };

  // Group sessions by day for weekly view
  const sessionsByDay = {};
  sessions.forEach((s) => {
    sessionsByDay[s.session_date] = sessionsByDay[s.session_date] || [];
    sessionsByDay[s.session_date].push(s);
  });

  return (
    <div className="space-y-6">
      {/* Top Controls Bar */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 p-4 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-sm">
        <div className="flex items-center gap-2">
          <div className="inline-flex p-1 rounded-xl bg-slate-100 dark:bg-slate-800">
            <button
              onClick={() => setViewMode('weekly')}
              className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${
                viewMode === 'weekly'
                  ? 'bg-white dark:bg-slate-700 text-brand-600 dark:text-brand-300 shadow-sm'
                  : 'text-slate-500 hover:text-slate-900 dark:hover:text-slate-100'
              }`}
            >
              Weekly Timetable
            </button>
            <button
              onClick={() => setViewMode('daily')}
              className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${
                viewMode === 'daily'
                  ? 'bg-white dark:bg-slate-700 text-brand-600 dark:text-brand-300 shadow-sm'
                  : 'text-slate-500 hover:text-slate-900 dark:hover:text-slate-100'
              }`}
            >
              Daily View
            </button>
          </div>

          <div className="flex items-center gap-1 ml-2">
            <button
              onClick={() => navigateDate(-1)}
              className="p-1.5 rounded-lg border border-slate-200 dark:border-slate-800 text-slate-500 hover:bg-slate-100 dark:hover:bg-slate-800"
            >
              <ChevronLeft className="w-4 h-4" />
            </button>
            <button
              onClick={() => setCurrentDate(new Date())}
              className="px-2.5 py-1 text-xs font-semibold rounded-lg border border-slate-200 dark:border-slate-800 hover:bg-slate-100 dark:hover:bg-slate-800"
            >
              Today
            </button>
            <button
              onClick={() => navigateDate(1)}
              className="p-1.5 rounded-lg border border-slate-200 dark:border-slate-800 text-slate-500 hover:bg-slate-100 dark:hover:bg-slate-800"
            >
              <ChevronRight className="w-4 h-4" />
            </button>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <span className="text-xs font-semibold text-slate-500">
            {currentDate.toLocaleDateString(undefined, { month: 'long', year: 'numeric' })}
          </span>
          <button
            onClick={() => setShowGenModal(true)}
            className="flex items-center gap-1.5 px-3.5 py-2 rounded-xl text-xs font-bold bg-brand-600 hover:bg-brand-700 text-white shadow-md shadow-brand-500/20 transition-all"
          >
            <Sparkles className="w-3.5 h-3.5" />
            <span>Generate Plan</span>
          </button>
        </div>
      </div>

      {/* AI Strategy Overview Box */}
      {aiSummary && (
        <div className="p-4 rounded-2xl bg-gradient-to-r from-brand-50 via-indigo-50 to-purple-50 dark:from-brand-950/30 dark:via-indigo-950/30 dark:to-purple-950/30 border border-brand-200/60 dark:border-brand-800/40">
          <div className="flex items-start gap-3">
            <div className="p-2 rounded-xl bg-brand-600 text-white shrink-0 mt-0.5">
              <Sparkles className="w-4 h-4" />
            </div>
            <div>
              <h3 className="font-bold text-xs uppercase tracking-wider text-brand-700 dark:text-brand-300">
                AI Scheduling Rationale & Strategy
              </h3>
              <p className="text-xs text-slate-700 dark:text-slate-300 mt-1 leading-relaxed">{aiSummary}</p>
              {aiNotes.length > 0 && (
                <ul className="mt-2 space-y-1 text-xs text-slate-600 dark:text-slate-400 list-disc list-inside">
                  {aiNotes.map((note, idx) => (
                    <li key={idx}>{note}</li>
                  ))}
                </ul>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Timetable / Calendar Body */}
      {loading ? (
        <div className="flex items-center justify-center min-h-[400px]">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-brand-600"></div>
        </div>
      ) : sessions.length === 0 ? (
        <div className="p-12 text-center rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800">
          <CalendarIcon className="w-10 h-10 text-slate-300 dark:text-slate-700 mx-auto mb-3" />
          <h3 className="font-bold text-sm text-slate-800 dark:text-slate-200">No Sessions Found</h3>
          <p className="text-xs text-slate-400 max-w-sm mx-auto mt-1 mb-4">
            No study sessions are scheduled for this period. Click 'Generate Plan' to create an AI-optimized schedule.
          </p>
          <button
            onClick={() => setShowGenModal(true)}
            className="px-4 py-2 rounded-xl bg-brand-600 hover:bg-brand-700 text-white text-xs font-semibold shadow-md"
          >
            Generate Study Schedule
          </button>
        </div>
      ) : viewMode === 'daily' ? (
        /* Daily View List */
        <div className="space-y-3">
          {sessions.map((session) => (
            <SessionCard key={session.id} session={session} onStatusUpdate={handleUpdateStatus} />
          ))}
        </div>
      ) : (
        /* Weekly Columns View */
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-7 gap-3">
          {Array.from({ length: 7 }).map((_, i) => {
            const dayDate = new Date(currentDate);
            dayDate.setDate(dayDate.getDate() + i);
            const dateStr = formatDateStr(dayDate);
            const isToday = dateStr === formatDateStr(new Date());
            const daySessions = sessionsByDay[dateStr] || [];

            return (
              <div
                key={dateStr}
                className={`p-3 rounded-2xl border flex flex-col min-h-[350px] ${
                  isToday
                    ? 'bg-brand-50/20 dark:bg-brand-950/10 border-brand-300 dark:border-brand-800/80 shadow-sm'
                    : 'bg-white dark:bg-slate-900 border-slate-200 dark:border-slate-800'
                }`}
              >
                {/* Day Header */}
                <div className="pb-2.5 mb-2.5 border-b border-slate-100 dark:border-slate-800 flex items-center justify-between">
                  <div>
                    <span className="text-[11px] font-bold uppercase tracking-wider text-slate-400">
                      {dayDate.toLocaleDateString(undefined, { weekday: 'short' })}
                    </span>
                    <p className={`text-sm font-extrabold ${isToday ? 'text-brand-600 dark:text-brand-400' : 'text-slate-800 dark:text-slate-200'}`}>
                      {dayDate.getDate()}
                    </p>
                  </div>
                  <span className="text-[10px] font-semibold px-2 py-0.5 rounded-full bg-slate-100 dark:bg-slate-800 text-slate-500">
                    {daySessions.length} sess
                  </span>
                </div>

                {/* Day Sessions List */}
                <div className="space-y-2 flex-1 overflow-y-auto">
                  {daySessions.length === 0 ? (
                    <div className="h-full flex items-center justify-center text-[11px] text-slate-400 italic">
                      Rest / Free
                    </div>
                  ) : (
                    daySessions.map((session) => (
                      <MiniSessionCard
                        key={session.id}
                        session={session}
                        onStatusUpdate={handleUpdateStatus}
                      />
                    ))
                  )}
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Generation Modal */}
      {showGenModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-sm">
          <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-3xl p-6 max-w-md w-full shadow-2xl">
            <div className="flex items-center gap-3 mb-4">
              <div className="p-2 rounded-xl bg-brand-600 text-white">
                <Sparkles className="w-5 h-5" />
              </div>
              <div>
                <h3 className="font-bold text-base text-slate-900 dark:text-slate-100">Generate Study Schedule</h3>
                <p className="text-xs text-slate-400">Intelligent workload distribution</p>
              </div>
            </div>

            <div className="space-y-4">
              <div>
                <label className="block text-xs font-semibold mb-1.5">Schedule Scope</label>
                <div className="grid grid-cols-2 gap-2">
                  <button
                    type="button"
                    onClick={() => setGenPlanType('weekly')}
                    className={`py-2 px-3 rounded-xl border text-xs font-semibold transition-all ${
                      genPlanType === 'weekly'
                        ? 'border-brand-500 bg-brand-50 dark:bg-brand-950/40 text-brand-600'
                        : 'border-slate-200 dark:border-slate-800'
                    }`}
                  >
                    7-Day Weekly Plan
                  </button>
                  <button
                    type="button"
                    onClick={() => setGenPlanType('daily')}
                    className={`py-2 px-3 rounded-xl border text-xs font-semibold transition-all ${
                      genPlanType === 'daily'
                        ? 'border-brand-500 bg-brand-50 dark:bg-brand-950/40 text-brand-600'
                        : 'border-slate-200 dark:border-slate-800'
                    }`}
                  >
                    1-Day Single Day
                  </button>
                </div>
              </div>

              {subjects.length > 0 && (
                <div>
                  <label className="block text-xs font-semibold mb-1.5">Filter Focus Subjects (Optional)</label>
                  <div className="max-h-36 overflow-y-auto space-y-1 p-2 rounded-xl border border-slate-200 dark:border-slate-800">
                    {subjects.map((s) => {
                      const isSelected = selectedSubjects.includes(s.id);
                      return (
                        <button
                          key={s.id}
                          type="button"
                          onClick={() => {
                            if (isSelected) {
                              setSelectedSubjects(selectedSubjects.filter((id) => id !== s.id));
                            } else {
                              setSelectedSubjects([...selectedSubjects, s.id]);
                            }
                          }}
                          className={`w-full flex items-center justify-between px-2.5 py-1.5 rounded-lg text-xs transition-colors ${
                            isSelected
                              ? 'bg-brand-50 dark:bg-brand-950/40 text-brand-600 font-semibold'
                              : 'hover:bg-slate-100 dark:hover:bg-slate-800'
                          }`}
                        >
                          <span className="truncate">{s.name}</span>
                          {isSelected && <Check className="w-3.5 h-3.5 text-brand-600" />}
                        </button>
                      );
                    })}
                  </div>
                </div>
              )}

              <p className="text-[11px] text-slate-400 bg-slate-50 dark:bg-slate-800/40 p-2.5 rounded-xl">
                The scheduler calculates topic urgency, upcoming exam proximity, and respects your daily hour limits and breaks.
              </p>

              <div className="flex items-center justify-end gap-2 pt-2">
                <button
                  type="button"
                  onClick={() => setShowGenModal(false)}
                  className="px-4 py-2 rounded-xl text-xs font-semibold text-slate-500 hover:bg-slate-100 dark:hover:bg-slate-800"
                >
                  Cancel
                </button>
                <button
                  type="button"
                  onClick={handleGeneratePlan}
                  disabled={generating}
                  className="px-4 py-2 rounded-xl text-xs font-semibold bg-brand-600 hover:bg-brand-700 text-white shadow-md shadow-brand-500/25 flex items-center gap-1.5 disabled:opacity-50"
                >
                  <Sparkles className="w-3.5 h-3.5" />
                  <span>{generating ? 'Scheduling...' : 'Run Scheduling'}</span>
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

function SessionCard({ session, onStatusUpdate }) {
  const isCompleted = session.status === 'Completed';

  return (
    <div
      className={`p-4 rounded-2xl border transition-all ${
        isCompleted
          ? 'bg-emerald-50/40 dark:bg-emerald-950/10 border-emerald-200 dark:border-emerald-800/40'
          : 'bg-white dark:bg-slate-900 border-slate-200 dark:border-slate-800 shadow-sm'
      }`}
    >
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div className="flex items-start gap-3">
          <div
            className="w-2.5 h-12 rounded-full shrink-0"
            style={{ backgroundColor: session.subject_color || '#4F46E5' }}
          />
          <div>
            <div className="flex items-center gap-2 flex-wrap">
              <span className="text-xs font-bold text-slate-800 dark:text-slate-200">
                {session.start_time} - {session.end_time} ({session.duration_minutes}m)
              </span>
              <span className="text-xs font-semibold text-brand-600 dark:text-brand-400">
                {session.subject_name}
              </span>
              <span className="text-[10px] font-semibold px-2 py-0.5 rounded-full bg-slate-100 dark:bg-slate-800">
                {session.session_type}
              </span>
              <span className="text-[10px] font-semibold px-2 py-0.5 rounded-full bg-amber-50 dark:bg-amber-950/40 text-amber-600">
                {session.priority} Priority
              </span>
            </div>
            <h4 className="font-bold text-sm text-slate-900 dark:text-slate-100 mt-1">{session.topic_name}</h4>
            {session.ai_recommendation && (
              <p className="text-xs text-slate-500 dark:text-slate-400 mt-1 flex items-center gap-1.5">
                <Sparkles className="w-3.5 h-3.5 text-amber-500 shrink-0" />
                <span>{session.ai_recommendation}</span>
              </p>
            )}
          </div>
        </div>

        <div className="flex items-center gap-2 shrink-0">
          <select
            value={session.status}
            onChange={(e) => onStatusUpdate(session.id, e.target.value)}
            className="text-xs font-semibold px-2.5 py-1.5 rounded-xl border border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-800 focus:outline-none"
          >
            <option value="Pending">Pending</option>
            <option value="Completed">Completed</option>
            <option value="Partially Completed">Partially Completed</option>
            <option value="Not Completed">Not Completed</option>
            <option value="Skipped">Skipped</option>
          </select>
        </div>
      </div>
    </div>
  );
}

function MiniSessionCard({ session, onStatusUpdate }) {
  const isCompleted = session.status === 'Completed';

  return (
    <div
      className={`p-2 rounded-xl border text-left transition-all ${
        isCompleted
          ? 'bg-emerald-50/60 dark:bg-emerald-950/20 border-emerald-300 dark:border-emerald-800/60'
          : 'bg-slate-50 dark:bg-slate-800/40 border-slate-200 dark:border-slate-700/60 hover:border-brand-400'
      }`}
    >
      <div className="flex items-center justify-between gap-1 mb-1">
        <span className="text-[10px] font-bold text-slate-500">{session.start_time}</span>
        <button
          onClick={() => onStatusUpdate(session.id, isCompleted ? 'Pending' : 'Completed')}
          className={`p-0.5 rounded ${isCompleted ? 'text-emerald-600' : 'text-slate-300 hover:text-emerald-500'}`}
        >
          <CheckCircle2 className="w-3.5 h-3.5" />
        </button>
      </div>
      <p className="font-bold text-xs truncate text-slate-900 dark:text-slate-100">{session.topic_name}</p>
      <p className="text-[10px] truncate text-brand-600 dark:text-brand-400 font-medium">{session.subject_name}</p>
    </div>
  );
}

