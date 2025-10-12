import React, { createContext, useContext, useState, useEffect } from 'react';
import { api } from '../services/api';
import toast from 'react-hot-toast';

// Types for authentication
interface User {
  id: number;
  username: string;
  email: string;
  role: 'admin' | 'operator' | 'viewer';
  is_active: boolean;
  created_at: string;
  last_login?: string;
}

interface AuthContextType {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (username: string, password: string) => Promise<void>;
  logout: () => void;
  updateUser: (userData: Partial<User>) => void;
}

// Create authentication context
const AuthContext = createContext<AuthContextType | undefined>(undefined);

/**
 * Authentication provider component
 * Manages user authentication state and provides auth methods
 */
export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  // Check if user is authenticated
  const isAuthenticated = !!user;

  /**
   * Initialize authentication state
   * Checks for stored token and validates it
   */
  useEffect(() => {
    const initAuth = async () => {
      try {
        const token = localStorage.getItem('access_token');
        if (token) {
          // Set token in API client
          api.defaults.headers.common['Authorization'] = `Bearer ${token}`;
          
          // Verify token and get user info
          const response = await api.get('/auth/me');
          setUser(response.data);
        }
      } catch (error) {
        // Token is invalid, remove it
        localStorage.removeItem('access_token');
        delete api.defaults.headers.common['Authorization'];
      } finally {
        setIsLoading(false);
      }
    };

    initAuth();
  }, []);

  /**
   * Login user with username and password
   * @param username - User's username
   * @param password - User's password
   */
  const login = async (username: string, password: string) => {
    try {
      setIsLoading(true);
      
      // Create form data for OAuth2 password flow
      const formData = new FormData();
      formData.append('username', username);
      formData.append('password', password);
      
      const response = await api.post('/auth/login', formData, {
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded',
        },
      });
      
      const { access_token } = response.data;
      
      // Store token
      localStorage.setItem('access_token', access_token);
      api.defaults.headers.common['Authorization'] = `Bearer ${access_token}`;
      
      // Get user info
      const userResponse = await api.get('/auth/me');
      setUser(userResponse.data);
      
      toast.success('Login successful!');
      
    } catch (error: any) {
      const message = error.response?.data?.detail || 'Login failed';
      toast.error(message);
      throw error;
    } finally {
      setIsLoading(false);
    }
  };

  /**
   * Logout user and clear authentication state
   */
  const logout = () => {
    try {
      // Call logout endpoint (optional)
      api.post('/auth/logout').catch(() => {
        // Ignore logout errors
      });
    } finally {
      // Clear local state
      localStorage.removeItem('access_token');
      delete api.defaults.headers.common['Authorization'];
      setUser(null);
      toast.success('Logged out successfully');
    }
  };

  /**
   * Update user information
   * @param userData - Partial user data to update
   */
  const updateUser = (userData: Partial<User>) => {
    if (user) {
      setUser({ ...user, ...userData });
    }
  };

  const value: AuthContextType = {
    user,
    isAuthenticated,
    isLoading,
    login,
    logout,
    updateUser,
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
}

/**
 * Hook to use authentication context
 * @returns Authentication context value
 */
export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}

/**
 * Hook to check if user has required permission
 * @param requiredRole - Required role level
 * @returns True if user has permission
 */
export function usePermission(requiredRole: 'admin' | 'operator' | 'viewer') {
  const { user } = useAuth();
  
  if (!user) return false;
  
  const roleHierarchy = {
    admin: 3,
    operator: 2,
    viewer: 1,
  };
  
  const userLevel = roleHierarchy[user.role];
  const requiredLevel = roleHierarchy[requiredRole];
  
  return userLevel >= requiredLevel;
}
