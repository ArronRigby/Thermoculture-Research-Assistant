import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { login as apiLogin, register as apiRegister, getCurrentUser } from '../api/endpoints';
import { TOKEN_KEY } from '../api/client';
import type { UserResponse, LoginRequest, RegisterRequest } from '../types';

interface AuthContextType {
  user: UserResponse | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;
  login: (credentials: LoginRequest) => Promise<void>;
  register: (data: RegisterRequest) => Promise<void>;
  logout: () => void;
  clearError: () => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<UserResponse | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchUser = useCallback(async () => {
    const token = localStorage.getItem(TOKEN_KEY);
    if (!token) {
      console.log('[Auth] No token found in localStorage');
      setIsLoading(false);
      return;
    }

    try {
      console.log('[Auth] Token found, fetching current user...');
      const userData = await getCurrentUser();
      console.log('[Auth] User fetched successfully:', userData.email);
      setUser(userData);
    } catch (err) {
      console.error('[Auth] Failed to fetch user:', err);
      // Only clear token if it was a 401, but the interceptor handles that.
      // Here we just ensure state is updated.
      setUser(null);
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchUser();
  }, [fetchUser]);



  const login = useCallback(async (credentials: LoginRequest) => {
    setIsLoading(true);
    setError(null);
    try {
      console.log('[Auth] Attempting login for:', credentials.username);
      const response = await apiLogin(credentials);
      localStorage.setItem(TOKEN_KEY, response.access_token);
      console.log('[Auth] Login successful, token stored');

      const userData = await getCurrentUser();
      setUser(userData);
    } catch (err: any) {
      const message = err.response?.data?.detail || err.message || 'Login failed';
      console.error('[Auth] Login error:', message);
      setError(message);
      throw err;
    } finally {
      setIsLoading(false);
    }
  }, []);

  const register = useCallback(async (data: RegisterRequest) => {
    setIsLoading(true);
    setError(null);
    try {
      await apiRegister(data);
      const loginResponse = await apiLogin({
        username: data.email,
        password: data.password,
      });
      localStorage.setItem(TOKEN_KEY, loginResponse.access_token);
      const userData = await getCurrentUser();
      setUser(userData);
    } catch (err: any) {
      const message = err.response?.data?.detail || err.message || 'Registration failed';
      setError(message);
      throw err;
    } finally {
      setIsLoading(false);
    }
  }, []);

  const logout = useCallback(() => {
    console.log('[Auth] Logging out');
    localStorage.removeItem(TOKEN_KEY);
    setUser(null);
    setError(null);
  }, []);

  useEffect(() => {
    const handleUnauthorized = () => {
      console.log('[Auth] Received unauthorized event, logging out...');
      logout();
    };
    window.addEventListener('auth-unauthorized', handleUnauthorized);
    return () => window.removeEventListener('auth-unauthorized', handleUnauthorized);
  }, [logout]);

  const clearError = useCallback(() => setError(null), []);

  console.log('[Auth] Render state:', { userEmail: user?.email, isAuthenticated: !!user, isLoading });

  return (
    <AuthContext.Provider
      value={{
        user,
        isAuthenticated: !!user,
        isLoading,
        error,
        login,
        register,
        logout,
        clearError,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
