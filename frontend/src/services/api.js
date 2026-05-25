const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8001';

async function request(path, options = {}) {
  const response = await fetch(`${API_BASE}${path}`, {
    headers: { 'Content-Type': 'application/json', ...(options.headers || {}) },
    ...options,
  });

  let payload = null;
  try {
    payload = await response.json();
  } catch {
    // Non-JSON response (e.g. 204) — leave payload null.
  }

  if (!response.ok) {
    const message =
      payload?.detail?.[0]?.msg ||
      payload?.detail ||
      `Request failed with status ${response.status}`;
    const error = new Error(typeof message === 'string' ? message : 'Request failed');
    error.status = response.status;
    error.payload = payload;
    throw error;
  }

  return payload;
}

export const api = {
  health: () => request('/health'),
  submitContact: (data) =>
    request('/api/contact', { method: 'POST', body: JSON.stringify(data) }),
};
