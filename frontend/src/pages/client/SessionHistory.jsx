import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { History, ArrowUpRight, Sparkles, Star } from 'lucide-react';
import { clientApi } from '../../services/dashboard';
import {
  EmptyState, PageHeading, StatusPill, formatRelative,
} from '../../components/dashboard/ReportShared';

export default function SessionHistory() {
  const [sessions, setSessions] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    clientApi.sessions().then((s) => { setSessions(s); setLoading(false); });
  }, []);

  return (
    <div className="space-y-12">
      <PageHeading
        eyebrow="Session history"
        title="Every diagnostic you've started."
        description="Click any session to read the full transcript or leave a rating."
      />

      {loading ? (
        <p className="text-sm text-musper-muted">Loading...</p>
      ) : sessions.length === 0 ? (
        <EmptyState
          icon={History}
          title="No sessions yet."
          body="When you start your first diagnostic, it'll show up here with the full transcript."
          action={
            <Link
              to="/diagnostic"
              className="inline-flex items-center gap-2 rounded-full bg-musper-green px-5 py-2.5 text-sm font-medium text-musper-cream"
            >
              <Sparkles size={15} /> Start a diagnostic
            </Link>
          }
        />
      ) : (
        <div className="divide-y divide-musper-line overflow-hidden rounded-3xl border border-musper-line bg-musper-cream-soft/70">
          {sessions.map((s) => (
            <Link
              key={s.id}
              to={`/dashboard/history/${s.id}`}
              className="group grid items-center gap-3 px-6 py-5 transition-colors duration-200 hover:bg-musper-cream-soft sm:grid-cols-12"
            >
              <div className="sm:col-span-5">
                <p className="font-display text-lg leading-tight tracking-editorial">
                  {new Date(s.started_at).toLocaleDateString([], { day: 'numeric', month: 'short', year: 'numeric' })}
                </p>
                <p className="mt-0.5 text-xs text-musper-muted">
                  {s.completed_at ? `Completed ${formatRelative(s.completed_at)}` : 'In progress'}
                </p>
              </div>
              <div className="sm:col-span-2">
                {s.overall_score ? (
                  <span className="font-display text-lg font-medium italic text-musper-green">
                    {Math.round(s.overall_score)}<span className="text-xs text-musper-muted">/100</span>
                  </span>
                ) : (
                  <span className="text-xs text-musper-muted">-</span>
                )}
              </div>
              <div className="flex flex-wrap items-center gap-2 sm:col-span-4">
                <StatusPill status={s.status} />
                {s.is_shared && <StatusPill status="shared" />}
                {s.rating_score && (
                  <span className="inline-flex items-center gap-1 rounded-full bg-musper-orange-soft px-2.5 py-1 text-xs text-musper-orange-dark">
                    <Star size={11} fill="currentColor" /> {s.rating_score}/5
                  </span>
                )}
              </div>
              <div className="text-right sm:col-span-1">
                <ArrowUpRight
                  size={16}
                  className="ml-auto text-musper-muted-soft transition-all duration-300 group-hover:translate-x-0.5 group-hover:text-musper-green"
                />
              </div>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}
