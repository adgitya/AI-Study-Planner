import React, { useState, useEffect } from 'react';
import { examsAPI, subjectsAPI, plansAPI } from '../services/api';
import {
  GraduationCap,
  Plus,
  Trash2,
  Edit2,
  Calendar,
  AlertTriangle,
  Clock,
  Sparkles,
  BookOpen,
  ArrowRight
} from 'lucide-react';
import { useNavigate } from 'react-router-dom';

export default function Examinations() {
  const [exams, setExams] = useState([]);
  const [subjects, setSubjects] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [editingExam, setEditingExam] = useState(null);
  const navigate = useNavigate();

  const [form, setForm] = useState({
    subject_id: '',
    title: '',
    exam_date: '',
    priority: 'High',
    notes: ''
  });

  const fetchData = async () => {
    setLoading(true);
    try {
      const [examRes, subjRes] = await Promise.all([
        examsAPI.getAll(),
        subjectsAPI.getAll()
      ]);
      setExams(examRes.data);
      setSubjects(subjRes.data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const handleSave = async (e) => {
    e.preventDefault();
    try {
      const payload = {
        subject_id: parseInt(form.subject_id, 10),
        title: form.title,
        exam_date: new Date(form.exam_date).toISOString(),
        priority: form.priority,
        notes: form.notes
      };

      if (editingExam) {
        await examsAPI.update(editingExam.id, payload);
      } else {
        await examsAPI.create(payload);
      }
      setShowModal(false);
      setEditingExam(null);
      fetchData();
    } catch (err) {
      console.error(err);
    }
  };

  const handleDelete = async (id) => {
    if (window.confirm('Delete this examination?')) {
      try {
        await examsAPI.delete(id);
        fetchData();
      } catch (err) {
        console.error(err);
      }
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold text-slate-900 dark:text-slate-100">Examination Deadlines</h2>
          <p className="text-xs text-slate-500 dark:text-slate-400">
            Track exam schedules and automatically prioritize approaching subjects
          </p>
        </div>
        <button
          onClick={() => {
            setEditingExam(null);
            setForm({
              subject_id: subjects[0]?.id || '',
              title: '',
              exam_date: '',
              priority: 'High',
              notes: ''
            });
            setShowModal(true);
          }}
          disabled={subjects.length === 0}
          className="flex items-center gap-1.5 px-3.5 py-2 rounded-xl text-xs font-semibold bg-brand-600 hover:bg-brand-700 text-white shadow-md shadow-brand-500/20 disabled:opacity-50"
        >
          <Plus className="w-4 h-4" />
          <span>Add Examination</span>
        </button>
      </div>

      {subjects.length === 0 && (
        <div className="p-4 rounded-2xl bg-amber-50 dark:bg-amber-950/30 border border-amber-200 dark:border-amber-800 text-xs text-amber-800 dark:text-amber-200 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <AlertTriangle className="w-4 h-4 text-amber-600 shrink-0" />
            <span>You need at least one subject registered before adding an examination.</span>
          </div>
          <button
            onClick={() => navigate('/subjects')}
            className="font-bold underline hover:opacity-80"
          >
            Create Subject →
          </button>
        </div>
      )}

      {loading ? (
        <div className="flex items-center justify-center min-h-[300px]">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-brand-600"></div>
        </div>
      ) : exams.length === 0 ? (
        <div className="p-12 text-center rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800">
          <GraduationCap className="w-10 h-10 text-slate-300 dark:text-slate-700 mx-auto mb-2" />
          <h3 className="font-bold text-sm text-slate-800 dark:text-slate-200">No Examinations Scheduled</h3>
          <p className="text-xs text-slate-400 max-w-sm mx-auto mt-1 mb-4">
            Add your upcoming midterms, finals, or entrance tests to allow the AI to sequence your study sessions accordingly.
          </p>
          <button
            onClick={() => {
              setEditingExam(null);
              setForm({
                subject_id: subjects[0]?.id || '',
                title: '',
                exam_date: '',
                priority: 'High',
                notes: ''
              });
              setShowModal(true);
            }}
            disabled={subjects.length === 0}
            className="px-4 py-2 rounded-xl bg-brand-600 hover:bg-brand-700 text-white text-xs font-semibold shadow-md disabled:opacity-50"
          >
            Schedule Examination
          </button>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {exams.map((exam) => {
            const isCritical = exam.days_remaining <= 3 && exam.days_remaining >= 0;
            const isUrgent = exam.days_remaining <= 7 && exam.days_remaining > 3;

            return (
              <div
                key={exam.id}
                className={`p-5 rounded-2xl border transition-all ${
                  isCritical
                    ? 'bg-red-50/40 dark:bg-red-950/15 border-red-200 dark:border-red-900/60 shadow-sm'
                    : isUrgent
                    ? 'bg-amber-50/40 dark:bg-amber-950/15 border-amber-200 dark:border-amber-900/60 shadow-sm'
                    : 'bg-white dark:bg-slate-900 border-slate-200 dark:border-slate-800 shadow-sm hover:shadow-md'
                }`}
              >
                <div className="flex items-start justify-between gap-2 mb-3">
                  <div className="flex items-center gap-2">
                    <div
                      className="w-3 h-3 rounded-full shrink-0"
                      style={{ backgroundColor: exam.subject_color || '#4F46E5' }}
                    />
                    <span className="text-xs font-semibold text-slate-500 dark:text-slate-400">
                      {exam.subject_name}
                    </span>
                  </div>

                  <span
                    className={`px-2.5 py-0.5 rounded-full text-[11px] font-bold ${
                      isCritical
                        ? 'bg-red-100 dark:bg-red-950 text-red-700 dark:text-red-400 animate-pulse'
                        : isUrgent
                        ? 'bg-amber-100 dark:bg-amber-950 text-amber-700 dark:text-amber-400'
                        : 'bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400'
                    }`}
                  >
                    {exam.days_remaining < 0
                      ? 'Concluded'
                      : exam.days_remaining === 0
                      ? 'TODAY'
                      : `${exam.days_remaining} Days Remaining`}
                  </span>
                </div>

                <h3 className="font-bold text-base text-slate-900 dark:text-slate-100 mb-1">{exam.title}</h3>
                {exam.notes && <p className="text-xs text-slate-500 dark:text-slate-400 mb-3">{exam.notes}</p>}

                <div className="pt-3 border-t border-slate-100 dark:border-slate-800 flex items-center justify-between text-xs text-slate-400">
                  <div className="flex items-center gap-1.5 font-medium">
                    <Calendar className="w-3.5 h-3.5" />
                    <span>{new Date(exam.exam_date).toLocaleDateString(undefined, { month: 'short', day: 'numeric', year: 'numeric' })}</span>
                  </div>

                  <div className="flex items-center gap-1">
                    <button
                      onClick={() => {
                        setEditingExam(exam);
                        setForm({
                          subject_id: exam.subject_id,
                          title: exam.title,
                          exam_date: exam.exam_date.slice(0, 16),
                          priority: exam.priority,
                          notes: exam.notes
                        });
                        setShowModal(true);
                      }}
                      className="p-1 rounded text-slate-400 hover:text-slate-700 dark:hover:text-slate-200"
                    >
                      <Edit2 className="w-3.5 h-3.5" />
                    </button>
                    <button
                      onClick={() => handleDelete(exam.id)}
                      className="p-1 rounded text-slate-400 hover:text-red-500"
                    >
                      <Trash2 className="w-3.5 h-3.5" />
                    </button>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Modal */}
      {showModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-sm">
          <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-3xl p-6 max-w-md w-full shadow-2xl">
            <h3 className="font-bold text-base text-slate-900 dark:text-slate-100 mb-4">
              {editingExam ? 'Edit Examination' : 'Add Upcoming Examination'}
            </h3>

            <form onSubmit={handleSave} className="space-y-4">
              <div>
                <label className="block text-xs font-semibold mb-1">Associated Subject</label>
                <select
                  required
                  value={form.subject_id}
                  onChange={(e) => setForm({ ...form, subject_id: e.target.value })}
                  className="w-full px-3 py-2 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-950 text-sm"
                >
                  {subjects.map((s) => (
                    <option key={s.id} value={s.id}>{s.name}</option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-xs font-semibold mb-1">Examination Title</label>
                <input
                  type="text"
                  required
                  value={form.title}
                  onChange={(e) => setForm({ ...form, title: e.target.value })}
                  placeholder="e.g. End Semester Theory Examination"
                  className="w-full px-3 py-2 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-950 text-sm"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-semibold mb-1">Exam Date & Time</label>
                  <input
                    type="datetime-local"
                    required
                    value={form.exam_date}
                    onChange={(e) => setForm({ ...form, exam_date: e.target.value })}
                    className="w-full px-3 py-2 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-950 text-xs"
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold mb-1">Priority</label>
                  <select
                    value={form.priority}
                    onChange={(e) => setForm({ ...form, priority: e.target.value })}
                    className="w-full px-3 py-2 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-950 text-sm"
                  >
                    <option value="Low">Low</option>
                    <option value="Medium">Medium</option>
                    <option value="High">High</option>
                    <option value="Urgent">Urgent</option>
                  </select>
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold mb-1">Notes / Syllabus Reference</label>
                <textarea
                  rows={2}
                  value={form.notes}
                  onChange={(e) => setForm({ ...form, notes: e.target.value })}
                  placeholder="Important chapters, question weightage..."
                  className="w-full px-3 py-2 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-950 text-sm"
                />
              </div>

              <div className="flex items-center justify-end gap-2 pt-2">
                <button
                  type="button"
                  onClick={() => setShowModal(false)}
                  className="px-4 py-2 rounded-xl text-xs font-semibold text-slate-500 hover:bg-slate-100 dark:hover:bg-slate-800"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 rounded-xl text-xs font-semibold bg-brand-600 hover:bg-brand-700 text-white shadow-md shadow-brand-500/25"
                >
                  Save Examination
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}

