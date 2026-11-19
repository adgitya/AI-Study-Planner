import React, { useState, useEffect } from 'react';
import { revisionAPI } from '../services/api';
import {
  Repeat,
  CheckCircle2,
  AlertTriangle,
  Clock,
  Sparkles,
  BookOpen,
  Calendar,
  Check
} from 'lucide-react';
import { useNavigate } from 'react-router-dom';

export default function Revisions() {
  const [revisions, setRevisions] = useState([]);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

  const fetchRevisions = async () => {
    setLoading(true);
    try {
      const res = await revisionAPI.getAll();
      setRevisions(res.data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchRevisions();
  }, []);

  const handleComplete = async (id) => {
    try {
      await revisionAPI.complete(id);
      fetchRevisions();
    } catch (err) {
      console.error(err);
    }
  };

  const pendingRevisions = revisions.filter((r) => r.status === 'Pending');
  const completedRevisions = revisions.filter((r) => r.status === 'Completed');

  return (
    <div className="space-y-6 max-w-5xl mx-auto">
      {/* Title */}
      <div>
        <h2 className="text-xl font-bold text-slate-900 dark:text-slate-100 flex items-center gap-2">
          <Repeat className="w-5 h-5 text-indigo-500" />
          <span>Spaced Repetition & Revision System</span>
        </h2>
        <p className="text-xs text-slate-500 dark:text-slate-400">
          Scientifically scheduled revision intervals (1d, 3d, 7d, 14d) to combat the Ebbinghaus forgetting curve
        </p>
      </div>

      {/* Science Explainer Banner */}
      <div className="p-5 rounded-2xl bg-indigo-50/60 dark:bg-indigo-950/20 border border-indigo-200/60 dark:border-indigo-800/40 text-xs text-indigo-900 dark:text-indigo-200">
        <h3 className="font-bold mb-1 flex items-center gap-1.5">
          <Sparkles className="w-4 h-4 text-indigo-600 dark:text-indigo-400" />
          <span>How Spaced Repetition Works in AI Study Planner</span>
        </h3>
        <p className="leading-relaxed">
          Whenever you complete a topic or score under 70% in a quiz, future reviews are scheduled:
          <strong> Step 1 (1 day)</strong>, <strong>Step 2 (3 days)</strong>, <strong>Step 3 (7 days)</strong>, and <strong>Step 4 (14 days)</strong>.
          Completing each step shifts the memory trace into permanent long-term storage.
        </p>
      </div>

      {/* Active Revisions */}
      <div className="space-y-3">
        <h3 className="font-bold text-sm text-slate-900 dark:text-slate-100">
          Due & Upcoming Revisions ({pendingRevisions.length})
        </h3>

        {loading ? (
          <div className="flex items-center justify-center min-h-[200px]">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-brand-600"></div>
          </div>
        ) : pendingRevisions.length === 0 ? (
          <div className="p-8 text-center rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800">
            <CheckCircle2 className="w-8 h-8 text-emerald-500 mx-auto mb-2" />
            <h4 className="font-bold text-sm">No Pending Revisions</h4>
            <p className="text-xs text-slate-400 mt-1">
              You're completely caught up! As topics are marked complete, subsequent reviews appear here automatically.
            </p>
          </div>
        ) : (
          <div className="space-y-3">
            {pendingRevisions.map((rev) => (
              <div
                key={rev.id}
                className={`p-4 rounded-2xl border transition-all ${
                  rev.is_overdue
                    ? 'bg-amber-50/50 dark:bg-amber-950/20 border-amber-300 dark:border-amber-800/80 shadow-sm'
                    : 'bg-white dark:bg-slate-900 border-slate-200 dark:border-slate-800 shadow-sm'
                }`}
              >
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                  <div className="flex items-start gap-3">
                    <div
                      className="w-2.5 h-10 rounded-full shrink-0 mt-0.5"
                      style={{ backgroundColor: rev.subject_color || '#4F46E5' }}
                    />
                    <div>
                      <div className="flex items-center gap-2">
                        <span className="text-xs font-semibold text-brand-600 dark:text-brand-400">
                          {rev.subject_name}
                        </span>
                        <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-indigo-50 dark:bg-indigo-950 text-indigo-600">
                          Step {rev.revision_step} of 4
                        </span>
                        {rev.is_overdue && (
                          <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-red-100 text-red-700 animate-pulse">
                            Overdue
                          </span>
                        )}
                      </div>
                      <h4 className="font-bold text-sm text-slate-900 dark:text-slate-100 mt-0.5">
                        {rev.topic_name}
                      </h4>
                      <p className="text-xs text-slate-400 mt-1 flex items-center gap-1.5">
                        <Calendar className="w-3.5 h-3.5" />
                        <span>Scheduled: {rev.scheduled_date}</span>
                      </p>
                    </div>
                  </div>

                  <div className="flex items-center gap-2 self-end sm:self-center">
                    <button
                      onClick={() => navigate('/quiz', { state: { subject_id: rev.subject_id, topic_id: rev.topic_id } })}
                      className="px-3 py-1.5 rounded-xl text-xs font-semibold bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300 hover:bg-slate-200"
                    >
                      Quiz Topic
                    </button>
                    <button
                      onClick={() => handleComplete(rev.id)}
                      className="px-3 py-1.5 rounded-xl text-xs font-semibold bg-emerald-600 hover:bg-emerald-700 text-white shadow-sm flex items-center gap-1.5"
                    >
                      <Check className="w-3.5 h-3.5" />
                      <span>Mark Step Completed</span>
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Completed History */}
      {completedRevisions.length > 0 && (
        <div className="space-y-3 pt-6 border-t border-slate-200 dark:border-slate-800">
          <h3 className="font-bold text-sm text-slate-900 dark:text-slate-100">
            Recently Mastered Revisions
          </h3>
          <div className="divide-y divide-slate-100 dark:divide-slate-800 bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 p-4">
            {completedRevisions.slice(0, 5).map((rev) => (
              <div key={rev.id} className="py-2.5 flex items-center justify-between text-xs">
                <div>
                  <span className="font-bold text-slate-900 dark:text-slate-100">{rev.topic_name}</span>
                  <span className="text-slate-400 ml-2">({rev.subject_name})</span>
                </div>
                <span className="text-emerald-600 font-semibold flex items-center gap-1">
                  <CheckCircle2 className="w-3.5 h-3.5" /> Step {rev.revision_step} Done
                </span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

