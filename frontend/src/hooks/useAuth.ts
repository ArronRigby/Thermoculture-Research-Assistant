import { useState, useEffect, useCallback } from 'react';
import { login as apiLogin, register as apiRegister, getCurrentUser } from '../api/endpoints';
import { TOKEN_KEY } from '../api/client';
import type { UserResponse, LoginRequest, RegisterRequest } from '../types';

interface UseAuthReturn {
  user: UserResponse | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;
  login: (credentials: LoginRequest) => Promise<void>;
  register: (data: RegisterRequest) => Promise<void>;
  logout: () => void;
  clearError: () => void;
}

export function useAuth(): UseAuthReturn {
  const [user, setUser] = useState<UserResponse | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const isAuthenticated = user !== null;

  // On mount, try to load the current user if a token exists
  useEffect(() => {
    const token = localStorage.getItem(TOKEN_KEY);
    if (!token) {
      setIsLoading(false);
      return;
    }

    getCurrentUser()
      .then((userData) => {
        setUser(userData);
      })
      .catch(() => {
        // Token is invalid or expired
        localStorage.removeItem(TOKEN_KEY);
        setUser(null);
      })
      .finally(() => {
        setIsLoading(false);
      });
  }, []);

  const login = useCallback(async (credentials: LoginRequest) => {
    setIsLoading(true);
    setError(null);
    try {
      const response = await apiLogin(credentials);
      localStorage.setItem(TOKEN_KEY, response.access_token);

      const userData = await getCurrentUser();
      setUser(userData);
    } catch (err: unknown) {
      const message =
        err instanceof Error ? err.message : 'Login failed. Please check your credentials.';
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
      // After successful registration, auto-login
      const loginResponse = await apiLogin({
        username: data.email,
        password: data.password,
      });
      localStorage.setItem(TOKEN_KEY, loginResponse.access_token);

      const userData = await getCurrentUser();
      setUser(userData);
    } catch (err: unknown) {
      const message =
        err instanceof Error ? err.message : 'Registration failed. Please try again.';
      setError(message);
      throw err;
    } finally {
      setIsLoading(false);
    }
  }, []);

  const logout = useCallback(() => {
    localStorage.removeItem(TOKEN_KEY);
    setUser(null);
    setError(null);
  }, []);

  const clearError = useCallback(() => {
    setError(null);
  }, []);

  return {
    user,
    isAuthenticated,
    isLoading,
    error,
    login,
    register,
    logout,
    clearError,
  };
}

export default useAuth;
