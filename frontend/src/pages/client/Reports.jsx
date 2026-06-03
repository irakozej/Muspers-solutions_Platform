import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { FileText, ArrowUpRight, Sparkles } from 'lucide-react';
import { clientApi } from '../../services/dashboard';
import { EmptyState, PageHeading, ScoreBand } from '../../components/dashboard/ReportShared';

export default function ClientReports() {
  const [reports, setReports] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    clientApi.reports().then((rs) => { setReports(rs); setLoading(false); });
  }, []);

  return (
    <div className="space-y-12">
      <PageHeading
        eyebrow="My Reports"
        title="Diagnostic reports shared with you."
        description="Each report distils your session into priority actions and coaching topics. Read at your pace."
      />

      {loading ? (
        <p className="text-sm text-musper-muted">Loading…</p>
      ) : reports.length === 0 ? (
        <EmptyState
          icon={FileText}
          title="No shared reports yet."
          body="When Penny shares a diagnostic report with you, it will appear here."
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
        <div className="grid gap-4">
          {reports.map((r) => (
            <Link
              key={r.id}
              to={`/dashboard/reports/${r.id}`}
              className="group flex flex-col gap-5 rounded-3xl border border-musper-line bg-musper-cream-soft/70 p-6 transition-all duration-300 hover:-translate-y-0.5 hover:border-musper-green/30 hover:shadow-soft sm:flex-row sm:items-center"
            >
              <div className="flex-1">
                <p className="text-xs uppercase tracking-eyebrow text-musper-green">Report</p>
                <p className="mt-3 font-display text-2xl leading-tight tracking-editorial">
                  {new Date(r.created_at).toLocaleDateString([], { day: 'numeric', month: 'long', year: 'numeric' })}
                </p>
                {r.summary && (
                  <p className="mt-3 max-w-2xl text-sm text-musper-muted line-clamp-2">{r.summary}</p>
                )}
                <p className="mt-3 text-xs text-musper-muted-soft">
                  {r.priority_actions?.length || 0} priority actions · {r.red_flags?.length || 0} red flags · {r.suggested_topics?.length || 0} coaching topics
                </p>
              </div>
              <div className="flex items-center gap-5">
                <div>
                  <p className="text-[0.65rem] uppercase tracking-eyebrow text-musper-muted">GROW</p>
                  <ScoreBand band={r.headline.grow_band} score={r.headline.grow_overall} size="sm" />
                </div>
                <ArrowUpRight size={18} className="text-musper-green opacity-0 transition-all duration-300 group-hover:translate-x-0.5 group-hover:opacity-100" />
              </div>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}
