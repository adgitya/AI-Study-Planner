import React, { useState, useEffect } from 'react';
import { subjectsAPI, topicsAPI } from '../services/api';
import { useNavigate } from 'react-router-dom';
import {
  BookOpen,
  Plus,
  Trash2,
  Edit2,
  CheckCircle2,
  Clock,
  Sparkles,
  ChevronDown,
  ChevronRight,
  BrainCircuit,
  Filter,
  Check,
  X
} from 'lucide-react';

const COLOR_OPTIONS = [
  '#4F46E5', '#6366F1', '#8B5CF6', '#EC4899',
  '#F43F5E', '#F97316', '#EAB308', '#10B981', '#06B6D4', '#0EA5E9'
];

export default function Subjects() {
  const [subjects, setSubjects] = useState([]);
  const [topics, setTopics] = useState([]);
  const [selectedSubjectId, setSelectedSubjectId] = useState(null);
  const [loading, setLoading] = useState(true);
  const [statusFilter, setStatusFilter] = useState('ALL');
  const navigate = useNavigate();

  // Modals
  const [showSubjectModal, setShowSubjectModal] = useState(false);
  const [editingSubject, setEditingSubject] = useState(null);
  const [subjForm, setSubjForm] = useState({
    name: '',
    description: '',
    color: '#4F46E5',
    difficulty: 'Medium',
    priority: 'Medium'
  });

  const [showTopicModal, setShowTopicModal] = useState(false);
  const [editingTopic, setEditingTopic] = useState(null);
  const [topicForm, setTopicForm] = useState({
    subject_id: '',
    name: '',
    description: '',
    difficulty: 'Medium',
    estimated_time_minutes: 60,
    revision_required: false
  });

  const fetchData = async () => {
    setLoading(true);
    try {
      const [subjRes, topRes] = await Promise.all([
        subjectsAPI.getAll(),
        topicsAPI.getAll(),
      ]);
      setSubjects(subjRes.data);
      setTopics(topRes.data);
      if (subjRes.data.length > 0 && !selectedSubjectId) {
        setSelectedSubjectId(subjRes.data[0].id);
      }
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const handleSaveSubject = async (e) => {
    e.preventDefault();
    try {
      if (editingSubject) {
        await subjectsAPI.update(editingSubject.id, subjForm);
      } else {
        await subjectsAPI.create(subjForm);
      }
      setShowSubjectModal(false);
      setEditingSubject(null);
      fetchData();
    } catch (err) {
      console.error(err);
    }
  };

  const handleDeleteSubject = async (id) => {
    if (window.confirm('Are you sure you want to delete this subject? All topics and study sessions under it will be deleted.')) {
      try {
        await subjectsAPI.delete(id);
        fetchData();
      } catch (err) {
        console.error(err);
      }
    }
  };

  const handleSaveTopic = async (e) => {
    e.preventDefault();
    try {
      if (editingTopic) {
        await topicsAPI.update(editingTopic.id, {
          name: topicForm.name,
          description: topicForm.description,
          difficulty: topicForm.difficulty,
          estimated_time_minutes: parseInt(topicForm.estimated_time_minutes, 10),
          revision_required: topicForm.revision_required
        });
      } else {
        await topicsAPI.create({
          subject_id: parseInt(topicForm.subject_id, 10),
          name: topicForm.name,
          description: topicForm.description,
          difficulty: topicForm.difficulty,
          estimated_time_minutes: parseInt(topicForm.estimated_time_minutes, 10),
          revision_required: topicForm.revision_required
        });
      }
      setShowTopicModal(false);
      setEditingTopic(null);
      fetchData();
    } catch (err) {
      console.error(err);
    }
  };

  const handleDeleteTopic = async (id) => {
    if (window.confirm('Delete this topic?')) {
      try {
        await topicsAPI.delete(id);
        fetchData();
      } catch (err) {
        console.error(err);
      }
    }
  };

  const handleToggleTopicComplete = async (topic) => {
    const isNowCompleted = topic.status !== 'Completed';
    try {
      await topicsAPI.update(topic.id, {
        status: isNowCompleted ? 'Completed' : 'Pending',
        completion_percentage: isNowCompleted ? 100 : 0
      });
      fetchData();
    } catch (err) {
      console.error(err);
    }
  };

  const filteredTopics = topics.filter((t) => {
    if (selectedSubjectId && t.subject_id !== selectedSubjectId) return false;
    if (statusFilter !== 'ALL' && t.status !== statusFilter) return false;
    return true;
  });

  const activeSubject = subjects.find((s) => s.id === selectedSubjectId);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold text-slate-900 dark:text-slate-100">Academic Hierarchy</h2>
          <p className="text-xs text-slate-500 dark:text-slate-400">Manage subjects, topics, and study progress</p>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={() => {
              setEditingSubject(null);
              setSubjForm({ name: '', description: '', color: '#4F46E5', difficulty: 'Medium', priority: 'Medium' });
              setShowSubjectModal(true);
            }}
            className="flex items-center gap-1.5 px-3 py-2 rounded-xl text-xs font-semibold bg-brand-600 hover:bg-brand-700 text-white shadow-md shadow-brand-500/20"
          >
            <Plus className="w-4 h-4" />
            <span>Add Subject</span>
          </button>
          <button
            onClick={() => {
              if (subjects.length === 0) {
                alert('Please add a subject first before adding topics.');
                return;
              }
              setEditingTopic(null);
              setTopicForm({
                subject_id: selectedSubjectId || (subjects[0]?.id || ''),
                name: '',
                description: '',
                difficulty: 'Medium',
                estimated_time_minutes: 60,
                revision_required: false
              });
              setShowTopicModal(true);
            }}
            disabled={subjects.length === 0}
            className={`flex items-center gap-1.5 px-3 py-2 rounded-xl text-xs font-semibold ${
              subjects.length === 0
                ? 'bg-slate-200 dark:bg-slate-800 text-slate-400 cursor-not-allowed'
                : 'bg-slate-900 dark:bg-slate-100 text-white dark:text-slate-900 hover:opacity-90 shadow-sm'
            }`}
            title={subjects.length === 0 ? 'Create a subject first' : 'Add Topic'}
          >
            <Plus className="w-4 h-4" />
            <span>Add Topic</span>
          </button>
        </div>
      </div>

      {/* Main Two-Column Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left Column: Subjects List (4 cols) */}
        <div className="lg:col-span-4 space-y-3">
          <h3 className="text-xs font-bold uppercase tracking-wider text-slate-400 px-1">
            Enrolled Subjects ({subjects.length})
          </h3>

          {subjects.length === 0 ? (
            <div className="p-6 text-center rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800">
              <BookOpen className="w-8 h-8 text-slate-400 mx-auto mb-2" />
              <p className="text-xs text-slate-400">No subjects added yet.</p>
            </div>
          ) : (
            subjects.map((subj) => {
              const isSelected = subj.id === selectedSubjectId;
              return (
                <div
                  key={subj.id}
                  onClick={() => setSelectedSubjectId(subj.id)}
                  className={`p-4 rounded-2xl border cursor-pointer transition-all ${
                    isSelected
                      ? 'bg-white dark:bg-slate-900 border-brand-500 shadow-md ring-2 ring-brand-500/20'
                      : 'bg-white dark:bg-slate-900 border-slate-200 dark:border-slate-800 hover:border-slate-300'
                  }`}
                >
                  <div className="flex items-start justify-between gap-2">
                    <div className="flex items-center gap-2.5">
                      <div className="w-3.5 h-3.5 rounded-full shrink-0" style={{ backgroundColor: subj.color }} />
                      <h4 className="font-bold text-sm text-slate-900 dark:text-slate-100">{subj.name}</h4>
                    </div>
                    <div className="flex items-center gap-1">
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          setEditingSubject(subj);
                          setSubjForm({
                            name: subj.name,
                            description: subj.description,
                            color: subj.color,
                            difficulty: subj.difficulty,
                            priority: subj.priority
                          });
                          setShowSubjectModal(true);
                        }}
                        className="p-1 rounded text-slate-400 hover:text-slate-700 dark:hover:text-slate-200"
                      >
                        <Edit2 className="w-3.5 h-3.5" />
                      </button>
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          handleDeleteSubject(subj.id);
                        }}
                        className="p-1 rounded text-slate-400 hover:text-red-500"
                      >
                        <Trash2 className="w-3.5 h-3.5" />
                      </button>
                    </div>
                  </div>

                  <div className="flex items-center gap-2 mt-2 text-[11px] text-slate-400">
                    <span className="font-medium px-2 py-0.5 rounded-md bg-slate-100 dark:bg-slate-800">
                      {subj.difficulty}
                    </span>
                    <span className="font-medium px-2 py-0.5 rounded-md bg-slate-100 dark:bg-slate-800">
                      {subj.priority} Priority
                    </span>
                    <span className="ml-auto font-bold text-slate-600 dark:text-slate-300">
                      {subj.completed_topics_count} / {subj.topics_count} done
                    </span>
                  </div>

                  {/* Progress bar */}
                  <div className="w-full h-1.5 rounded-full bg-slate-100 dark:bg-slate-800 mt-3 overflow-hidden">
                    <div
                      className="h-full rounded-full transition-all duration-300"
                      style={{
                        width: `${subj.progress_percentage}%`,
                        backgroundColor: subj.color,
                      }}
                    />
                  </div>
                </div>
              );
            })
          )}
        </div>

        {/* Right Column: Topics List (8 cols) */}
        <div className="lg:col-span-8 space-y-4">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 p-4 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800">
            <div>
              <h3 className="text-sm font-bold text-slate-900 dark:text-slate-100">
                {activeSubject ? activeSubject.name : 'All Topics'}
              </h3>
              <p className="text-xs text-slate-400">
                {filteredTopics.length} topic(s) • Subject → Topics → Study Sessions
              </p>
            </div>

            {/* Status Filter */}
            <div className="flex items-center gap-1.5">
              {['ALL', 'Pending', 'In Progress', 'Completed'].map((st) => (
                <button
                  key={st}
                  onClick={() => setStatusFilter(st)}
                  className={`px-2.5 py-1 rounded-lg text-xs font-semibold transition-all ${
                    statusFilter === st
                      ? 'bg-brand-500 text-white shadow-sm'
                      : 'text-slate-500 hover:bg-slate-100 dark:hover:bg-slate-800'
                  }`}
                >
                  {st}
                </button>
              ))}
            </div>
          </div>

          {filteredTopics.length === 0 ? (
            <div className="p-12 text-center rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800">
              <BookOpen className="w-10 h-10 text-slate-300 dark:text-slate-700 mx-auto mb-2" />
              <h4 className="font-bold text-sm text-slate-700 dark:text-slate-300">No Topics in this Subject</h4>
              <p className="text-xs text-slate-400 mt-1 mb-4">Add individual topics to enable intelligent study scheduling.</p>
              <button
                onClick={() => {
                  setEditingTopic(null);
                  setTopicForm({
                    subject_id: selectedSubjectId || (subjects[0]?.id || ''),
                    name: '',
                    description: '',
                    difficulty: 'Medium',
                    estimated_time_minutes: 60,
                    revision_required: false
                  });
                  setShowTopicModal(true);
                }}
                className="px-4 py-2 rounded-xl bg-brand-600 hover:bg-brand-700 text-white text-xs font-semibold shadow-md"
              >
                + Add First Topic
              </button>
            </div>
          ) : (
            <div className="space-y-3">
              {filteredTopics.map((topic) => {
                const isCompleted = topic.status === 'Completed';

                return (
                  <div
                    key={topic.id}
                    className={`p-4 rounded-2xl border transition-all ${
                      isCompleted
                        ? 'bg-emerald-50/40 dark:bg-emerald-950/10 border-emerald-200 dark:border-emerald-800/40'
                        : 'bg-white dark:bg-slate-900 border-slate-200 dark:border-slate-800 shadow-sm'
                    }`}
                  >
                    <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                      <div className="flex items-start gap-3">
                        <button
                          onClick={() => handleToggleTopicComplete(topic)}
                          className={`mt-0.5 p-1 rounded-lg transition-colors ${
                            isCompleted ? 'text-emerald-600' : 'text-slate-300 hover:text-emerald-500'
                          }`}
                        >
                          <CheckCircle2 className="w-5 h-5" />
                        </button>
                        <div>
                          <div className="flex items-center gap-2 flex-wrap">
                            <h4
                              className={`font-bold text-sm ${
                                isCompleted
                                  ? 'line-through text-slate-500'
                                  : 'text-slate-900 dark:text-slate-100'
                              }`}
                            >
                              {topic.name}
                            </h4>
                            <span className="text-[10px] font-semibold px-2 py-0.5 rounded-full bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400">
                              {topic.difficulty}
                            </span>
                            {topic.revision_required && (
                              <span className="text-[10px] font-semibold px-2 py-0.5 rounded-full bg-amber-50 dark:bg-amber-950/50 text-amber-600">
                                Revision Required
                              </span>
                            )}
                          </div>
                          {topic.description && (
                            <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">{topic.description}</p>
                          )}
                          <div className="flex items-center gap-3 mt-2 text-[11px] text-slate-400">
                            <span>Est: {topic.estimated_time_minutes}m</span>
                            <span>Spent: {topic.actual_time_spent_minutes}m</span>
                            <span>Progress: {topic.completion_percentage}%</span>
                          </div>
                        </div>
                      </div>

                      <div className="flex items-center gap-2 self-end sm:self-center">
                        <button
                          onClick={() =>
                            navigate('/quiz', {
                              state: { subject_id: topic.subject_id, topic_id: topic.id }
                            })
                          }
                          className="flex items-center gap-1 px-2.5 py-1.5 rounded-xl text-xs font-semibold bg-brand-50 dark:bg-brand-950/40 text-brand-600 hover:bg-brand-100 transition-colors"
                          title="Generate Quiz on this topic"
                        >
                          <BrainCircuit className="w-3.5 h-3.5" />
                          <span>Quiz</span>
                        </button>
                        <button
                          onClick={() => {
                            setEditingTopic(topic);
                            setTopicForm({
                              subject_id: topic.subject_id,
                              name: topic.name,
                              description: topic.description,
                              difficulty: topic.difficulty,
                              estimated_time_minutes: topic.estimated_time_minutes,
                              revision_required: topic.revision_required
                            });
                            setShowTopicModal(true);
                          }}
                          className="p-1.5 rounded-lg text-slate-400 hover:text-slate-700 dark:hover:text-slate-200"
                        >
                          <Edit2 className="w-3.5 h-3.5" />
                        </button>
                        <button
                          onClick={() => handleDeleteTopic(topic.id)}
                          className="p-1.5 rounded-lg text-slate-400 hover:text-red-500"
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
        </div>
      </div>

      {/* Subject Modal */}
      {showSubjectModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-sm">
          <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-3xl p-6 max-w-md w-full shadow-2xl">
            <h3 className="font-bold text-base text-slate-900 dark:text-slate-100 mb-4">
              {editingSubject ? 'Edit Subject' : 'Add New Subject'}
            </h3>
            <form onSubmit={handleSaveSubject} className="space-y-4">
              <div>
                <label className="block text-xs font-semibold mb-1">Subject Name</label>
                <input
                  type="text"
                  required
                  value={subjForm.name}
                  onChange={(e) => setSubjForm({ ...subjForm, name: e.target.value })}
                  placeholder="e.g. Data Structures & Algorithms"
                  className="w-full px-3 py-2 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-950 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold mb-1">Description</label>
                <textarea
                  rows={2}
                  value={subjForm.description}
                  onChange={(e) => setSubjForm({ ...subjForm, description: e.target.value })}
                  placeholder="Core focus areas..."
                  className="w-full px-3 py-2 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-950 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-semibold mb-1">Difficulty</label>
                  <select
                    value={subjForm.difficulty}
                    onChange={(e) => setSubjForm({ ...subjForm, difficulty: e.target.value })}
                    className="w-full px-3 py-2 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-950 text-sm"
                  >
                    <option value="Easy">Easy</option>
                    <option value="Medium">Medium</option>
                    <option value="Hard">Hard</option>
                  </select>
                </div>
                <div>
                  <label className="block text-xs font-semibold mb-1">Priority</label>
                  <select
                    value={subjForm.priority}
                    onChange={(e) => setSubjForm({ ...subjForm, priority: e.target.value })}
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
                <label className="block text-xs font-semibold mb-1.5">Color Tag</label>
                <div className="flex items-center gap-2 flex-wrap">
                  {COLOR_OPTIONS.map((c) => (
                    <button
                      key={c}
                      type="button"
                      onClick={() => setSubjForm({ ...subjForm, color: c })}
                      className={`w-6 h-6 rounded-full transition-all ${
                        subjForm.color === c ? 'ring-2 ring-offset-2 ring-slate-900 dark:ring-white scale-110' : ''
                      }`}
                      style={{ backgroundColor: c }}
                    />
                  ))}
                </div>
              </div>

              <div className="flex items-center justify-end gap-2 pt-2">
                <button
                  type="button"
                  onClick={() => setShowSubjectModal(false)}
                  className="px-4 py-2 rounded-xl text-xs font-semibold text-slate-500 hover:bg-slate-100 dark:hover:bg-slate-800"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 rounded-xl text-xs font-semibold bg-brand-600 hover:bg-brand-700 text-white shadow-md shadow-brand-500/25"
                >
                  Save Subject
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Topic Modal */}
      {showTopicModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-sm">
          <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-3xl p-6 max-w-md w-full shadow-2xl">
            <h3 className="font-bold text-base text-slate-900 dark:text-slate-100 mb-4">
              {editingTopic ? 'Edit Topic' : 'Add Topic'}
            </h3>
            <form onSubmit={handleSaveTopic} className="space-y-4">
              {!editingTopic && (
                <div>
                  <label className="block text-xs font-semibold mb-1">Subject</label>
                  <select
                    required
                    value={topicForm.subject_id}
                    onChange={(e) => setTopicForm({ ...topicForm, subject_id: e.target.value })}
                    className="w-full px-3 py-2 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-950 text-sm"
                  >
                    {subjects.map((s) => (
                      <option key={s.id} value={s.id}>{s.name}</option>
                    ))}
                  </select>
                </div>
              )}

              <div>
                <label className="block text-xs font-semibold mb-1">Topic Name</label>
                <input
                  type="text"
                  required
                  value={topicForm.name}
                  onChange={(e) => setTopicForm({ ...topicForm, name: e.target.value })}
                  placeholder="e.g. Dynamic Programming & Memoization"
                  className="w-full px-3 py-2 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-950 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold mb-1">Description / Notes</label>
                <textarea
                  rows={2}
                  value={topicForm.description}
                  onChange={(e) => setTopicForm({ ...topicForm, description: e.target.value })}
                  placeholder="Key concepts or textbook chapters..."
                  className="w-full px-3 py-2 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-950 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-semibold mb-1">Difficulty</label>
                  <select
                    value={topicForm.difficulty}
                    onChange={(e) => setTopicForm({ ...topicForm, difficulty: e.target.value })}
                    className="w-full px-3 py-2 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-950 text-sm"
                  >
                    <option value="Easy">Easy</option>
                    <option value="Medium">Medium</option>
                    <option value="Hard">Hard</option>
                  </select>
                </div>
                <div>
                  <label className="block text-xs font-semibold mb-1">Estimated Time (Mins)</label>
                  <input
                    type="number"
                    min="15"
                    max="600"
                    step="15"
                    value={topicForm.estimated_time_minutes}
                    onChange={(e) => setTopicForm({ ...topicForm, estimated_time_minutes: e.target.value })}
                    className="w-full px-3 py-2 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-950 text-sm"
                  />
                </div>
              </div>

              <div className="flex items-center gap-2">
                <input
                  type="checkbox"
                  id="rev_req"
                  checked={topicForm.revision_required}
                  onChange={(e) => setTopicForm({ ...topicForm, revision_required: e.target.checked })}
                  className="rounded text-brand-600 focus:ring-brand-500"
                />
                <label htmlFor="rev_req" className="text-xs font-medium text-slate-700 dark:text-slate-300">
                  Mark as requiring urgent revision
                </label>
              </div>

              <div className="flex items-center justify-end gap-2 pt-2">
                <button
                  type="button"
                  onClick={() => setShowTopicModal(false)}
                  className="px-4 py-2 rounded-xl text-xs font-semibold text-slate-500 hover:bg-slate-100 dark:hover:bg-slate-800"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 rounded-xl text-xs font-semibold bg-brand-600 hover:bg-brand-700 text-white shadow-md shadow-brand-500/25"
                >
                  Save Topic
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}

