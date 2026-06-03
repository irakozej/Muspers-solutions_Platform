import { useEffect, useState } from 'react';
import {
  BarChart, Bar, XAxis, YAxis, ResponsiveContainer, Tooltip, CartesianGrid,
  PieChart, Pie, Cell, Legend,
} from 'recharts';
import { advisorApi, DOMAIN_LABELS } from '../../services/dashboard';
import { PageHeading } from '../../components/dashboard/ReportShared';

const PIE_COLORS = ['#1F4E3D', '#2C6B55', '#E07B1F', '#B8631A', '#6B6B6B', '#9A9591', '#16382B', '#163A2D'];

export default function Analytics() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    advisorApi.analytics().then((d) => { setData(d); setLoading(false); });
  }, []);

  if (loading) return <p className="text-sm text-musper-muted">Loading…</p>;
  if (!data) return null;

  const domainData = Object.entries(data.average_domain_scores).map(([k, v]) => ({
    domain: DOMAIN_LABELS[k] || k,
    score: v,
  }));

  return (
    <div className="space-y-12">
      <PageHeading
        eyebrow="Analytics"
        title="Practice in aggregate."
        description="Patterns across every diagnostic in the system — useful for spotting common gaps and tuning programs."
      />

      <div className="grid gap-4 sm:grid-cols-3">
        <SummaryTile label="Completed sessions" value={data.total_completed} />
        <SummaryTile label="In progress" value={data.total_in_progress} accent />
        <SummaryTile label="Completion rate" value={`${data.completion_rate}%`} />
      </div>

      {/* Domain averages */}
      <section className="rounded-3xl border border-musper-line bg-musper-cream-soft/70 p-6 sm:p-8">
        <div className="flex items-baseline justify-between gap-3">
          <div>
            <p className="eyebrow">Average scores by domain</p>
            <h2 className="mt-3 font-display text-2xl tracking-editorial">Where the practice is strongest.</h2>
          </div>
        </div>
        <div className="mt-6 h-72 w-full">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={domainData} margin={{ top: 10, right: 20, bottom: 0, left: 0 }}>
              <CartesianGrid stroke="rgba(22,22,22,0.06)" vertical={false} />
              <XAxis dataKey="domain" stroke="#9A9591" tick={{ fontSize: 12 }} />
              <YAxis stroke="#9A9591" tick={{ fontSize: 12 }} domain={[0, 100]} />
              <Tooltip
                contentStyle={{ borderRadius: 12, border: '1px solid rgba(22,22,22,0.08)', fontSize: 12 }}
                formatter={(v) => [`${v}`, 'Avg score']}
              />
              <Bar dataKey="score" fill="#1F4E3D" radius={[8, 8, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </section>

      <div className="grid gap-8 lg:grid-cols-12">
        {/* Sector distribution */}
        <section className="rounded-3xl border border-musper-line bg-musper-cream-soft/70 p-6 sm:p-8 lg:col-span-6">
          <p className="eyebrow">Client distribution by sector</p>
          <h2 className="mt-3 font-display text-2xl tracking-editorial">Sector mix.</h2>
          <div className="mt-6 h-72 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={data.sector_distribution}
                  dataKey="count"
                  nameKey="sector"
                  innerRadius={55}
                  outerRadius={95}
                  paddingAngle={2}
                >
                  {data.sector_distribution.map((_, i) => (
                    <Cell key={i} fill={PIE_COLORS[i % PIE_COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip
                  contentStyle={{ borderRadius: 12, border: '1px solid rgba(22,22,22,0.08)', fontSize: 12 }}
                />
                <Legend wrapperStyle={{ fontSize: 11 }} />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </section>

        {/* Top red flags */}
        <section className="rounded-3xl border border-musper-line bg-musper-cream-soft/70 p-6 sm:p-8 lg:col-span-6">
          <p className="eyebrow">Most common red flags</p>
          <h2 className="mt-3 font-display text-2xl tracking-editorial">What keeps coming up.</h2>
          {data.top_red_flags.length === 0 ? (
            <p className="mt-6 text-sm text-musper-muted">No red flags recorded yet.</p>
          ) : (
            <ol className="mt-6 space-y-2.5">
              {data.top_red_flags.map((f, i) => (
                <li key={i} className="flex items-start gap-3 rounded-xl border border-musper-line bg-white px-4 py-3 text-sm">
                  <span className="mt-0.5 font-mono text-xs text-musper-muted-soft">0{i + 1}</span>
                  <span className="flex-1">{f.label}</span>
                  <span className="text-xs text-musper-muted">×{f.count}</span>
                </li>
              ))}
            </ol>
          )}
        </section>
      </div>
    </div>
  );
}

function SummaryTile({ label, value, accent }) {
  return (
    <div className="rounded-2xl border border-musper-line bg-musper-cream-soft p-5">
      <p className="text-xs uppercase tracking-eyebrow text-musper-muted">{label}</p>
      <p className={[
        'mt-3 font-display text-4xl font-medium italic leading-none tracking-editorial',
        accent ? 'text-musper-orange' : 'text-musper-green',
      ].join(' ')}>
        {value}
      </p>
    </div>
  );
}
