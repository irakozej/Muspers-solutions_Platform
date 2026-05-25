// Centralised API client.
//
// - All requests are sent with credentials so the HTTP-only refresh cookie is included.
// - Access token lives in module memory (set by AuthContext after login / refresh).
// - 401 responses on authenticated requests trigger one transparent refresh + retry.
// - Mutating requests carry the X-CSRF-Token header read from the musper_csrf cookie.

const API_BASE = import.meta.env.VITE_API_URL || '';

let accessToken = null;
let onUnauthenticated = null;
let refreshInFlight = null;

export const tokenStore = {
  set(token) { accessToken = token || null; },
  get() { return accessToken; },
  clear() { accessToken = null; },
  onUnauthenticated(handler) { onUnauthenticated = handler; },
};

function readCsrf() {
  if (typeof document === 'undefined') return null;
  const match = document.cookie.match(/(?:^|; )musper_csrf=([^;]+)/);
  return match ? decodeURIComponent(match[1]) : null;
}

function buildHeaders(method, headers = {}, withAuth = true) {
  const h = { 'Content-Type': 'application/json', ...headers };
  if (withAuth && accessToken) {
    h.Authorization = `Bearer ${accessToken}`;
  }
  if (method && method !== 'GET' && method !== 'HEAD') {
    const csrf = readCsrf();
    if (csrf) h['X-CSRF-Token'] = csrf;
  }
  return h;
}

async function parseBody(response) {
  if (response.status === 204) return null;
  try { return await response.json(); } catch { return null; }
}

function asError(response, payload) {
  const message =
    payload?.detail?.[0]?.msg ||
    (typeof payload?.detail === 'string' ? payload.detail : null) ||
    payload?.message ||
    `Request failed with status ${response.status}`;
  const err = new Error(message);
  err.status = response.status;
  err.payload = payload;
  return err;
}

async function rawRequest(path, { method = 'GET', body, headers, withAuth = true } = {}) {
  const response = await fetch(`${API_BASE}${path}`, {
    method,
    credentials: 'include',
    headers: buildHeaders(method, headers, withAuth),
    body: body !== undefined ? JSON.stringify(body) : undefined,
  });
  const payload = await parseBody(response);
  if (!response.ok) throw asError(response, payload);
  return payload;
}

async function refreshAccessToken() {
  if (!refreshInFlight) {
    refreshInFlight = (async () => {
      try {
        const data = await rawRequest('/api/auth/refresh', { method: 'POST', withAuth: false });
        if (data?.access_token) {
          tokenStore.set(data.access_token);
          return data;
        }
        return null;
      } finally {
        refreshInFlight = null;
      }
    })();
  }
  return refreshInFlight;
}

export async function request(path, options = {}) {
  const opts = { method: 'GET', ...options };
  try {
    return await rawRequest(path, opts);
  } catch (err) {
    // Only attempt a silent refresh for authenticated 401s; never retry the refresh endpoint itself.
    const isAuthRequest = path === '/api/auth/refresh' || path === '/api/auth/login' || path === '/api/auth/register';
    if (err.status === 401 && opts.withAuth !== false && !isAuthRequest) {
      try {
        await refreshAccessToken();
      } catch {
        tokenStore.clear();
        onUnauthenticated?.();
        throw err;
      }
      return rawRequest(path, opts);
    }
    throw err;
  }
}

export const api = {
  health: () => request('/health', { withAuth: false }),
  submitContact: (data) =>
    request('/api/contact', { method: 'POST', body: data, withAuth: false }),
};
