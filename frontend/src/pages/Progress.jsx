import React, { useState, useEffect } from 'react';
import { progressAPI } from '../services/api';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
  LineChart,
  Line,
  AreaChart,
  Area
} from 'recharts';
import {
  BarChart3,
  Flame,
  Clock,
  CheckCircle2,
  TrendingUp,
  Percent,
  Calendar,
  AlertCircle
} from 'lucide-react';
import { useTheme } from '../context/ThemeContext';

export default function Progress() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const { theme } = useTheme();

  useEffect(() => {
    progressAPI.getOverview()
      .then((res) => setData(res.data))
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-brand-600"></div>
      </div>
    );
  }

  if (!data) return null;

  const isDark = theme === 'dark';
  const gridColor = isDark ? '#1e293b' : '#f1f5f9';
  const textColor = isDark ? '#94a3b8' : '#64748b';

  const hasData = (data.total_study_hours > 0) || (data.total_topics > 0);

  return (
    <div className="space-y-6">
      {/* Title */}
      <div>
        <h2 className="text-xl font-bold text-slate-900 dark:text-slate-100">Progress & Productivity Analytics</h2>
        <p className="text-xs text-slate-500 dark:text-slate-400">
          Real-time metrics calculated from your actual logged study sessions and topics
        </p>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="p-4 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-sm">
          <div className="flex items-center justify-between text-slate-500 dark:text-slate-400">
            <span className="text-xs font-semibold uppercase tracking-wider">Total Studied</span>
            <div className="p-2 rounded-xl bg-brand-50 dark:bg-brand-950/50 text-brand-600">
              <Clock className="w-4 h-4" />
            </div>
          </div>
          <p className="text-2xl font-bold text-slate-900 dark:text-slate-100 mt-2">
            {data.total_study_hours} <span className="text-sm font-normal text-slate-500">hrs</span>
          </p>
          <p className="text-xs text-slate-400 mt-1">Today: {data.daily_study_hours} hrs</p>
        </div>

        <div className="p-4 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-sm">
          <div className="flex items-center justify-between text-slate-500 dark:text-slate-400">
            <span className="text-xs font-semibold uppercase tracking-wider">Consistency Streak</span>
            <div className="p-2 rounded-xl bg-orange-50 dark:bg-orange-950/50 text-orange-500">
              <Flame className="w-4 h-4" />
            </div>
          </div>
          <p className="text-2xl font-bold text-slate-900 dark:text-slate-100 mt-2">
            {data.current_streak_days} <span className="text-sm font-normal text-slate-500">days</span>
          </p>
          <p className="text-xs text-slate-400 mt-1">Consecutive study days</p>
        </div>

        <div className="p-4 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-sm">
          <div className="flex items-center justify-between text-slate-500 dark:text-slate-400">
            <span className="text-xs font-semibold uppercase tracking-wider">Topics Mastered</span>
            <div className="p-2 rounded-xl bg-emerald-50 dark:bg-emerald-950/50 text-emerald-500">
              <CheckCircle2 className="w-4 h-4" />
            </div>
          </div>
          <p className="text-2xl font-bold text-slate-900 dark:text-slate-100 mt-2">
            {data.completed_topics} <span className="text-sm font-normal text-slate-500">/ {data.total_topics}</span>
          </p>
          <p className="text-xs text-slate-400 mt-1">{data.pending_topics} topics remaining</p>
        </div>

        <div className="p-4 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-sm">
          <div className="flex items-center justify-between text-slate-500 dark:text-slate-400">
            <span className="text-xs font-semibold uppercase tracking-wider">Plan Adherence</span>
            <div className="p-2 rounded-xl bg-indigo-50 dark:bg-indigo-950/50 text-indigo-500">
              <TrendingUp className="w-4 h-4" />
            </div>
          </div>
          <p className="text-2xl font-bold text-slate-900 dark:text-slate-100 mt-2">
            {data.planned_vs_actual_hours?.efficiency_rate || 100}%
          </p>
          <p className="text-xs text-slate-400 mt-1">
            {data.planned_vs_actual_hours?.actual_hours || 0}h actual vs {data.planned_vs_actual_hours?.planned_hours || 0}h planned
          </p>
        </div>
      </div>

      {!hasData ? (
        <div className="p-12 text-center rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800">
          <BarChart3 className="w-12 h-12 text-slate-300 dark:text-slate-700 mx-auto mb-3" />
          <h3 className="font-bold text-base text-slate-800 dark:text-slate-200">No Study Data Recorded Yet</h3>
          <p className="text-xs text-slate-400 max-w-sm mx-auto mt-1">
            As you schedule and mark study sessions as completed, interactive charts for weekly hours, subject breakdowns, and task distributions will populate here.
          </p>
        </div>
      ) : (
        <>
          {/* Charts Row 1: Weekly Hours & Task Status */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Weekly Study Hours (Planned vs Actual) */}
            <div className="lg:col-span-2 p-5 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-sm">
              <div className="flex items-center justify-between mb-4">
                <h3 className="font-bold text-sm text-slate-900 dark:text-slate-100">
                  Weekly Study Hours (Planned vs Actual)
                </h3>
                <span className="text-xs text-slate-400">Past 7 Days</span>
              </div>
              <div className="h-64 w-full">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={data.weekly_hours_by_day}>
                    <CartesianGrid strokeDasharray="3 3" stroke={gridColor} />
                    <XAxis dataKey="day" stroke={textColor} fontSize={12} />
                    <YAxis stroke={textColor} fontSize={12} unit="h" />
                    <Tooltip
                      contentStyle={{
                        backgroundColor: isDark ? '#0f172a' : '#ffffff',
                        borderColor: isDark ? '#334155' : '#e2e8f0',
                        borderRadius: '0.75rem',
                        fontSize: '12px'
                      }}
                    />
                    <Legend wrapperStyle={{ fontSize: '12px' }} />
                    <Bar dataKey="planned" fill="#818cf8" radius={[4, 4, 0, 0]} name="Planned (h)" />
                    <Bar dataKey="actual" fill="#4f46e5" radius={[4, 4, 0, 0]} name="Actual (h)" />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </div>

            {/* Task Status Distribution */}
            <div className="p-5 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-sm">
              <h3 className="font-bold text-sm text-slate-900 dark:text-slate-100 mb-4">
                Session Status Distribution
              </h3>
              <div className="h-64 w-full flex items-center justify-center">
                <ResponsiveContainer width="100%" height="100%">
                  <PieChart>
                    <Pie
                      data={data.task_status_distribution.filter(d => d.value > 0)}
                      cx="50%"
                      cy="50%"
                      innerRadius={50}
                      outerRadius={80}
                      paddingAngle={4}
                      dataKey="value"
                    >
                      {data.task_status_distribution.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={entry.color} />
                      ))}
                    </Pie>
                    <Tooltip
                      contentStyle={{
                        backgroundColor: isDark ? '#0f172a' : '#ffffff',
                        borderColor: isDark ? '#334155' : '#e2e8f0',
                        borderRadius: '0.75rem',
                        fontSize: '12px'
                      }}
                    />
                    <Legend wrapperStyle={{ fontSize: '11px' }} />
                  </PieChart>
                </ResponsiveContainer>
              </div>
            </div>
          </div>

          {/* Charts Row 2: Subject Progress & 14-Day Productivity Trend */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Subject-Wise Progress Bar Chart */}
            <div className="p-5 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-sm">
              <h3 className="font-bold text-sm text-slate-900 dark:text-slate-100 mb-4">
                Subject-Wise Completion Percentage
              </h3>
              <div className="h-64 w-full">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={data.subject_progress} layout="vertical">
                    <CartesianGrid strokeDasharray="3 3" stroke={gridColor} />
                    <XAxis type="number" domain={[0, 100]} stroke={textColor} fontSize={12} unit="%" />
                    <YAxis dataKey="subject" type="category" stroke={textColor} fontSize={11} width={90} />
                    <Tooltip
                      contentStyle={{
                        backgroundColor: isDark ? '#0f172a' : '#ffffff',
                        borderColor: isDark ? '#334155' : '#e2e8f0',
                        borderRadius: '0.75rem',
                        fontSize: '12px'
                      }}
                      formatter={(val) => [`${val}%`, 'Progress']}
                    />
                    <Bar dataKey="progress" fill="#10b981" radius={[0, 4, 4, 0]} name="Progress %" />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </div>

            {/* 14-Day Productivity Trend Area Chart */}
            <div className="p-5 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-sm">
              <h3 className="font-bold text-sm text-slate-900 dark:text-slate-100 mb-4">
                Daily Productivity Trend (Last 14 Days)
              </h3>
              <div className="h-64 w-full">
                <ResponsiveContainer width="100%" height="100%">
                  <AreaChart data={data.productivity_trend}>
                    <defs>
                      <linearGradient id="colorHours" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor="#6366f1" stopOpacity={0.4}/>
                        <stop offset="95%" stopColor="#6366f1" stopOpacity={0}/>
                      </linearGradient>
                    </defs>
                    <CartesianGrid strokeDasharray="3 3" stroke={gridColor} />
                    <XAxis dataKey="date" stroke={textColor} fontSize={11} />
                    <YAxis stroke={textColor} fontSize={12} unit="h" />
                    <Tooltip
                      contentStyle={{
                        backgroundColor: isDark ? '#0f172a' : '#ffffff',
                        borderColor: isDark ? '#334155' : '#e2e8f0',
                        borderRadius: '0.75rem',
                        fontSize: '12px'
                      }}
                    />
                    <Area type="monotone" dataKey="hours" stroke="#4f46e5" strokeWidth={2} fillOpacity={1} fill="url(#colorHours)" name="Study Hours" />
                  </AreaChart>
                </ResponsiveContainer>
              </div>
            </div>
          </div>
        </>
      )}
    </div>
  );
}

