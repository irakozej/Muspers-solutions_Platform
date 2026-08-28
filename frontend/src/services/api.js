// Centralised API client.
//
// - All requests are sent with credentials so the HTTP-only refresh cookie is included.
// - Access token lives in module memory (set by AuthContext after login / refresh).
// - 401 responses on authenticated requests trigger one transparent refresh + retry.
// - Mutating requests carry the X-CSRF-Token header read from the musper_csrf cookie.
// - Every request is time-boxed. A backend that accepts the connection but never
//   answers (failed deploy, cold start, suspended DB) would otherwise leave the
//   fetch promise pending forever, and AuthProvider stuck on `initializing`.

const API_BASE = import.meta.env.VITE_API_URL || '';

// Ordinary API calls are fast; the exceptions are the ones that wait on Claude,
// so those pass their own `timeoutMs` (see TIMEOUTS below).
const DEFAULT_TIMEOUT_MS = 20_000;

export const TIMEOUTS = {
  // Session boot: keep short. A slow answer here only costs us the silent
  // rehydrate, and the user gets the login form instead of a spinner.
  boot: 8_000,
  // One chatbot turn: the backend caps its own Claude call at 45s.
  chatTurn: 75_000,
  // Report generation is a single large Claude call, capped at 120s server-side.
  report: 180_000,
};

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

function timeoutError() {
  const err = new Error('The server took too long to respond. Please try again.');
  // 0 keeps it clear of real HTTP statuses, so the 401 refresh path ignores it.
  err.status = 0;
  err.isTimeout = true;
  return err;
}

async function rawRequest(
  path,
  { method = 'GET', body, headers, withAuth = true, timeoutMs = DEFAULT_TIMEOUT_MS } = {},
) {
  let response;
  try {
    response = await fetch(`${API_BASE}${path}`, {
      method,
      credentials: 'include',
      headers: buildHeaders(method, headers, withAuth),
      body: body !== undefined ? JSON.stringify(body) : undefined,
      signal: AbortSignal.timeout(timeoutMs),
    });
  } catch (err) {
    if (err?.name === 'TimeoutError' || err?.name === 'AbortError') throw timeoutError();
    throw err;
  }
  const payload = await parseBody(response);
  if (!response.ok) throw asError(response, payload);
  return payload;
}

// The single entry point for refreshing a session. Every caller shares one
// in-flight request: the backend rotates refresh tokens on use, so two parallel
// refreshes would have the second one present an already-revoked token and get
// a 401 — signing the user straight back out. React StrictMode double-invokes
// the boot effect in dev, which makes that race fire on every page load.
export function refreshSession({ timeoutMs } = {}) {
  if (!refreshInFlight) {
    refreshInFlight = (async () => {
      try {
        const data = await rawRequest('/api/auth/refresh', {
          method: 'POST',
          withAuth: false,
          timeoutMs,
        });
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
        await refreshSession();
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

// Fetch a binary resource (e.g. a PDF) with the same auth + refresh treatment
// as `request`. Returns { blob, filename } where `filename` is parsed from the
// Content-Disposition header if present (otherwise null).
export async function fetchAttachment(
  path,
  { fallbackName = 'download', timeoutMs = TIMEOUTS.report } = {},
) {
  const doFetch = async () => {
    try {
      return await fetch(`${API_BASE}${path}`, {
        method: 'GET',
        credentials: 'include',
        headers: {
          ...(accessToken ? { Authorization: `Bearer ${accessToken}` } : {}),
        },
        signal: AbortSignal.timeout(timeoutMs),
      });
    } catch (err) {
      if (err?.name === 'TimeoutError' || err?.name === 'AbortError') throw timeoutError();
      throw err;
    }
  };

  let response = await doFetch();
  if (response.status === 401) {
    try {
      await refreshSession();
      response = await doFetch();
    } catch {
      tokenStore.clear();
      onUnauthenticated?.();
    }
  }

  if (!response.ok) {
    let payload = null;
    try { payload = await response.json(); } catch { /* binary or empty */ }
    throw asError(response, payload);
  }

  const blob = await response.blob();
  const cd = response.headers.get('content-disposition') || '';
  const match = cd.match(/filename\*?=(?:UTF-8'')?"?([^";]+)"?/i);
  const filename = match ? decodeURIComponent(match[1]) : fallbackName;
  return { blob, filename };
}

// Triggers a browser download for a fetched attachment.
export function triggerDownload(blob, filename) {
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  a.remove();
  // Free the URL after the download starts.
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}
