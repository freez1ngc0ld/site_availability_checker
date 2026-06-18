import axios from 'axios';

const API = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8000', 
});

API.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

export const authAPI = {
  register: (email, password) => API.post('/auth/registration', { email, password }),
  
  login: (email, password) => {
    const formData = new URLSearchParams();
    formData.append('username', email);
    formData.append('password', password);
    return API.post('/auth/login', formData, {
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' }
    });
  },
  
  verificate: (token) => API.post('/auth/verificate', { access_token: token }),
  
  resetPasswordRequest: (email) => API.patch('/auth/reset-password/request', { email }),
  
  resetPasswordConfirm: (token, newPassword) => 
    API.patch('/auth/reset-password/confirm', { access_token: token, new_password: newPassword }),
    
  deleteAccountRequest: () => API.delete('/auth/delete-account/request'),
  
  deleteAccountConfirm: (otp, token) => 
    API.delete('/auth/delete-account/confirm', { data: { one_time_password: otp, access_token: token } }),
    
  getGoogleUrl: () => API.get('/auth/google/url'),
  
  googleLogin: (code) => API.post(`/auth/google/login?code=${code}`),
};

export const checkerAPI = {
  getAll: (limit, offset) => API.get(`/site_checkers?limit=${limit}&offset=${offset}`),
  add: (url) => API.post(`/site_checkers?site_url=${encodeURIComponent(url)}`),
  delete: (id) => API.delete(`/site_checkers/${id}`),
  getLogs: (id) => API.get(`/site_checkers/${id}/logs`),
};

export const apiKeyAPI = {
  getAll: ({ limit = 10, offset = 0 } = {}) => 
    API.get(`/api_keys?limit=${limit}&offset=${offset}`),
    
  create: () => 
    API.post('/api_keys'),
    
  delete: (key) => 
    API.delete(`/api_keys/${key}`),
};
export default API;