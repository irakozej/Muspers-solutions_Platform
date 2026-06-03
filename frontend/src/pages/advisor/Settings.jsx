import { Link } from 'react-router-dom';
import { ArrowUpRight, Bell, Plug } from 'lucide-react';
import { useAuth } from '../../context/AuthContext';
import { PageHeading } from '../../components/dashboard/ReportShared';

export default function AdvisorSettings() {
  const { user } = useAuth();

  return (
    <div className="space-y-12">
      <PageHeading
        eyebrow="Settings"
        title="Workspace settings."
        description="Your profile, notifications, and integrations."
      />

      <section className="rounded-3xl border border-musper-line bg-musper-cream-soft/70 p-6 sm:p-8">
        <p className="eyebrow">Profile</p>
        <h2 className="mt-3 font-display text-2xl tracking-editorial">Account details.</h2>
        <div className="mt-6 grid gap-3 text-sm sm:grid-cols-2">
          <Row label="Name" value={user?.full_name || '—'} />
          <Row label="Email" value={user?.email} />
          <Row label="Role" value={user?.role} />
          <Row label="Email verified" value={user?.is_verified ? 'Yes' : 'No'} />
        </div>
        <div className="mt-6">
          <Link
            to="/profile"
            className="inline-flex items-center gap-2 rounded-full bg-musper-green px-5 py-2.5 text-sm font-medium text-musper-cream hover:bg-musper-green-deep"
          >
            Edit profile <ArrowUpRight size={14} />
          </Link>
        </div>
      </section>

      <section className="rounded-3xl border border-musper-line bg-musper-cream-soft/70 p-6 sm:p-8">
        <div className="flex items-start gap-4">
          <span className="flex h-10 w-10 items-center justify-center rounded-full bg-musper-green-soft text-musper-green">
            <Bell size={16} />
          </span>
          <div>
            <p className="eyebrow">Notifications</p>
            <h2 className="mt-3 font-display text-2xl tracking-editorial">Stay in the loop.</h2>
            <p className="mt-3 max-w-2xl text-sm text-musper-muted">
              Email summaries when a client completes a diagnostic, a new rating arrives, or a
              scheduled follow-up is due. Configuration UI lands with the notifications phase.
            </p>
          </div>
        </div>
      </section>

      <section className="rounded-3xl border border-musper-line bg-musper-cream-soft/70 p-6 sm:p-8">
        <div className="flex items-start gap-4">
          <span className="flex h-10 w-10 items-center justify-center rounded-full bg-musper-green-soft text-musper-green">
            <Plug size={16} />
          </span>
          <div className="flex-1">
            <p className="eyebrow">Connected accounts</p>
            <h2 className="mt-3 font-display text-2xl tracking-editorial">Integrations.</h2>
            <p className="mt-3 max-w-2xl text-sm text-musper-muted">
              Cal.com (consultation bookings), Mailchimp (newsletter), and Wave (accounting) integrations
              ship in Phase 7. Each will appear here for one-click connection.
            </p>
            <div className="mt-6 grid gap-3 sm:grid-cols-3">
              <IntegrationCard name="Cal.com" />
              <IntegrationCard name="Mailchimp" />
              <IntegrationCard name="Wave" />
            </div>
          </div>
        </div>
      </section>
    </div>
  );
}

function Row({ label, value }) {
  return (
    <div className="flex items-center justify-between rounded-xl border border-musper-line bg-white px-4 py-3">
      <span className="text-xs uppercase tracking-eyebrow text-musper-muted">{label}</span>
      <span className="truncate text-sm font-medium text-musper-ink">{value}</span>
    </div>
  );
}

function IntegrationCard({ name }) {
  return (
    <div className="rounded-2xl border border-dashed border-musper-line bg-white px-4 py-5 text-center">
      <p className="font-display text-base font-medium">{name}</p>
      <p className="mt-1 text-xs text-musper-muted">Coming soon</p>
    </div>
  );
}
