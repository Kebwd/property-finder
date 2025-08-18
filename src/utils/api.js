// API configuration for different environments
const getApiUrl = () => {
  // In production (Vercel), use the same domain for API calls
  if (import.meta.env.PROD) {
    return import.meta.env.VITE_API_URL || '/api';
  }
  
  // In development, use environment variable or fallback to localhost
  return import.meta.env.VITE_API_URL || 'http://localhost:5000/api';
};

export const API_BASE_URL = getApiUrl();

// API endpoints
export const API_ENDPOINTS = {
  HEALTH: `${API_BASE_URL}/health`,
  SEARCH: `${API_BASE_URL}/search`,
  HOUSES: `${API_BASE_URL}/house`,
  BUSINESSES: `${API_BASE_URL}/business`,
  EXPORT: `${API_BASE_URL}/export`,
  SCRAPER: {
    START: `${API_BASE_URL}/scraper/start`,
    STATUS: `${API_BASE_URL}/scraper/status`
  }
};

// API helper functions
export const apiRequest = async (url, options = {}) => {
  const response = await fetch(url, {
    headers: {
      'Content-Type': 'application/json',
      ...options.headers
    },
    ...options
  });

  if (!response.ok) {
    throw new Error(`API request failed: ${response.status} ${response.statusText}`);
  }

  return response.json();
};

export const apiGet = (url) => apiRequest(url);
export const apiPost = (url, data) => apiRequest(url, {
  method: 'POST',
  body: JSON.stringify(data)
});
export const apiPut = (url, data) => apiRequest(url, {
  method: 'PUT',
  body: JSON.stringify(data)
});
export const apiDelete = (url) => apiRequest(url, { method: 'DELETE' });
