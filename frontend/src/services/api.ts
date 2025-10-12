import axios from 'axios';
import toast from 'react-hot-toast';

// API base configuration
const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

// Create axios instance
export const api = axios.create({
  baseURL: `${API_BASE_URL}/api`,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor to add auth token
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('access_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor to handle errors
api.interceptors.response.use(
  (response) => {
    return response;
  },
  (error) => {
    if (error.response?.status === 401) {
      // Unauthorized - clear token and redirect to login
      localStorage.removeItem('access_token');
      delete api.defaults.headers.common['Authorization'];
      
      // Only show toast if not already on login page
      if (!window.location.pathname.includes('/login')) {
        toast.error('Session expired. Please login again.');
        window.location.href = '/login';
      }
    } else if (error.response?.status >= 500) {
      toast.error('Server error. Please try again later.');
    } else if (error.response?.status >= 400) {
      const message = error.response?.data?.detail || 'Request failed';
      toast.error(message);
    } else if (error.code === 'ECONNABORTED') {
      toast.error('Request timeout. Please try again.');
    } else {
      toast.error('Network error. Please check your connection.');
    }
    
    return Promise.reject(error);
  }
);

// API service functions

/**
 * Authentication API functions
 */
export const authAPI = {
  /**
   * Login user
   * @param username - User's username
   * @param password - User's password
   * @returns Promise with login response
   */
  login: async (username: string, password: string) => {
    const formData = new FormData();
    formData.append('username', username);
    formData.append('password', password);
    
    const response = await api.post('/auth/login', formData, {
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
      },
    });
    return response.data;
  },

  /**
   * Get current user info
   * @returns Promise with user data
   */
  getCurrentUser: async () => {
    const response = await api.get('/auth/me');
    return response.data;
  },

  /**
   * Logout user
   * @returns Promise
   */
  logout: async () => {
    await api.post('/auth/logout');
  },
};

/**
 * License Plates API functions
 */
export const platesAPI = {
  /**
   * Get license plates list
   * @param params - Query parameters
   * @returns Promise with plates list
   */
  getPlates: async (params?: {
    skip?: number;
    limit?: number;
    is_authorized?: boolean;
    is_blacklisted?: boolean;
    country_code?: string;
  }) => {
    const response = await api.get('/plates', { params });
    return response.data;
  },

  /**
   * Get specific license plate
   * @param plateId - Plate ID
   * @returns Promise with plate data
   */
  getPlate: async (plateId: number) => {
    const response = await api.get(`/plates/${plateId}`);
    return response.data;
  },

  /**
   * Create new license plate
   * @param plateData - Plate data
   * @returns Promise with created plate
   */
  createPlate: async (plateData: any) => {
    const response = await api.post('/plates', plateData);
    return response.data;
  },

  /**
   * Update license plate
   * @param plateId - Plate ID
   * @param plateData - Updated plate data
   * @returns Promise with updated plate
   */
  updatePlate: async (plateId: number, plateData: any) => {
    const response = await api.put(`/plates/${plateId}`, plateData);
    return response.data;
  },

  /**
   * Delete license plate
   * @param plateId - Plate ID
   * @returns Promise
   */
  deletePlate: async (plateId: number) => {
    await api.delete(`/plates/${plateId}`);
  },

  /**
   * Search license plates
   * @param searchData - Search criteria
   * @returns Promise with search results
   */
  searchPlates: async (searchData: any) => {
    const response = await api.post('/plates/search', searchData);
    return response.data;
  },

  /**
   * Get plate statistics
   * @returns Promise with statistics
   */
  getPlateStats: async () => {
    const response = await api.get('/plates/stats/summary');
    return response.data;
  },

  /**
   * Get recent detections
   * @param params - Query parameters
   * @returns Promise with recent detections
   */
  getRecentDetections: async (params?: {
    limit?: number;
    hours?: number;
  }) => {
    const response = await api.get('/plates/detections/recent', { params });
    return response.data;
  },
};

/**
 * Cameras API functions
 */
export const camerasAPI = {
  /**
   * Get cameras list
   * @param params - Query parameters
   * @returns Promise with cameras list
   */
  getCameras: async (params?: {
    skip?: number;
    limit?: number;
    status?: string;
    is_enabled?: boolean;
  }) => {
    const response = await api.get('/cameras', { params });
    return response.data;
  },

  /**
   * Get specific camera
   * @param cameraId - Camera ID
   * @returns Promise with camera data
   */
  getCamera: async (cameraId: number) => {
    const response = await api.get(`/cameras/${cameraId}`);
    return response.data;
  },

  /**
   * Create new camera
   * @param cameraData - Camera data
   * @returns Promise with created camera
   */
  createCamera: async (cameraData: any) => {
    const response = await api.post('/cameras', cameraData);
    return response.data;
  },

  /**
   * Update camera
   * @param cameraId - Camera ID
   * @param cameraData - Updated camera data
   * @returns Promise with updated camera
   */
  updateCamera: async (cameraId: number, cameraData: any) => {
    const response = await api.put(`/cameras/${cameraId}`, cameraData);
    return response.data;
  },

  /**
   * Delete camera
   * @param cameraId - Camera ID
   * @returns Promise
   */
  deleteCamera: async (cameraId: number) => {
    await api.delete(`/cameras/${cameraId}`);
  },

  /**
   * Start camera
   * @param cameraId - Camera ID
   * @returns Promise
   */
  startCamera: async (cameraId: number) => {
    await api.post(`/cameras/${cameraId}/start`);
  },

  /**
   * Stop camera
   * @param cameraId - Camera ID
   * @returns Promise
   */
  stopCamera: async (cameraId: number) => {
    await api.post(`/cameras/${cameraId}/stop`);
  },

  /**
   * Get camera statistics
   * @returns Promise with statistics
   */
  getCameraStats: async () => {
    const response = await api.get('/cameras/stats/summary');
    return response.data;
  },

  /**
   * Get camera health
   * @param cameraId - Camera ID
   * @returns Promise with health data
   */
  getCameraHealth: async (cameraId: number) => {
    const response = await api.get(`/cameras/${cameraId}/health`);
    return response.data;
  },
};

/**
 * Dashboard API functions
 */
export const dashboardAPI = {
  /**
   * Get dashboard statistics
   * @returns Promise with dashboard stats
   */
  getStats: async () => {
    const response = await api.get('/dashboard/stats');
    return response.data;
  },

  /**
   * Get system health
   * @returns Promise with system health data
   */
  getSystemHealth: async () => {
    const response = await api.get('/dashboard/health');
    return response.data;
  },

  /**
   * Get recent detections
   * @param params - Query parameters
   * @returns Promise with recent detections
   */
  getRecentDetections: async (params?: {
    limit?: number;
    hours?: number;
  }) => {
    const response = await api.get('/dashboard/recent-detections', { params });
    return response.data;
  },

  /**
   * Get detection trends
   * @param params - Query parameters
   * @returns Promise with trends data
   */
  getDetectionTrends: async (params?: {
    days?: number;
  }) => {
    const response = await api.get('/dashboard/detection-trends', { params });
    return response.data;
  },

  /**
   * Get camera performance
   * @param params - Query parameters
   * @returns Promise with performance data
   */
  getCameraPerformance: async (params?: {
    camera_id?: number;
    hours?: number;
  }) => {
    const response = await api.get('/dashboard/camera-performance', { params });
    return response.data;
  },

  /**
   * Get system alerts
   * @returns Promise with alerts data
   */
  getSystemAlerts: async () => {
    const response = await api.get('/dashboard/alerts');
    return response.data;
  },
};

/**
 * Utility functions for API calls
 */
export const apiUtils = {
  /**
   * Handle API errors consistently
   * @param error - Error object
   * @param defaultMessage - Default error message
   */
  handleError: (error: any, defaultMessage: string = 'An error occurred') => {
    const message = error.response?.data?.detail || error.message || defaultMessage;
    toast.error(message);
    return message;
  },

  /**
   * Format API response data
   * @param response - API response
   * @returns Formatted data
   */
  formatResponse: (response: any) => {
    return response.data;
  },

  /**
   * Create query string from parameters
   * @param params - Parameters object
   * @returns Query string
   */
  createQueryString: (params: Record<string, any>) => {
    const searchParams = new URLSearchParams();
    Object.entries(params).forEach(([key, value]) => {
      if (value !== undefined && value !== null && value !== '') {
        searchParams.append(key, String(value));
      }
    });
    return searchParams.toString();
  },
};
