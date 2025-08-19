// Auto-detect API URL based on current domain
const getApiUrl = () => {
  // In development, use the environment variable for API URL
  if (import.meta.env.VITE_API_URL) {
    return import.meta.env.VITE_API_URL;
  }
  
  if (typeof window !== 'undefined') {
    // Use the same domain as the frontend for API calls
    return window.location.origin;
  }
  
  // Fallback for server-side rendering
  return 'https://property-finder-vert-beta.vercel.app';
};

export const API_URL = getApiUrl();
