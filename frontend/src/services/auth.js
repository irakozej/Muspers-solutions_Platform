import { request, tokenStore } from './api';

async function setAccessFromResponse(data) {
  if (data?.access_token) tokenStore.set(data.access_token);
  return data;
}

export const authApi = {
  register: (payload) =>
    request('/api/auth/register', { method: 'POST', body: payload, withAuth: false })
      .then(setAccessFromResponse),

  login: (payload) =>
    request('/api/auth/login', { method: 'POST', body: payload, withAuth: false })
      .then(setAccessFromResponse),

  logout: () =>
    request('/api/auth/logout', { method: 'POST' })
      .finally(() => tokenStore.clear()),

  me: () => request('/api/auth/me'),

  refresh: () =>
    request('/api/auth/refresh', { method: 'POST', withAuth: false })
      .then(setAccessFromResponse),

  forgotPassword: (email) =>
    request('/api/auth/forgot-password', {
      method: 'POST',
      body: { email },
      withAuth: false,
    }),

  resetPassword: (token, newPassword) =>
    request('/api/auth/reset-password', {
      method: 'POST',
      body: { token, new_password: newPassword },
      withAuth: false,
    }),

  verifyEmail: (token) =>
    request('/api/auth/verify-email', {
      method: 'POST',
      body: { token },
      withAuth: false,
    }),

  updateProfile: (payload) =>
    request('/api/auth/me', { method: 'PATCH', body: payload }),

  changePassword: (currentPassword, newPassword) =>
    request('/api/auth/password', {
      method: 'PATCH',
      body: { current_password: currentPassword, new_password: newPassword },
    }),
};
