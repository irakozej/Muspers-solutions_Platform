import { useEffect, useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import {
  LineChart, Line, ResponsiveContainer, Tooltip, XAxis, YAxis, CartesianGrid,
} from 'recharts';
import {
  ArrowLeft, Share2, FileDown, MessageSquare, Star, Mail, MapPin, Users as UsersIcon, Calendar,
} from 'lucide-react';
import { advisorApi } from '../../services/dashboard';
import {
  ChatTranscript,
  PageHeading,
  ReportCard,
  StatusPill,
  formatRelative,
} from '../../components/dashboard/ReportShared';

export default function ClientDetail() {
  const { id } = useParams();
  const [client, setClient] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [noteText, setNoteText] = useState('');
  const [noteBusy, setNoteBusy] = useState(false);
  const [shareBusy, setShareBusy] = useState(false);
  const [pdfBusy, setPdfBusy] = useState(false);
  const [pdfError, setPdfError] = useState(null);

  const load = () =>
    advisorApi.clientDetail(id)
      .then((d) => { setClient(d); setLoading(false); })
      .catch((e) => { setError(e.message); setLoading(false); });

  useEffect(() => { setLoading(true); load(); /* eslint-disable-next-line */ }, [id]);

  const onAddNote = async (e) => {
    e.preventDefault();
    if (!noteText.trim()) return;
    setNoteBusy(true);
    try {
      await advisorApi.addNote(id, noteText.trim());
      setNoteText('');
      await load();
    } finally { setNoteBusy(false); }
  };

  const onToggleShare = async () => {
    if (!client?.latest_report) return;
    setShareBusy(true);
    try {
      await advisorApi.toggleShare(client.latest_report.id, !client.latest_report.is_shared);
      await load();
    } finally { setShareBusy(false); }
  };

  const onDownloadPdf = async () => {
    if (!client?.latest_report) return;
    setPdfBusy(true);
    setPdfError(null);
    try {
      await advisorApi.downloadReportPdf(id);
    } catch (e) {
      setPdfError(e?.message || 'Could not generate the PDF.');
    } finally { setPdfBusy(false); }
  };

  if (loading) return <p className="text-sm text-musper-muted">Loading client...</p>;
  if (error) return <p className="text-sm text-musper-orange-dark">{error}</p>;
  if (!client) return null;

  const r = client.latest_report;

  return (
    <div className="space-y-12">
      <Link to="/advisor/clients" className="inline-flex items-center gap-1.5 text-sm text-musper-green hover:text-musper-green-deep">
        <ArrowLeft size={14} /> All clients
      </Link>

      <PageHeading
        eyebrow={client.sector || 'Client'}
        title={client.business_name}
        description={[
          client.location,
          client.business_size && `${client.business_size} business`,
          client.employee_count && `${client.employee_count} employees`,
          client.founded_year && `est. ${client.founded_year}`,
        ].filter(Boolean).join(' · ')}
        action={
          r && (
            <div className="flex flex-wrap items-center gap-2">
              <button
                type="button"
                onClick={onToggleShare}
                disabled={shareBusy}
                className={[
                  'inline-flex items-center gap-2 rounded-full px-5 py-2.5 text-sm font-medium transition-all duration-300 disabled:opacity-60',
                  r.is_shared
                    ? 'border border-musper-green/30 bg-musper-cream-soft text-musper-green hover:bg-white'
                    : 'bg-musper-green text-musper-cream shadow-soft hover:-translate-y-0.5 hover:bg-musper-green-deep',
                ].join(' ')}
              >
                <Share2 size={14} /> {r.is_shared ? 'Shared with client' : 'Share with client'}
              </button>
              <button
                type="button"
                onClick={onDownloadPdf}
                disabled={pdfBusy}
                className="inline-flex items-center gap-2 rounded-full border border-musper-line bg-musper-cream-soft px-5 py-2.5 text-sm font-medium text-musper-ink/80 transition hover:border-musper-green/30 disabled:cursor-not-allowed disabled:opacity-60"
              >
                <FileDown size={14} /> {pdfBusy ? 'Generating PDF...' : 'Export PDF'}
              </button>
            </div>
          )
        }
      />

      {pdfError && (
        <div className="rounded-2xl border border-musper-orange/30 bg-musper-orange-soft px-4 py-3 text-sm text-musper-orange-dark">
          {pdfError}
        </div>
      )}

      {/* Business snapshot */}
      <section className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <SnapshotTile icon={Mail} label="Contact" value={client.contact_email || '-'} sub={client.contact_name} />
        <SnapshotTile icon={MapPin} label="Location" value={client.location || '-'} />
        <SnapshotTile icon={UsersIcon} label="Headcount" value={client.employee_count ?? '-'} sub={client.business_size || ''} />
        <SnapshotTile icon={Calendar} label="Founded" value={client.founded_year ?? '-'} sub={client.revenue_band || ''} />
      </section>

      {/* Revenue trend */}
      {client.revenue_trend?.length > 0 && (
        <section className="rounded-3xl border border-musper-line bg-musper-cream-soft/70 p-6 sm:p-8">
          <div className="flex items-baseline justify-between gap-3">
            <p className="eyebrow">Revenue trend</p>
            <p className="text-xs text-musper-muted">Quarterly, millions of RWF</p>
          </div>
          <div className="mt-6 h-44 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={client.revenue_trend} margin={{ top: 10, right: 20, bottom: 0, left: 0 }}>
                <CartesianGrid stroke="rgba(22,22,22,0.06)" />
                <XAxis dataKey="period" stroke="#9A9591" tick={{ fontSize: 12 }} />
                <YAxis stroke="#9A9591" tick={{ fontSize: 12 }} />
                <Tooltip
                  contentStyle={{ borderRadius: 12, border: '1px solid rgba(22,22,22,0.08)', fontSize: 12 }}
                  formatter={(v) => [`${v}M RWF`, 'Revenue']}
                />
                <Line type="monotone" dataKey="revenue_mrwf" stroke="#1F4E3D" strokeWidth={2.5} dot={{ fill: '#E07B1F', r: 4 }} activeDot={{ r: 6 }} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </section>
      )}

      {/* Report */}
      {r ? (
        <ReportCard report={r} />
      ) : (
        <div className="rounded-3xl border border-dashed border-musper-line bg-musper-cream-soft/60 p-10 text-center">
          <p className="font-display text-2xl leading-tight tracking-editorial">No report yet.</p>
          <p className="mt-3 text-sm text-musper-muted">
            This session is still in progress. The report will appear here when the diagnostic is complete.
          </p>
        </div>
      )}

      {/* Session history */}
      {client.sessions?.length > 0 && (
        <section>
          <p className="eyebrow">Session history</p>
          <h2 className="mt-3 font-display text-2xl tracking-editorial">All sessions for this client</h2>
          <div className="mt-6 divide-y divide-musper-line overflow-hidden rounded-3xl border border-musper-line bg-musper-cream-soft/70">
            {client.sessions.map((s) => (
              <div key={s.id} className="flex flex-col items-start justify-between gap-3 px-6 py-4 sm:flex-row sm:items-center">
                <div>
                  <p className="font-medium text-musper-ink">
                    {new Date(s.started_at).toLocaleDateString([], { day: 'numeric', month: 'short', year: 'numeric' })}
                  </p>
                  <p className="text-xs text-musper-muted">
                    {s.completed_at ? `Completed ${formatRelative(s.completed_at)}` : 'In progress'}
                  </p>
                </div>
                <div className="flex flex-wrap items-center gap-3 text-sm">
                  {s.overall_score && (
                    <span className="font-display text-lg font-medium italic text-musper-green">
                      {Math.round(s.overall_score)}<span className="text-xs text-musper-muted">/100</span>
                    </span>
                  )}
                  <StatusPill status={s.status} />
                  {s.is_shared && <StatusPill status="shared" />}
                  {s.rating_score && (
                    <span className="inline-flex items-center gap-1 rounded-full bg-musper-orange-soft px-2.5 py-1 text-xs text-musper-orange-dark">
                      <Star size={11} fill="currentColor" /> {s.rating_score}/5
                    </span>
                  )}
                </div>
              </div>
            ))}
          </div>
        </section>
      )}

      {/* Transcript */}
      {client.transcript?.length > 0 && (
        <section>
          <div className="flex items-baseline gap-3">
            <p className="eyebrow">Transcript</p>
            <p className="text-xs text-musper-muted">{client.transcript.length} messages</p>
          </div>
          <h2 className="mt-3 font-display text-2xl tracking-editorial flex items-center gap-2">
            <MessageSquare size={20} className="text-musper-orange" />
            From the diagnostic session
          </h2>
          <div className="mt-6 rounded-3xl border border-musper-line bg-musper-cream-soft/70 p-6 sm:p-8">
            <ChatTranscript messages={client.transcript} />
          </div>
        </section>
      )}

      {/* Rating */}
      {client.rating && (
        <section className="rounded-3xl border border-musper-orange/25 bg-musper-orange-soft/60 p-6 sm:p-8">
          <p className="eyebrow">Client rating</p>
          <div className="mt-4 flex items-center gap-1">
            {[1, 2, 3, 4, 5].map((n) => (
              <Star
                key={n}
                size={20}
                fill={n <= client.rating.score ? '#E07B1F' : 'none'}
                stroke="#E07B1F"
              />
            ))}
            <span className="ml-2 font-medium">{client.rating.score} / 5</span>
          </div>
          {client.rating.feedback && (
            <blockquote className="mt-4 text-base italic text-musper-ink/85">
              "{client.rating.feedback}"
            </blockquote>
          )}
          <p className="mt-3 text-xs text-musper-muted">{formatRelative(client.rating.created_at)}</p>
        </section>
      )}

      {/* Private notes */}
      <section>
        <p className="eyebrow">Private advisor notes</p>
        <h2 className="mt-3 font-display text-2xl tracking-editorial">
          Only visible to you.
        </h2>
        <form onSubmit={onAddNote} className="mt-6 rounded-2xl border border-musper-line bg-white p-4">
          <textarea
            value={noteText}
            onChange={(e) => setNoteText(e.target.value)}
            placeholder="Add a private note about this client..."
            rows={3}
            className="w-full resize-y rounded-lg border border-musper-line bg-musper-cream-soft px-3 py-2 text-sm focus:border-musper-green focus:outline-none"
          />
          <div className="mt-3 flex justify-end">
            <button
              type="submit"
              disabled={noteBusy || !noteText.trim()}
              className="rounded-full bg-musper-green px-5 py-2 text-sm font-medium text-musper-cream disabled:cursor-not-allowed disabled:opacity-60 hover:bg-musper-green-deep"
            >
              {noteBusy ? 'Saving...' : 'Add note'}
            </button>
          </div>
        </form>

        {client.notes?.length > 0 ? (
          <div className="mt-6 space-y-3">
            {client.notes.map((n) => (
              <div key={n.id} className="rounded-2xl border border-musper-line bg-musper-cream-soft/70 px-5 py-4">
                <p className="text-sm leading-relaxed text-musper-ink/90">{n.content}</p>
                <p className="mt-2 text-xs text-musper-muted">{formatRelative(n.created_at)}</p>
              </div>
            ))}
          </div>
        ) : (
          <p className="mt-6 text-sm text-musper-muted">No notes yet.</p>
        )}
      </section>
    </div>
  );
}

function SnapshotTile({ icon: Icon, label, value, sub }) {
  return (
    <div className="rounded-2xl border border-musper-line bg-musper-cream-soft p-5">
      <div className="flex items-center gap-2 text-xs uppercase tracking-eyebrow text-musper-muted">
        <Icon size={13} /> {label}
      </div>
      <p className="mt-3 truncate font-medium text-musper-ink">{value}</p>
      {sub && <p className="mt-1 text-xs text-musper-muted truncate">{sub}</p>}
    </div>
  );
}
