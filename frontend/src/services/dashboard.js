import { request, fetchAttachment, triggerDownload, TIMEOUTS } from './api';

async function downloadPdf(path, fallback) {
  const { blob, filename } = await fetchAttachment(path, { fallbackName: fallback });
  triggerDownload(blob, filename);
  return filename;
}

export const advisorApi = {
  stats: () => request('/api/advisor/stats'),
  clients: ({ search, sector } = {}) => {
    const params = new URLSearchParams();
    if (search) params.set('search', search);
    if (sector) params.set('sector', sector);
    const qs = params.toString();
    return request(`/api/advisor/clients${qs ? `?${qs}` : ''}`);
  },
  clientDetail: (id) => request(`/api/advisor/clients/${id}`),
  addNote: (clientId, content) =>
    request(`/api/advisor/clients/${clientId}/notes`, {
      method: 'POST',
      body: { content },
    }),
  generateReport: (sessionId) =>
    request(`/api/diagnostic/${sessionId}/generate-report`, {
      method: 'POST',
      timeoutMs: TIMEOUTS.report,
    }),
  toggleShare: (reportId, isShared) =>
    request(`/api/advisor/reports/${reportId}/share`, {
      method: 'PATCH',
      body: { is_shared: isShared },
    }),
  analytics: () => request('/api/advisor/analytics'),
  downloadReportPdf: (clientId) =>
    downloadPdf(`/api/advisor/clients/${clientId}/report.pdf`, 'Musper_Diagnostic.pdf'),
};

export const clientApi = {
  me: () => request('/api/client/me'),
  sessions: () => request('/api/client/sessions'),
  reports: () => request('/api/client/reports'),
  transcript: (sessionId) => request(`/api/client/sessions/${sessionId}/transcript`),
  rate: (sessionId, score, feedback) =>
    request(`/api/client/sessions/${sessionId}/rate`, {
      method: 'POST',
      body: { score, feedback },
    }),
  updateBusinessProfile: (payload) =>
    request('/api/client/profile', { method: 'PATCH', body: payload }),
  downloadReportPdf: (reportId) =>
    downloadPdf(`/api/client/reports/${reportId}/report.pdf`, 'Musper_Diagnostic.pdf'),
};

export const SCORE_BAND = {
  A: { label: 'A', tone: 'good', range: '≥ 80' },
  B: { label: 'B', tone: 'mid', range: '60-79' },
  C: { label: 'C', tone: 'low', range: '< 60' },
  '-': { label: '-', tone: 'neutral', range: 'no score yet' },
};

export const DOMAIN_LABELS = {
  strategy: 'Strategy',
  customers: 'Customers',
  money: 'Money',
  operations: 'Operations',
  talent: 'Talent',
};
