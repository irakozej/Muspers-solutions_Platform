import { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react';
import { authApi } from '../services/auth';
import { tokenStore } from '../services/api';

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [status, setStatus] = useState('initializing'); // initializing | authenticated | anonymous

  // On mount: try to silently rehydrate the session using the refresh cookie.
  useEffect(() => {
    let cancelled = false;
    const boot = async () => {
      try {
        const data = await authApi.refresh();
        if (cancelled) return;
        setUser(data?.user || null);
        setStatus(data?.user ? 'authenticated' : 'anonymous');
      } catch {
        if (cancelled) return;
        setUser(null);
        setStatus('anonymous');
      }
    };
    boot();
    tokenStore.onUnauthenticated(() => {
      setUser(null);
      setStatus('anonymous');
    });
    return () => { cancelled = true; };
  }, []);

  const login = useCallback(async (email, password, remember) => {
    const data = await authApi.login({ email, password, remember: !!remember });
    setUser(data.user);
    setStatus('authenticated');
    return data.user;
  }, []);

  const register = useCallback(async (email, password, fullName) => {
    const data = await authApi.register({ email, password, full_name: fullName });
    setUser(data.user);
    setStatus('authenticated');
    return data.user;
  }, []);

  const logout = useCallback(async () => {
    try { await authApi.logout(); } catch { /* ignore */ }
    setUser(null);
    setStatus('anonymous');
  }, []);

  const refreshUser = useCallback(async () => {
    const fresh = await authApi.me();
    setUser(fresh);
    return fresh;
  }, []);

  const updateProfile = useCallback(async (payload) => {
    const updated = await authApi.updateProfile(payload);
    setUser(updated);
    return updated;
  }, []);

  const value = useMemo(
    () => ({
      user,
      status,
      isAuthenticated: status === 'authenticated',
      isInitializing: status === 'initializing',
      login,
      register,
      logout,
      refreshUser,
      updateProfile,
    }),
    [user, status, login, register, logout, refreshUser, updateProfile],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used inside <AuthProvider>');
  return ctx;
}
