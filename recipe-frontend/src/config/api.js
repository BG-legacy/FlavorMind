// Base URL for the API
export const API_URL = process.env.REACT_APP_API_URL || (
  process.env.NODE_ENV === 'production'
    ? 'https://recipe-backend-577481829789.us-central1.run.app'
    : 'http://localhost:5001'
);

// API endpoints
export const API_ENDPOINTS = {
  SAVED_RECIPES: '/api/user/saved-recipes',
  USER_PROFILE: '/api/user/profile',
  GENERATE_RECIPE: '/generate-recipe'
};

// Helper function to build full API URLs
export const buildApiUrl = (endpoint) => `${API_URL}${endpoint}`;

// Export API_URL as default for backward compatibility
export default API_URL;
