// Auto-detect API URL based on current domain
const getApiUrl = () => {
  if (typeof window !== 'undefined') {
    // Use the same domain as the frontend for API calls
    return window.location.origin;
  }
  // Fallback for server-side rendering - use the stable domain
  return import.meta.env.VITE_API_URL || 'https://property-finder-vert-beta.vercel.app';
};

export const API_URL = getApiUrl();
