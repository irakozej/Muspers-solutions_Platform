import { request, TIMEOUTS } from './api';

export const diagnosticApi = {
  start: () =>
    request('/api/diagnostic/start', { method: 'POST', timeoutMs: TIMEOUTS.chatTurn }),
  sendMessage: (sessionId, content) =>
    request(`/api/diagnostic/${sessionId}/message`, {
      method: 'POST',
      body: { content },
      timeoutMs: TIMEOUTS.chatTurn,
    }),
  getSession: (sessionId) => request(`/api/diagnostic/${sessionId}`),
};

export const STAGE_ORDER = ['snapshot', 'scan', 'branch', 'triangulate', 'complete'];
export const STAGE_LABELS = {
  snapshot: 'Snapshot',
  scan: 'Scan',
  branch: 'Deeper questions',
  triangulate: 'Final reflections',
  complete: 'Complete',
};
