import React, { useState, useEffect } from 'react';
import { profileAPI } from '../services/api';
import { useAuth } from '../context/AuthContext';
import {
  Settings,
  User,
  Clock,
  Calendar,
  Sparkles,
  Save,
  CheckCircle2,
  Bell,
  Target,
  Brain
} from 'lucide-react';

const DAYS_OF_WEEK = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'];
const LEARNING_STYLES = ['Visual', 'Auditory', 'Read/Write', 'Kinesthetic'];

export default function Profile() {
  const { user, updateUser } = useAuth();
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [success, setSuccess] = useState(false);

  const [form, setForm] = useState({
    full_name: '',
    daily_study_hours: 4.0,
    preferred_start_time: '09:00',
    preferred_end_time: '21:00',
    preferred_study_days: 'Monday,Tuesday,Wednesday,Thursday,Friday,Saturday,Sunday',
    break_duration: 15,
    academic_goals: '',
    preferred_learning_style: 'Visual',
  });

  const [browserNotificationStatus, setBrowserNotificationStatus] = useState(
    typeof window !== 'undefined' && 'Notification' in window ? Notification.permission : 'unsupported'
  );

  useEffect(() => {
    profileAPI.getProfile().then((res) => {
      setForm({
        full_name: res.data.full_name || '',
        daily_study_hours: res.data.daily_study_hours || 4.0,
        preferred_start_time: res.data.preferred_start_time || '09:00',
        preferred_end_time: res.data.preferred_end_time || '21:00',
        preferred_study_days: res.data.preferred_study_days || 'Monday,Tuesday,Wednesday,Thursday,Friday,Saturday,Sunday',
        break_duration: res.data.break_duration || 15,
        academic_goals: res.data.academic_goals || '',
        preferred_learning_style: res.data.preferred_learning_style || 'Visual',
      });
    }).catch(console.error).finally(() => setLoading(false));
  }, []);

  const handleToggleDay = (day) => {
    const daysArr = form.preferred_study_days.split(',').map(d => d.trim()).filter(Boolean);
    let updated;
    if (daysArr.includes(day)) {
      if (daysArr.length === 1) {
        alert('You must have at least one study day selected.');
        return;
      }
      updated = daysArr.filter(d => d !== day);
    } else {
      updated = [...daysArr, day];
    }
    setForm({ ...form, preferred_study_days: updated.join(',') });
  };

  const handleSave = async (e) => {
    e.preventDefault();
    setSaving(true);
    setSuccess(false);

    try {
      const res = await profileAPI.updateProfile(form);
      if (user) {
        updateUser({ ...user, full_name: form.full_name });
      }
      setSuccess(true);
      setTimeout(() => setSuccess(false), 4000);
    } catch (err) {
      alert('Failed to save preferences');
    } finally {
      setSaving(false);
    }
  };

  const requestNotificationPermission = async () => {
    if ('Notification' in window) {
      const permission = await Notification.requestPermission();
      setBrowserNotificationStatus(permission);
      if (permission === 'granted') {
        new Notification('AI Study Planner', {
          body: 'Browser notifications enabled for your study sessions and upcoming exams!',
          icon: '/favicon.ico'
        });
      }
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-brand-600"></div>
      </div>
    );
  }

  const selectedDays = form.preferred_study_days.split(',').map(d => d.trim());

  return (
    <div className="space-y-6 max-w-3xl mx-auto">
      <div>
        <h2 className="text-xl font-bold text-slate-900 dark:text-slate-100 flex items-center gap-2">
          <Settings className="w-5 h-5 text-brand-600" />
          <span>Student Profile & Study Preferences</span>
        </h2>
        <p className="text-xs text-slate-500 dark:text-slate-400">
          Configure your daily capacity and study preferences to customize the scheduling engine
        </p>
      </div>

      {success && (
        <div className="p-4 rounded-2xl bg-emerald-50 dark:bg-emerald-950/40 border border-emerald-200 dark:border-emerald-800 text-xs text-emerald-800 dark:text-emerald-200 flex items-center gap-2">
          <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" />
          <span>Preferences updated successfully! Future generated study schedules will reflect these parameters.</span>
        </div>
      )}

      <form onSubmit={handleSave} className="p-6 rounded-3xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-sm space-y-6">
        {/* Personal Details */}
        <div className="space-y-4">
          <h3 className="font-bold text-sm text-slate-900 dark:text-slate-100 pb-2 border-b border-slate-100 dark:border-slate-800 flex items-center gap-2">
            <User className="w-4 h-4 text-brand-600" />
            <span>Personal Profile</span>
          </h3>

          <div>
            <label className="block text-xs font-semibold mb-1">Full Name</label>
            <input
              type="text"
              required
              value={form.full_name}
              onChange={(e) => setForm({ ...form, full_name: e.target.value })}
              className="w-full px-3.5 py-2.5 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-950 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500/40"
            />
          </div>

          <div>
            <label className="block text-xs font-semibold mb-1">Email (Account ID)</label>
            <input
              type="email"
              disabled
              value={user?.email || ''}
              className="w-full px-3.5 py-2.5 rounded-xl border border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-800/40 text-sm text-slate-500 cursor-not-allowed"
            />
          </div>
        </div>

        {/* Study Timing & Capacity */}
        <div className="space-y-4 pt-2">
          <h3 className="font-bold text-sm text-slate-900 dark:text-slate-100 pb-2 border-b border-slate-100 dark:border-slate-800 flex items-center gap-2">
            <Clock className="w-4 h-4 text-indigo-500" />
            <span>Study Availability & Limits</span>
          </h3>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-semibold mb-1">
                Daily Study Hours Limit ({form.daily_study_hours} hrs/day)
              </label>
              <input
                type="range"
                min="1.0"
                max="12.0"
                step="0.5"
                value={form.daily_study_hours}
                onChange={(e) => setForm({ ...form, daily_study_hours: parseFloat(e.target.value) })}
                className="w-full accent-brand-600"
              />
              <span className="text-[11px] text-slate-400">The planner will never exceed this daily limit.</span>
            </div>

            <div>
              <label className="block text-xs font-semibold mb-1">
                Break Duration Between Sessions ({form.break_duration} mins)
              </label>
              <input
                type="range"
                min="5"
                max="45"
                step="5"
                value={form.break_duration}
                onChange={(e) => setForm({ ...form, break_duration: parseInt(e.target.value, 10) })}
                className="w-full accent-brand-600"
              />
              <span className="text-[11px] text-slate-400">Rest intervals automatically spaced between sessions.</span>
            </div>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-semibold mb-1">Earliest Study Start Time</label>
              <input
                type="time"
                value={form.preferred_start_time}
                onChange={(e) => setForm({ ...form, preferred_start_time: e.target.value })}
                className="w-full px-3.5 py-2 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-950 text-sm"
              />
            </div>
            <div>
              <label className="block text-xs font-semibold mb-1">Latest Study End Time</label>
              <input
                type="time"
                value={form.preferred_end_time}
                onChange={(e) => setForm({ ...form, preferred_end_time: e.target.value })}
                className="w-full px-3.5 py-2 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-950 text-sm"
              />
            </div>
          </div>
        </div>

        {/* Preferred Study Days */}
        <div className="space-y-3 pt-2">
          <label className="block text-xs font-semibold">Active Study Days in Week</label>
          <div className="flex flex-wrap gap-2">
            {DAYS_OF_WEEK.map((day) => {
              const active = selectedDays.includes(day);
              return (
                <button
                  key={day}
                  type="button"
                  onClick={() => handleToggleDay(day)}
                  className={`px-3 py-1.5 rounded-xl text-xs font-semibold transition-all ${
                    active
                      ? 'bg-brand-600 text-white shadow-sm'
                      : 'bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400 hover:bg-slate-200'
                  }`}
                >
                  {day}
                </button>
              );
            })}
          </div>
        </div>

        {/* Learning Style & Goals */}
        <div className="space-y-4 pt-2">
          <h3 className="font-bold text-sm text-slate-900 dark:text-slate-100 pb-2 border-b border-slate-100 dark:border-slate-800 flex items-center gap-2">
            <Brain className="w-4 h-4 text-purple-500" />
            <span>Pedagogical Preferences</span>
          </h3>

          <div>
            <label className="block text-xs font-semibold mb-1">Preferred Learning Style</label>
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
              {LEARNING_STYLES.map((style) => (
                <button
                  key={style}
                  type="button"
                  onClick={() => setForm({ ...form, preferred_learning_style: style })}
                  className={`py-2 px-3 rounded-xl border text-xs font-semibold transition-all ${
                    form.preferred_learning_style === style
                      ? 'border-brand-500 bg-brand-50 dark:bg-brand-950/40 text-brand-600'
                      : 'border-slate-200 dark:border-slate-800 text-slate-600 dark:text-slate-400'
                  }`}
                >
                  {style}
                </button>
              ))}
            </div>
          </div>

          <div>
            <label className="block text-xs font-semibold mb-1">Short-term Academic Goals</label>
            <textarea
              rows={2}
              value={form.academic_goals}
              onChange={(e) => setForm({ ...form, academic_goals: e.target.value })}
              placeholder="e.g. Master dynamic programming, score A in Operating Systems finals..."
              className="w-full px-3.5 py-2.5 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-950 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500/40"
            />
          </div>
        </div>

        {/* Browser Notifications Permission */}
        <div className="p-4 rounded-2xl bg-slate-50 dark:bg-slate-800/40 border border-slate-200 dark:border-slate-700/60 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-xl bg-slate-200 dark:bg-slate-700 text-slate-700 dark:text-slate-200">
              <Bell className="w-4 h-4" />
            </div>
            <div>
              <p className="text-xs font-bold text-slate-900 dark:text-slate-100">Browser Push Notifications</p>
              <p className="text-[11px] text-slate-400">Receive reminders for scheduled study blocks</p>
            </div>
          </div>

          <button
            type="button"
            onClick={requestNotificationPermission}
            disabled={browserNotificationStatus === 'granted'}
            className="px-3 py-1.5 rounded-xl text-xs font-semibold border border-slate-300 dark:border-slate-600 hover:bg-white dark:hover:bg-slate-800 disabled:opacity-50"
          >
            {browserNotificationStatus === 'granted' ? 'Enabled ✓' : 'Enable Notifications'}
          </button>
        </div>

        {/* Submit */}
        <div className="pt-2 flex justify-end">
          <button
            type="submit"
            disabled={saving}
            className="px-6 py-2.5 rounded-xl bg-brand-600 hover:bg-brand-700 text-white font-semibold text-xs shadow-md shadow-brand-500/25 flex items-center gap-2 disabled:opacity-50"
          >
            <Save className="w-4 h-4" />
            <span>{saving ? 'Saving...' : 'Save Preferences'}</span>
          </button>
        </div>
      </form>
    </div>
  );
}

