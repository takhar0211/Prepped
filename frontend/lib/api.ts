import axios from 'axios';

const API_URL = 'http://localhost:8000/api/';

const api = axios.create({
  baseURL: API_URL,
  withCredentials: true,
});

export const authApi = {
  signup: (data: any) => api.post('signup/', data),
  login: (data: any) => api.post('login/', data),
  logout: () => api.post('logout/'),
  getCurrentUser: () => api.get('me/'),
  getProfileStats: () => api.get('me/stats/'),
};

export const questionApi = {
  getRecommendations: () => api.get('recommendations/'),
  getQuestion: (id: number) => api.get(`question/${id}/`),
  runCode: (data: { question_id: number; code: string; language: string }) =>
    api.post('run/', data),
  submitCode: (data: { question_id: number; code: string; language: string }) =>
    api.post('submit/', data),
  interviewChat: (sessionId: number, message: string) =>
    api.post(`interview/${sessionId}/`, { message }),
  speechToText: (data: FormData) => 
    api.post('speech-to-text/', data, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    }),
};

export const mockInterviewApi = {
  generate: (data: {
    topic: string;
    subtopics: string[];
    difficulty: string;
    num_questions: number;
    time_limit: number;
  }) => api.post('mock-interview/generate/', data),
  getDetail: (mockId: number) => api.get(`mock-interview/${mockId}/`),
  update: (mockId: number, data: any) => api.patch(`mock-interview/${mockId}/`, data),
  savePerformance: (mockId: number, questionId: number, data: any) =>
    api.post(`mock-interview/${mockId}/performance/${questionId}/`, data),
  finish: (mockId: number, data: { total_time_spent: number }) =>
    api.post(`mock-interview/${mockId}/finish/`, data),
};

export default api;
