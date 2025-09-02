'use client';

import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { authApi } from '@/utils/api';
import { User, MoomooAccount } from '@/types';

interface AuthContextType {
  user: User | null;
  isLoading: boolean;
  login: (email: string, password: string) => Promise<boolean>;
  register: (userData: {
    firstName: string;
    lastName: string;
    email: string;
    password: string;
  }) => Promise<boolean>;
  logout: () => void;
  forgotPassword: (email: string) => Promise<boolean>;
  isAdmin: boolean; // Add isAdmin helper
  changePassword: (oldPassword: string, newPassword: string) => Promise<boolean>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

interface AuthProviderProps {
  children: ReactNode;
}

export const AuthProvider: React.FC<AuthProviderProps> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  // Check for existing session on mount
  useEffect(() => {
    const checkAuth = async () => {
      try {
        const token = localStorage.getItem('doppler_token');
        const storedUser = localStorage.getItem('doppler_user');
        
        if (token && storedUser) {
          // Verify token with backend
          const response = await authApi.verify();
          
          if (response.success && response.data) {
            setUser(response.data.user);
          } else {
            // Token is invalid, clear storage
            localStorage.removeItem('doppler_user');
            localStorage.removeItem('doppler_token');
          }
        }
      } catch (error) {
        console.error('Auth check failed:', error);
        // Clear storage on error
        localStorage.removeItem('doppler_user');
        localStorage.removeItem('doppler_token');
      } finally {
        setIsLoading(false);
      }
    };

    checkAuth();
  }, []);

  const login = async (email: string, password: string): Promise<boolean> => {
    try {
      setIsLoading(true);
      
      const response = await authApi.login(email, password);
      
      if (response.success && response.data) {
        setUser(response.data.user);
        localStorage.setItem('doppler_user', JSON.stringify(response.data.user));
        localStorage.setItem('doppler_token', response.data.token);
        return true;
      } else {
        console.error('Login failed:', response.error);
        return false;
      }
    } catch (error) {
      console.error('Login failed:', error);
      return false;
    } finally {
      setIsLoading(false);
    }
  };

  const register = async (userData: {
    firstName: string;
    lastName: string;
    email: string;
    password: string;
  }): Promise<boolean> => {
    try {
      setIsLoading(true);
      
      const response = await authApi.register(userData);
      
      if (response.success && response.data) {
        setUser(response.data.user);
        localStorage.setItem('doppler_user', JSON.stringify(response.data.user));
        localStorage.setItem('doppler_token', response.data.token);
        return true;
      } else {
        console.error('Registration failed:', response.error);
        return false;
      }
    } catch (error) {
      console.error('Registration failed:', error);
      return false;
    } finally {
      setIsLoading(false);
    }
  };

  const logout = () => {
    setUser(null);
    localStorage.removeItem('doppler_user');
    localStorage.removeItem('doppler_token');
  };

  const forgotPassword = async (email: string): Promise<boolean> => {
    try {
      setIsLoading(true);
      
      const response = await authApi.forgotPassword(email);
      
      if (response.success) {
        return true;
      } else {
        console.error('Password reset failed:', response.error);
        return false;
      }
    } catch (error) {
      console.error('Password reset failed:', error);
      return false;
    } finally {
      setIsLoading(false);
    }
  };

  const changePassword = async (oldPassword: string, newPassword: string): Promise<boolean> => {
    try {
      const response = await authApi.changePassword(oldPassword, newPassword);
      if (response.success) {
        return true;
      }
      console.error('Change password failed:', response.error);
      return false;
    } catch (error) {
      console.error('Change password failed:', error);
      return false;
    }
  };

  const value: AuthContextType = {
    user,
    isLoading,
    login,
    register,
    logout,
    forgotPassword,
    isAdmin: user?.isAdmin || false, // Add isAdmin helper
    changePassword,
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
}; 