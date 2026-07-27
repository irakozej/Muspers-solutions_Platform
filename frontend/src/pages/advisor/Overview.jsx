import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { Users, Activity, FileClock, Star, UserPlus, ArrowUpRight, MessageSquare } from 'lucide-react';
import { advisorApi } from '../../services/dashboard';
import { useAuth } from '../../context/AuthContext';
import { PageHeading, StatTile, formatRelative } from '../../components/dashboard/ReportShared';

const ICONS = {
  client_registered: UserPlus,
  diagnostic_completed: FileClock,
  rating_received: Star,
};

export default function AdvisorOverview() {
  const { user } = useAuth();
  const [stats, setStats] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    advisorApi.stats().then(setStats).catch((e) => setError(e.message));
  }, []);

  const firstName = user?.full_name?.split(' ')[0] || 'MusperSolutions';

  return (
    <div className="space-y-12">
      <PageHeading
        eyebrow="Advisor workspace"
        title={`Welcome back, ${firstName}.`}
        description="A snapshot of the practice today, active sessions, completed diagnostics, and what's waiting for your attention."
        action={
          <Link
            to="/advisor/clients"
            className="inline-flex items-center gap-2 rounded-full bg-musper-green px-5 py-2.5 text-sm font-medium text-musper-cream shadow-soft transition-all duration-300 hover:-translate-y-0.5 hover:bg-musper-green-deep"
          >
            <UserPlus size={15} />
            Send diagnostic link
            <ArrowUpRight size={14} />
          </Link>
        }
      />

      {error && (
        <div className="rounded-2xl border border-musper-orange/30 bg-musper-orange-soft px-4 py-3 text-sm text-musper-orange-dark">
          {error}
        </div>
      )}

      {/* Stats */}
      {stats && (
        <section>
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            <StatTile
              label="Total clients"
              value={stats.total_clients}
              detail="across all sectors"
            />
            <StatTile
              label="Active this week"
              value={stats.active_sessions_this_week}
              detail="sessions started in the last 7 days"
              accent
            />
            <StatTile
              label="Avg GROW Overall"
              value={stats.average_grow_overall}
              detail="composite across all completed reports"
            />
            <StatTile
              label="Pending share"
              value={stats.reports_pending_share}
              detail="reports awaiting your share decision"
              accent
            />
          </div>
        </section>
      )}

      {/* Activity feed */}
      <section>
        <div className="flex items-end justify-between gap-3">
          <div>
            <p className="eyebrow">Recent activity</p>
            <h2 className="mt-3 font-display text-2xl tracking-editorial sm:text-3xl">
              What's happened lately.
            </h2>
          </div>
          <Link to="/advisor/clients" className="text-sm text-musper-green hover:text-musper-green-deep">
            View all clients →
          </Link>
        </div>

        <div className="mt-8 divide-y divide-musper-line overflow-hidden rounded-3xl border border-musper-line bg-musper-cream-soft/70">
          {stats?.recent_activity?.length === 0 && (
            <div className="px-6 py-10 text-center text-sm text-musper-muted">
              Nothing has happened yet.
            </div>
          )}
          {stats?.recent_activity?.map((e, i) => {
            const Icon = ICONS[e.kind] || Activity;
            const linkTo = e.client_id ? `/advisor/clients/${e.client_id}` : '/advisor/clients';
            return (
              <Link
                key={i}
                to={linkTo}
                className="group flex items-start gap-4 px-6 py-4 transition-colors duration-200 hover:bg-musper-cream-soft"
              >
                <span className="mt-1 flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-musper-green text-musper-cream">
                  <Icon size={14} strokeWidth={1.75} />
                </span>
                <div className="min-w-0 flex-1">
                  <p className="font-medium text-musper-ink">{e.title}</p>
                  {e.description && (
                    <p className="mt-0.5 truncate text-sm text-musper-muted">{e.description}</p>
                  )}
                  <p className="mt-1 text-xs uppercase tracking-eyebrow text-musper-muted-soft">
                    {formatRelative(e.at)}
                  </p>
                </div>
                <ArrowUpRight
                  size={15}
                  className="mt-1 text-musper-muted-soft opacity-0 transition-all duration-300 group-hover:translate-x-0.5 group-hover:opacity-100"
                />
              </Link>
            );
          })}
        </div>
      </section>

      {/* Quick action card */}
      <section className="rounded-3xl border border-musper-green/15 bg-musper-green-soft/60 p-8">
        <div className="flex flex-col gap-6 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <p className="eyebrow">Quick action</p>
            <h3 className="mt-3 font-display text-2xl leading-tight tracking-editorial">
              Send a diagnostic link to a new client.
            </h3>
            <p className="mt-3 max-w-md text-sm text-musper-muted">
              When the chatbot (Phase 4) ships, this will generate a one-link onboarding flow.
              Until then, send the public diagnostic page link.
            </p>
          </div>
          <Link
            to="/diagnostic"
            className="inline-flex items-center gap-2 rounded-full bg-musper-green px-5 py-3 text-sm font-medium text-musper-cream shadow-soft hover:bg-musper-green-deep"
          >
            <MessageSquare size={15} /> Open diagnostic page
          </Link>
        </div>
      </section>
    </div>
  );
}
