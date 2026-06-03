import { useEffect, useMemo, useState } from 'react';
import { Link } from 'react-router-dom';
import { Search, Filter, ArrowUpRight } from 'lucide-react';
import { advisorApi } from '../../services/dashboard';
import {
  PageHeading,
  ScoreBand,
  StatusPill,
  formatRelative,
} from '../../components/dashboard/ReportShared';

export default function ClientList() {
  const [clients, setClients] = useState([]);
  const [search, setSearch] = useState('');
  const [sector, setSector] = useState('');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    advisorApi.clients().then((rows) => {
      setClients(rows);
      setLoading(false);
    });
  }, []);

  const sectors = useMemo(
    () => Array.from(new Set(clients.map((c) => c.sector).filter(Boolean))).sort(),
    [clients],
  );

  const filtered = useMemo(() => {
    return clients.filter((c) => {
      const matchesSearch = !search || c.business_name.toLowerCase().includes(search.toLowerCase());
      const matchesSector = !sector || c.sector === sector;
      return matchesSearch && matchesSector;
    });
  }, [clients, search, sector]);

  return (
    <div className="space-y-10">
      <PageHeading
        eyebrow="Clients"
        title="All clients."
        description={`${clients.length} businesses currently in the practice. Click a row to open the full diagnostic.`}
      />

      {/* Filters */}
      <div className="flex flex-col gap-3 sm:flex-row">
        <div className="relative flex-1">
          <Search size={15} className="absolute left-4 top-1/2 -translate-y-1/2 text-musper-muted" />
          <input
            type="search"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search by business name"
            className="w-full rounded-full border border-musper-line bg-white py-3 pl-11 pr-4 text-sm placeholder:text-musper-muted-soft focus:border-musper-green focus:outline-none focus:ring-2 focus:ring-musper-green/15"
          />
        </div>
        <div className="relative">
          <Filter size={15} className="pointer-events-none absolute left-4 top-1/2 -translate-y-1/2 text-musper-muted" />
          <select
            value={sector}
            onChange={(e) => setSector(e.target.value)}
            className="appearance-none rounded-full border border-musper-line bg-white py-3 pl-11 pr-9 text-sm text-musper-ink focus:border-musper-green focus:outline-none"
          >
            <option value="">All sectors</option>
            {sectors.map((s) => <option key={s} value={s}>{s}</option>)}
          </select>
        </div>
      </div>

      {/* Table */}
      <div className="overflow-hidden rounded-3xl border border-musper-line bg-musper-cream-soft/70">
        <div className="hidden grid-cols-12 border-b border-musper-line bg-white px-6 py-3 text-xs font-medium uppercase tracking-eyebrow text-musper-muted lg:grid">
          <div className="col-span-4">Business</div>
          <div className="col-span-2">Sector</div>
          <div className="col-span-1 text-right">Score</div>
          <div className="col-span-1 text-center">Band</div>
          <div className="col-span-2">Last activity</div>
          <div className="col-span-2 text-right">Status</div>
        </div>

        {loading ? (
          <div className="px-6 py-12 text-center text-sm text-musper-muted">Loading…</div>
        ) : filtered.length === 0 ? (
          <div className="px-6 py-12 text-center text-sm text-musper-muted">No clients match.</div>
        ) : (
          <div className="divide-y divide-musper-line">
            {filtered.map((c) => (
              <Link
                key={c.id}
                to={`/advisor/clients/${c.id}`}
                className="group grid grid-cols-1 gap-4 px-6 py-5 transition-colors duration-200 hover:bg-musper-cream-soft lg:grid-cols-12 lg:items-center lg:gap-2"
              >
                <div className="lg:col-span-4">
                  <p className="font-display text-lg leading-tight tracking-editorial">
                    {c.business_name}
                  </p>
                  <p className="mt-0.5 text-xs text-musper-muted">{c.location || '—'}</p>
                </div>
                <div className="text-sm text-musper-ink/80 lg:col-span-2">{c.sector || '—'}</div>
                <div className="lg:col-span-1 lg:text-right">
                  <span className="font-display text-lg font-medium italic text-musper-green">
                    {c.overall_score ? Math.round(c.overall_score) : '—'}
                  </span>
                </div>
                <div className="lg:col-span-1 lg:text-center">
                  <ScoreBand band={c.band} size="sm" />
                </div>
                <div className="text-sm text-musper-muted lg:col-span-2">
                  {formatRelative(c.last_activity)}
                </div>
                <div className="flex items-center gap-2 lg:col-span-2 lg:justify-end">
                  <StatusPill status={c.session_status || 'pending'} />
                  {c.has_report && (
                    <StatusPill status={c.is_shared ? 'shared' : 'not_shared'} />
                  )}
                  <ArrowUpRight
                    size={14}
                    className="text-musper-muted-soft opacity-0 transition-all duration-300 group-hover:translate-x-0.5 group-hover:opacity-100"
                  />
                </div>
              </Link>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
