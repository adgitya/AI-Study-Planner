import axios from 'axios';

const api = axios.create({
  baseURL: '/api/v1',
  headers: {
    'Content-Type': 'application/json',
  },
});

// Attach JWT token to requests if present
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token');
    if (token) {
      config.headers['Authorization'] = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Intercept 401s
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response && error.response.status === 401) {
      // Don't auto-redirect on login/register failures
      const url = error.config?.url || '';
      if (!url.includes('/auth/login') && !url.includes('/auth/register')) {
        localStorage.removeItem('token');
        localStorage.removeItem('user');
        window.location.href = '/login';
      }
    }
    return Promise.reject(error);
  }
);

export const authAPI = {
  register: (data) => api.post('/auth/register', data),
  login: (data) => api.post('/auth/login', data),
  getMe: () => api.get('/auth/me'),
};

export const profileAPI = {
  getProfile: () => api.get('/profile'),
  updateProfile: (data) => api.put('/profile', data),
};

export const subjectsAPI = {
  getAll: () => api.get('/subjects'),
  getDetail: (id) => api.get(`/subjects/${id}`),
  create: (data) => api.post('/subjects', data),
  update: (id, data) => api.put(`/subjects/${id}`, data),
  delete: (id) => api.delete(`/subjects/${id}`),
};

export const topicsAPI = {
  getAll: (subjectId, status) => {
    let url = '/topics';
    const params = new URLSearchParams();
    if (subjectId) params.append('subject_id', subjectId);
    if (status) params.append('status_filter', status);
    if (params.toString()) url += `?${params.toString()}`;
    return api.get(url);
  },
  create: (data) => api.post('/topics', data),
  get: (id) => api.get(`/topics/${id}`),
  update: (id, data) => api.put(`/topics/${id}`, data),
  delete: (id) => api.delete(`/topics/${id}`),
};

export const examsAPI = {
  getAll: () => api.get('/exams'),
  create: (data) => api.post('/exams', data),
  update: (id, data) => api.put(`/exams/${id}`, data),
  delete: (id) => api.delete(`/exams/${id}`),
};

export const plansAPI = {
  generate: (data) => api.post('/plans/generate', data),
  getDaily: (targetDate) => api.get(`/plans/daily${targetDate ? `?target_date=${targetDate}` : ''}`),
  getWeekly: (startDate) => api.get(`/plans/weekly${startDate ? `?start_date_str=${startDate}` : ''}`),
  adjust: (data) => api.post('/plans/adjust', data),
  updateSessionStatus: (id, data) => api.put(`/sessions/${id}/status`, data),
};

export const progressAPI = {
  getOverview: () => api.get('/progress'),
};

export const aiAPI = {
  chat: (data) => api.post('/ai/chat', data),
  getStatus: () => api.get('/ai/status'),
  getConversations: () => api.get('/ai/conversations'),
  clearConversation: (id) => api.delete(`/ai/conversations/${id}`),
  generateQuiz: (data) => api.post('/ai/generate-quiz', data),
  submitQuiz: (data) => api.post('/ai/submit-quiz', data),
  getQuizHistory: () => api.get('/ai/quiz-history'),
};

export const revisionAPI = {
  getAll: () => api.get('/revision'),
  complete: (id, data) => api.post(`/revision/${id}/complete`, data || {}),
};

export const notificationsAPI = {
  getAll: () => api.get('/notifications'),
  markRead: (id) => api.put(`/notifications/${id}/read`),
  markAllRead: () => api.put('/notifications/read-all/mark'),
};

export default api;

