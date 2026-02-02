import axios from 'axios';
import router from '../router';

const apiClient = axios.create({
  baseURL: 'http://localhost:8000',
});

// Add a request interceptor to attach the token
apiClient.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Add a response interceptor to handle 401
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response && error.response.status === 401) {
      // Token expired or invalid
      localStorage.removeItem('token');
      // Only redirect if not already on login/register
      const currentPath = router.currentRoute.value.path;
      if (currentPath !== '/login' && currentPath !== '/register') {
          router.push('/login');
      }
    }
    return Promise.reject(error);
  }
);

export default apiClient;
