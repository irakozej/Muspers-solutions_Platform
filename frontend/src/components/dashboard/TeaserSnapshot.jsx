// The client's teaser: two headline scores and two area names, shown the
// moment the interview ends. Everything else is listed as locked until Penny
// shares the full report. All data comes from the allowlisted
// /api/client/sessions/:id/snapshot endpoint; nothing here can reveal more.
import { useState } from 'react';
import { Link } from 'react-router-dom';
import { Lock, CalendarDays, FileDown, ArrowUpRight } from 'lucide-react';
import { ScoreRing } from './ReportShared';
import { BOOKING_URL } from '../../data/site';
import { clientApi } from '../../services/dashboard';

export default function TeaserSnapshot({ teaser, compact = false }) {
  if (!teaser) return null;
  const shared = teaser.report_shared && teaser.report_id;

  return (
    <section className="overflow-hidden rounded-[2rem] bg-musper-green-deep text-musper-cream">
      <div className={compact ? 'p-6 sm:p-8' : 'p-7 sm:p-10'}>
        <p className="text-sm text-musper-orange">Your snapshot</p>
        <h2 className="mt-2 font-display text-2xl leading-tight tracking-editorial text-musper-cream sm:text-3xl">
          {shared ? 'Your full report is ready.' : 'A first look at where you stand.'}
        </h2>

        <div className="mt-7 flex flex-wrap items-center gap-x-10 gap-y-6">
          <ScoreRing label="Financial health" score={teaser.financial_health} size="lg" />
          <ScoreRing label="Business health" score={teaser.business_health} size="sm" />
        </div>

        {(teaser.strongest_area || teaser.attention_area) && (
          <dl className="mt-7 grid gap-2 sm:grid-cols-2">
            {teaser.strongest_area && (
              <div className="rounded-xl bg-musper-cream/10 px-4 py-3">
                <dt className="text-xs text-musper-cream/60">Strongest area</dt>
                <dd className="mt-0.5 font-medium">{teaser.strongest_area}</dd>
              </div>
            )}
            {teaser.attention_area && (
              <div className="rounded-xl bg-musper-orange/15 px-4 py-3 ring-1 ring-musper-orange/40">
                <dt className="text-xs text-musper-orange">Needs most attention</dt>
                <dd className="mt-0.5 font-medium">{teaser.attention_area}</dd>
              </div>
            )}
          </dl>
        )}
      </div>

      <div className={['border-t border-musper-line-on-dark bg-musper-green/40', compact ? 'p-6 sm:p-8' : 'p-7 sm:p-10'].join(' ')}>
        {shared ? (
          <SharedActions reportId={teaser.report_id} />
        ) : (
          <>
            <p className="text-sm text-musper-cream/80">Your full report includes</p>
            <ul className="mt-3 grid gap-2 sm:grid-cols-2">
              {teaser.locked_sections.map((title) => (
                <li key={title} className="flex items-center gap-3 rounded-xl border border-dashed border-musper-line-on-dark px-4 py-3 text-sm text-musper-cream/70">
                  <Lock size={14} className="shrink-0 text-musper-orange" aria-hidden="true" />
                  <span>{title}</span>
                  <span className="sr-only">(locked)</span>
                </li>
              ))}
            </ul>
            <p className="mt-5 text-sm text-musper-cream/70">{teaser.share_note}</p>
          </>
        )}
        <Link
          to={BOOKING_URL}
          className="mt-6 inline-flex items-center gap-2 rounded-full bg-musper-orange px-6 py-3 text-sm font-medium text-musper-cream transition-colors hover:bg-musper-orange-dark focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-musper-cream"
        >
          <CalendarDays size={15} aria-hidden="true" />
          Book a session with Penny to go through your full report
        </Link>
      </div>
    </section>
  );
}

function SharedActions({ reportId }) {
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState(null);
  const download = async () => {
    setBusy(true);
    setError(null);
    try {
      await clientApi.downloadReportPdf(reportId);
    } catch (e) {
      setError(e?.message || 'Could not download the PDF. Try again in a moment.');
    } finally {
      setBusy(false);
    }
  };
  return (
    <div>
      <p className="text-sm text-musper-cream/80">Penny has shared your full report with you.</p>
      <div className="mt-4 flex flex-wrap gap-3">
        <Link
          to={`/dashboard/reports/${reportId}`}
          className="inline-flex items-center gap-2 rounded-full bg-musper-cream px-5 py-2.5 text-sm font-medium text-musper-green-deep transition-colors hover:bg-white"
        >
          Open full report <ArrowUpRight size={14} aria-hidden="true" />
        </Link>
        <button
          type="button"
          onClick={download}
          disabled={busy}
          className="inline-flex items-center gap-2 rounded-full border border-musper-line-on-dark px-5 py-2.5 text-sm font-medium text-musper-cream transition-colors hover:bg-musper-cream/10 disabled:opacity-60"
        >
          <FileDown size={14} aria-hidden="true" /> {busy ? 'Preparing PDF...' : 'Download PDF'}
        </button>
      </div>
      {error && <p className="mt-3 text-sm text-musper-orange">{error}</p>}
    </div>
  );
}
