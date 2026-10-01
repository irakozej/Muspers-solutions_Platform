import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { Sparkles, FileText, History, ArrowUpRight, Building2 } from 'lucide-react';
import { clientApi } from '../../services/dashboard';
import { useAuth } from '../../context/AuthContext';
import {
  EmptyState, PageHeading, StatusPill, formatRelative,
} from '../../components/dashboard/ReportShared';
import TeaserSnapshot from '../../components/dashboard/TeaserSnapshot';

// Teasers for the most recent completed interviews; older ones live in History.
const MAX_TEASERS = 3;

export default function ClientOverview() {
  const { user } = useAuth();
  const [overview, setOverview] = useState(null);
  const [loading, setLoading] = useState(true);
  const [teasers, setTeasers] = useState([]);

  useEffect(() => {
    clientApi.me().then(async (d) => {
      setOverview(d);
      setLoading(false);
      const completed = (d.sessions || []).filter((s) => s.status === 'completed').slice(0, MAX_TEASERS);
      const results = await Promise.all(completed.map((s) => clientApi.snapshot(s.id).catch(() => null)));
      setTeasers(results.filter(Boolean));
    });
  }, []);

  const firstName = user?.full_name?.split(' ')[0] || 'there';
  const sessions = overview?.sessions || [];
  const hasStarted = sessions.length > 0;

  return (
    <div className="space-y-12">
      <PageHeading
        eyebrow="Your dashboard"
        title={`Hello, ${firstName}.`}
        description={overview?.business_name ? `${overview.business_name} · ${overview.sector || 'Sector unspecified'}` : 'Your MusperSolutions workspace.'}
        action={
          <Link
            to="/diagnostic"
            className="inline-flex items-center gap-2 rounded-full bg-musper-orange px-5 py-2.5 text-sm font-medium text-musper-cream shadow-cta transition-all duration-300 hover:-translate-y-0.5 hover:bg-musper-orange-dark"
          >
            <Sparkles size={15} /> Start a new diagnostic
          </Link>
        }
      />

      {loading ? (
        <p className="text-sm text-musper-muted">Loading...</p>
      ) : !hasStarted ? (
        <EmptyState
          icon={Sparkles}
          title="No diagnostics yet."
          body="Start a diagnostic to receive a personalised report on your business strategy, customers, money, operations, and team."
          action={
            <Link
              to="/diagnostic"
              className="inline-flex items-center gap-2 rounded-full bg-musper-green px-6 py-3 text-sm font-medium text-musper-cream shadow-soft hover:bg-musper-green-deep"
            >
              <Sparkles size={15} /> Start your first diagnostic
            </Link>
          }
        />
      ) : (
        <>
          {/* Results: teaser per completed interview; full report once Penny shares */}
          {teasers.length > 0 && (
            <section>
              <p className="eyebrow">Your results</p>
              <h2 className="mt-3 font-display text-2xl tracking-editorial sm:text-3xl">Your latest diagnostic.</h2>
              <div className="mt-6 space-y-6">
                {teasers.map((t) => <TeaserSnapshot key={t.session_id} teaser={t} compact />)}
              </div>
            </section>
          )}

          {/* Past sessions */}
          <section>
            <div className="flex items-baseline justify-between">
              <div>
                <p className="eyebrow">Past sessions</p>
                <h2 className="mt-3 font-display text-2xl tracking-editorial sm:text-3xl">Your diagnostic history.</h2>
              </div>
              <Link to="/dashboard/history" className="text-sm text-musper-green hover:text-musper-green-deep">
                Full history →
              </Link>
            </div>

            <div className="mt-6 divide-y divide-musper-line overflow-hidden rounded-3xl border border-musper-line bg-musper-cream-soft/70">
              {sessions.map((s) => (
                <Link
                  key={s.id}
                  to={`/dashboard/history/${s.id}`}
                  className="group flex items-center justify-between gap-3 px-6 py-4 transition-colors duration-200 hover:bg-musper-cream-soft"
                >
                  <div>
                    <p className="font-medium">{new Date(s.started_at).toLocaleDateString([], { day: 'numeric', month: 'short', year: 'numeric' })}</p>
                    <p className="mt-0.5 text-xs text-musper-muted">
                      {s.completed_at ? `Completed ${formatRelative(s.completed_at)}` : 'In progress'}
                    </p>
                  </div>
                  <div className="flex items-center gap-3">
                    {s.overall_score && (
                      <span className="font-display text-lg font-medium italic text-musper-green">
                        {Math.round(s.overall_score)}<span className="text-xs text-musper-muted">/100</span>
                      </span>
                    )}
                    <StatusPill status={s.status} />
                    <ArrowUpRight
                      size={14}
                      className="text-musper-muted-soft opacity-0 transition-all duration-300 group-hover:translate-x-0.5 group-hover:opacity-100"
                    />
                  </div>
                </Link>
              ))}
            </div>
          </section>

          {/* Quick links */}
          <section className="grid gap-4 sm:grid-cols-3">
            <QuickCard icon={FileText} title="My Reports" detail="View reports shared with you" to="/dashboard/reports" />
            <QuickCard icon={History} title="Session History" detail="Past diagnostics + transcripts" to="/dashboard/history" />
            <QuickCard icon={Building2} title="Business Profile" detail="Update your business info" to="/dashboard/profile" />
          </section>
        </>
      )}
    </div>
  );
}

function QuickCard({ icon: Icon, title, detail, to }) {
  return (
    <Link
      to={to}
      className="group flex flex-col gap-4 rounded-3xl border border-musper-line bg-musper-cream-soft/70 p-5 transition-all duration-300 hover:-translate-y-0.5 hover:border-musper-green/30 hover:shadow-soft"
    >
      <span className="flex h-10 w-10 items-center justify-center rounded-full bg-musper-green-soft text-musper-green">
        <Icon size={16} strokeWidth={1.75} />
      </span>
      <div>
        <p className="font-display text-lg tracking-editorial">{title}</p>
        <p className="mt-1 text-xs text-musper-muted">{detail}</p>
      </div>
    </Link>
  );
}
