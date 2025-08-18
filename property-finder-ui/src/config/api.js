// Auto-detect API URL based on current domain
const getApiUrl = () => {
  if (typeof window !== 'undefined') {
    // Use the same domain as the frontend for API calls
    return window.location.origin;
  }
  // Fallback for server-side rendering - use the latest working deployment
  return import.meta.env.VITE_API_URL || 'https://property-finder-735t2f2g3-kens-projects-f9f968b0.vercel.app';
};

export const API_URL = getApiUrl();
