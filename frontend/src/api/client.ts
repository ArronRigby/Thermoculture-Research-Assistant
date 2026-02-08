import axios from 'axios';

const TOKEN_KEY = 'thermoculture_token';

const apiClient = axios.create({
  baseURL: '/api/v1',
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor: attach auth token
apiClient.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem(TOKEN_KEY);
    if (token) {
      console.log(`[API Request] ${config.method?.toUpperCase()} ${config.url} - Token: ${token.slice(0, 10)}...`);
      config.headers.Authorization = `Bearer ${token}`;
    } else {
      console.log(`[API Request] ${config.method?.toUpperCase()} ${config.url} - No token`);
    }
    return config;
  },
  (error) => Promise.reject(error),
);

// Response interceptor: handle 401 by clearing expired token
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      const hadToken = localStorage.getItem(TOKEN_KEY);
      localStorage.removeItem(TOKEN_KEY);
      // Only redirect if user had a token (session expired), not for unauthenticated requests
      if (
        hadToken &&
        window.location.pathname !== '/login' &&
        window.location.pathname !== '/register'
      ) {
        // Dispatch custom event so AuthProvider can react
        window.dispatchEvent(new Event('auth-unauthorized'));

        const returnTo = encodeURIComponent(window.location.pathname);
        window.location.href = `/login?returnTo=${returnTo}`;
      }
    }
    return Promise.reject(error);
  },
);

export { TOKEN_KEY };
export default apiClient;
