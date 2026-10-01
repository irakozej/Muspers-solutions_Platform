// Shared visual primitives used by both the advisor and client report views.
import { SCORE_BAND, DOMAIN_LABELS } from '../../services/dashboard';

export function ScoreBand({ band, score, size = 'md', label }) {
  const meta = SCORE_BAND[band || '-'] || SCORE_BAND['-'];
  const tones = {
    good: 'bg-musper-green text-musper-cream border-musper-green',
    mid: 'bg-musper-cream-soft text-musper-green border-musper-green/30',
    low: 'bg-musper-orange-soft text-musper-orange-dark border-musper-orange/40',
    neutral: 'bg-musper-cream-soft text-musper-muted border-musper-line',
  };
  const sizes = {
    sm: 'h-7 w-7 text-xs',
    md: 'h-9 w-9 text-sm',
    lg: 'h-12 w-12 text-base',
  };
  return (
    <div className="inline-flex items-center gap-3">
      <span
        className={[
          'inline-flex items-center justify-center rounded-full border font-display font-semibold tracking-editorial',
          tones[meta.tone],
          sizes[size],
        ].join(' ')}
      >
        {meta.label}
      </span>
      {label && (
        <span className="text-xs uppercase tracking-eyebrow text-musper-muted">{label}</span>
      )}
      {score !== undefined && score !== null && (
        <span className="font-display text-2xl font-medium tracking-editorial text-musper-ink">
          <span className="italic font-light">{Math.round(score)}</span>
          <span className="ml-0.5 text-sm text-musper-muted">/100</span>
        </span>
      )}
    </div>
  );
}

export function DomainGauge({ name, score }) {
  const pct = Math.max(0, Math.min(100, score || 0));
  const tone =
    pct >= 80 ? 'bg-musper-green' :
    pct >= 60 ? 'bg-musper-green-mid' :
    'bg-musper-orange';
  return (
    <div>
      <div className="flex items-baseline justify-between gap-3">
        <p className="text-sm font-medium tracking-tight text-musper-ink">
          {DOMAIN_LABELS[name] || name}
        </p>
        <p className="font-mono text-xs text-musper-muted">
          <span className="font-display text-lg font-medium italic text-musper-ink">
            {Math.round(score)}
          </span>
          <span className="ml-0.5">/100</span>
        </p>
      </div>
      <div className="mt-2 h-1.5 w-full overflow-hidden rounded-full bg-musper-line">
        <div className={`h-full ${tone}`} style={{ width: `${pct}%` }} />
      </div>
    </div>
  );
}

export function StatTile({ label, value, detail, accent }) {
  return (
    <div className="rounded-2xl border border-musper-line bg-musper-cream-soft p-5">
      <p className="text-xs uppercase tracking-eyebrow text-musper-muted">{label}</p>
      <p className="mt-3 font-display text-4xl font-medium leading-none tracking-editorial">
        <span className={accent ? 'text-musper-orange italic font-light' : 'italic font-light text-musper-green'}>
          {value}
        </span>
      </p>
      {detail && <p className="mt-3 text-xs text-musper-muted">{detail}</p>}
    </div>
  );
}

// Scan bar for MusperSolutions' root-cause framework: 1-5 scale, band-coloured.
function ScanGauge({ areaKey, name, score, summary, note, rationale, showRationale }) {
  const s = score ?? 0;
  const pct = Math.max(0, Math.min(100, (s / 5) * 100));
  const tone = s >= 4 ? 'bg-musper-green' : s === 3 ? 'bg-musper-green-mid' : 'bg-musper-orange';
  return (
    <div>
      <div className="flex items-baseline justify-between gap-3">
        <p className="text-sm font-medium tracking-tight text-musper-ink">
          <span className="mr-1.5 font-mono text-xs text-musper-muted-soft">{areaKey}</span>
          {name}
        </p>
        <p className="font-mono text-xs text-musper-muted">
          <span className="font-display text-lg font-medium italic text-musper-ink">
            {score ?? '-'}
          </span>
          <span className="ml-0.5">/5</span>
        </p>
      </div>
      <div className="mt-2 h-1.5 w-full overflow-hidden rounded-full bg-musper-line">
        <div className={`h-full ${tone}`} style={{ width: `${pct}%` }} />
      </div>
      <p className="mt-2 text-sm leading-relaxed text-musper-ink/80">{summary}</p>
      {note && (
        <p className="mt-1.5 text-xs italic leading-relaxed text-musper-orange-dark">{note}</p>
      )}
      {showRationale && rationale && (
        <p className="mt-2 text-xs leading-relaxed text-musper-muted">
          <span className="font-medium">Scoring note: </span>{rationale}
        </p>
      )}
    </div>
  );
}

const SCAN_AREAS = [
  ['A', 'Strategic Clarity'],
  ['B', 'Operations and Systems'],
  ['C', 'People and Capacity'],
  ['D', 'Funding and Resource Mobilization'],
  ['E', 'Governance and Structure'],
  ['F', 'Stakeholder and Customer Engagement'],
];

// Reports generated before per-area summaries existed have no summary text.
const NO_SUMMARY = 'No summary was recorded for this area. MusperSolutions will go over it with you.';

// MusperSolutions' Root-Cause Diagnostic Report, summary first.
// Every number here (scores, bands, strongest / weakest, priorities) is
// computed by the backend (report_summary.py); this component only lays it out.
// showRationales: true for the advisor view only; clients never see scoring notes.
function RootCauseReport({ report, showRationales = false }) {
  const snapshot = report.snapshot || {};
  const scan = report.scan_results || {};
  const diagnosis = report.diagnosis || {};
  const pathway = report.service_pathway || [];
  const engagement = report.engagement || {};
  const moneyHabits = report.money_habits || [];
  const priorities = report.priorities || [];
  const nextSteps = report.next_steps || [];
  const fhRow = report.financial_health_row;

  const snapshotRows = [
    ['Company', snapshot.company_name],
    ['Sector', snapshot.sector],
    ['Years in operation', snapshot.years_in_operation],
    ['Team size', snapshot.team_size],
    ['Revenue / budget range', snapshot.revenue_range],
    ['Diagnostic date', formatLongDate(report.created_at)],
    ['Completed by', snapshot.person_name
      ? `${snapshot.person_name}${snapshot.person_role ? `, ${snapshot.person_role}` : ''}`
      : null],
  ].filter(([, v]) => v);

  return (
    <article className="overflow-hidden rounded-[2rem] border border-musper-line bg-musper-cream-soft/70">
      <SummaryCover report={report} />

      <div className="p-7 sm:p-10">
        {/* Company snapshot */}
        <section>
          <SectionTitle>Company snapshot</SectionTitle>
          <div className="mt-4 grid gap-px overflow-hidden rounded-2xl border border-musper-line bg-musper-line sm:grid-cols-2">
            {snapshotRows.map(([label, value]) => (
              <div key={label} className="bg-white px-4 py-3">
                <p className="text-[0.65rem] uppercase tracking-eyebrow text-musper-muted">{label}</p>
                <p className="mt-1 text-sm font-medium text-musper-ink">{value}</p>
              </div>
            ))}
          </div>
        </section>

        {/* Money Habits */}
        <section id="money-habits" className="mt-12 scroll-mt-24">
          <SectionTitle hint="0 = critical gap, 3 = strong">Money habits</SectionTitle>
          {moneyHabits.some((m) => m.score !== null && m.score !== undefined) ? (
            <ul className="mt-5 space-y-3">
              {moneyHabits.map((m) => (
                <MoneyHabitRow key={m.key} habit={m} showRationale={showRationales} />
              ))}
            </ul>
          ) : (
            <p className="mt-4 rounded-2xl border border-dashed border-musper-line bg-white px-5 py-4 text-sm text-musper-muted">
              Money habits were not assessed in this interview. A new diagnostic will cover them.
            </p>
          )}
        </section>

        {/* Scan results, A to F plus G */}
        <section className="mt-12">
          <SectionTitle hint="1 = critical gap, 5 = strong">Scan results</SectionTitle>
          <div className="mt-5 grid gap-x-8 gap-y-6 sm:grid-cols-2">
            {SCAN_AREAS.map(([k, fallbackName]) => {
              const area = scan[k] || {};
              return (
                <ScanGauge
                  key={k}
                  areaKey={k}
                  name={area.name || fallbackName}
                  score={area.score}
                  summary={area.summary || NO_SUMMARY}
                  note={area.note}
                  rationale={area.rationale}
                  showRationale={showRationales}
                />
              );
            })}
            {fhRow && <FinancialHealthScanRow row={fhRow} />}
          </div>
        </section>

        {/* Diagnosis summary */}
        <section className="mt-12">
          <SectionTitle>Diagnosis summary</SectionTitle>
          <div className="mt-4 grid gap-4 lg:grid-cols-2">
            <div className="rounded-2xl border border-musper-line bg-white p-6">
              <p className="text-sm font-medium text-musper-muted">The presenting problem</p>
              <p className="mt-0.5 text-xs text-musper-muted-soft">What the client says is wrong</p>
              <p className="mt-4 text-[0.95rem] leading-relaxed text-musper-ink/85">
                {diagnosis.presenting_problem}
              </p>
            </div>
            <div className="relative rounded-2xl border-2 border-musper-green bg-musper-green-soft p-6">
              <span className="absolute -top-3 left-5 rounded-full bg-musper-green px-3 py-1 text-[0.65rem] font-medium uppercase tracking-eyebrow text-musper-cream">
                The root cause
              </span>
              <p className="mt-1 text-xs text-musper-green">What the diagnostic actually reveals</p>
              <p className="mt-4 text-[0.95rem] font-medium leading-relaxed text-musper-ink">
                {diagnosis.root_cause}
              </p>
              {diagnosis.root_cause_evidence?.length > 0 && (
                <ul className="mt-5 space-y-2 border-t border-musper-green/20 pt-4">
                  {diagnosis.root_cause_evidence.map((e, i) => (
                    <li key={i} className="flex items-start gap-2 text-xs leading-relaxed text-musper-ink/80">
                      <span className="mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full bg-musper-orange" />
                      {e}
                    </li>
                  ))}
                </ul>
              )}
            </div>
          </div>

          <div className="mt-4 grid gap-4 lg:grid-cols-2">
            <div className="rounded-2xl border border-musper-line bg-white p-6">
              <p className="text-sm font-medium text-musper-muted">What has already been tried</p>
              <ul className="mt-4 space-y-4">
                {(diagnosis.already_tried || []).map((t, i) => (
                  <li key={i}>
                    <p className="text-sm font-medium text-musper-ink">{t.attempt}</p>
                    <p className="mt-1 text-xs leading-relaxed text-musper-muted">
                      Why it did not work: {t.why_it_failed}
                    </p>
                  </li>
                ))}
              </ul>
            </div>
            <div className="rounded-2xl border border-musper-line bg-white p-6">
              <p className="text-sm font-medium text-musper-muted">Who owns this internally</p>
              <p className="mt-4 text-sm leading-relaxed text-musper-ink/85">{diagnosis.ownership}</p>
            </div>
          </div>
        </section>

        {/* Priority actions: ranked weakest first, so numbering is meaningful */}
        {priorities.length > 0 && (
          <section className="mt-12">
            <SectionTitle hint="weakest areas first, one step each">Priority actions</SectionTitle>
            <ol className="mt-5 space-y-3">
              {priorities.map((p, i) => (
                <li key={p.key} className="flex gap-4 rounded-2xl border border-musper-line bg-white p-5">
                  <span className="font-display text-2xl leading-none text-musper-orange">{i + 1}</span>
                  <div className="min-w-0 flex-1">
                    <div className="flex flex-wrap items-baseline justify-between gap-x-3 gap-y-1">
                      <p className="font-display text-lg leading-tight tracking-editorial">{p.name}</p>
                      <p className="text-xs text-musper-muted">
                        {p.kind === 'finance' ? 'Money habit' : 'Scan area'} · {p.score}/{p.max}
                      </p>
                    </div>
                    <p className="mt-2 text-sm leading-relaxed text-musper-ink/85">{p.first_step}</p>
                  </div>
                </li>
              ))}
            </ol>
          </section>
        )}

        {/* Service pathway */}
        {pathway.length > 0 && (
          <section className="mt-12">
            <SectionTitle hint="matched to the root cause">Recommended service pathway</SectionTitle>
            <ul className="mt-5 space-y-3">
              {pathway.map((p, i) => (
                <li key={i} className="rounded-2xl border border-musper-line bg-white p-5">
                  <p className="font-display text-lg leading-tight tracking-editorial">{p.service}</p>
                  <p className="mt-2 text-sm leading-relaxed text-musper-muted">{p.justification}</p>
                </li>
              ))}
            </ul>
          </section>
        )}

        {/* Engagement recommendation */}
        <section className="mt-10 rounded-2xl border border-musper-green/15 bg-musper-green-soft p-6">
          <p className="text-sm font-medium text-musper-green">Engagement recommendation</p>
          <div className="mt-4 grid gap-4 sm:grid-cols-2">
            <EngRow label="Engagement type" value={engagement.type_label || engagement.type} />
            <EngRow label="Estimated timeline" value={engagement.timeline} />
            <EngRow label="Estimated investment" value={engagement.investment_range} />
            <EngRow label="Next step" value={engagement.next_step} />
          </div>
        </section>

        {/* Next steps: a real sequence */}
        {nextSteps.length > 0 && (
          <section className="mt-12">
            <SectionTitle>Next steps</SectionTitle>
            <ol className="mt-5 grid gap-3 sm:grid-cols-3">
              {nextSteps.map((s, i) => (
                <li key={s.title} className="rounded-2xl border border-musper-line bg-white p-5">
                  <p className="font-display text-2xl leading-none text-musper-green">{i + 1}</p>
                  <p className="mt-3 text-sm font-medium text-musper-ink">{s.title}</p>
                  <p className="mt-1.5 text-xs leading-relaxed text-musper-muted">{s.detail}</p>
                </li>
              ))}
            </ol>
          </section>
        )}
      </div>
    </article>
  );
}

function formatLongDate(value) {
  return value
    ? new Date(value).toLocaleDateString([], { day: 'numeric', month: 'long', year: 'numeric' })
    : null;
}

function SectionTitle({ children, hint }) {
  return (
    <h3 className="font-display text-2xl leading-tight tracking-editorial text-musper-ink">
      {children}
      {hint && <span className="ml-2 font-sans text-xs font-normal tracking-normal text-musper-muted">({hint})</span>}
    </h3>
  );
}

// ── Summary cover ────────────────────────────────────────────

function SummaryCover({ report }) {
  const cover = report.summary_cover;
  const snapshot = report.snapshot || {};
  // Reports saved before the summary layer existed fall back to the headline only.
  const headline = cover?.combined?.headline || report.summary || 'What is actually going on.';
  const preparedFor = [snapshot.person_name, snapshot.person_role].filter(Boolean).join(', ');

  return (
    <header className="relative overflow-hidden bg-musper-green-deep px-7 pb-9 pt-8 text-musper-cream sm:px-10 sm:pb-11 sm:pt-10">
      <div aria-hidden="true" className="pointer-events-none absolute -right-24 -top-24 h-64 w-64 rounded-full border border-musper-orange/40" />
      <div aria-hidden="true" className="pointer-events-none absolute -right-36 -top-36 h-[22rem] w-[22rem] rounded-full border border-musper-line-on-dark" />

      <div className="relative flex flex-wrap items-baseline justify-between gap-x-6 gap-y-1 text-sm">
        <p className="font-display text-xl tracking-editorial">{snapshot.company_name || 'Diagnostic report'}</p>
        <p className="text-musper-cream/60">{formatLongDate(report.created_at)}</p>
      </div>
      {preparedFor && <p className="relative mt-1 text-sm text-musper-cream/70">Prepared for {preparedFor}</p>}

      {cover && (
        <div className="relative mt-8 flex flex-wrap items-end gap-x-10 gap-y-6">
          <ScoreRing label="Financial health" score={cover.financial_health} size="lg" />
          <ScoreRing label="Business health" score={cover.business_health} size="sm" />
          <div className="flex min-w-[14rem] flex-1 flex-col gap-2 pb-1">
            {cover.strongest && <AreaChip kind="strong" area={cover.strongest} />}
            {cover.weakest && <AreaChip kind="weak" area={cover.weakest} />}
          </div>
        </div>
      )}

      <div className="relative mt-9 border-t border-musper-line-on-dark pt-6">
        <p className="text-sm text-musper-orange">What the combined result tells us</p>
        <p className="mt-3 max-w-3xl font-display text-2xl font-medium leading-snug tracking-editorial text-balance sm:text-[1.75rem]">
          {headline}
        </p>
        {cover?.combined?.body && (
          <p className="mt-3 max-w-2xl text-[0.95rem] leading-relaxed text-musper-cream/80 text-pretty">
            {cover.combined.body}
          </p>
        )}
      </div>
    </header>
  );
}

function ScoreRing({ label, score, size }) {
  const big = size === 'lg';
  const dim = big ? 148 : 104;
  const stroke = big ? 10 : 7;
  const r = (dim - stroke) / 2;
  const circ = 2 * Math.PI * r;
  const assessed = score?.assessed;
  const pct = assessed ? Math.max(0, Math.min(100, score.pct)) : 0;
  const tone = !assessed ? 'transparent' : score.band === 'C' ? '#E07B1F' : score.band === 'B' ? '#F5F2EA' : '#7FB89E';

  return (
    <div className="flex items-center gap-4">
      <div className="relative shrink-0" style={{ width: dim, height: dim }}>
        <svg width={dim} height={dim} viewBox={`0 0 ${dim} ${dim}`} className="-rotate-90" role="img"
             aria-label={assessed ? `${label}: ${pct} out of 100, ${score.band_label}` : `${label}: not assessed`}>
          <circle cx={dim / 2} cy={dim / 2} r={r} fill="none" stroke="rgba(245,242,234,0.14)" strokeWidth={stroke} />
          <circle cx={dim / 2} cy={dim / 2} r={r} fill="none" stroke={tone} strokeWidth={stroke}
                  strokeLinecap="round" strokeDasharray={`${(pct / 100) * circ} ${circ}`} />
        </svg>
        <div className="absolute inset-0 flex flex-col items-center justify-center">
          {assessed ? (
            <span className={['font-display font-medium leading-none tracking-editorial', big ? 'text-[2.6rem]' : 'text-[1.7rem]'].join(' ')}>
              {pct}<span className={big ? 'text-lg' : 'text-sm'}>%</span>
            </span>
          ) : (
            <span className="px-3 text-center text-xs leading-tight text-musper-cream/60">Not assessed</span>
          )}
        </div>
      </div>
      <div>
        <p className={['font-medium', big ? 'text-base' : 'text-sm'].join(' ')}>{label}</p>
        {assessed ? (
          <p className="mt-1.5 inline-flex items-center gap-2 rounded-full border border-musper-line-on-dark px-2.5 py-1 text-xs">
            <span className="font-display font-semibold text-musper-orange">{score.band}</span>
            {score.band_label}
          </p>
        ) : (
          <p className="mt-1 text-xs text-musper-cream/60">{score?.band_label || 'Not assessed'}</p>
        )}
      </div>
    </div>
  );
}

function AreaChip({ kind, area }) {
  const strong = kind === 'strong';
  return (
    <div className={[
      'flex items-baseline justify-between gap-3 rounded-xl px-3.5 py-2.5 text-sm',
      strong ? 'bg-musper-cream/10' : 'bg-musper-orange/15 ring-1 ring-musper-orange/40',
    ].join(' ')}>
      <span className="min-w-0">
        <span className={['mr-2 text-xs', strong ? 'text-musper-cream/60' : 'text-musper-orange'].join(' ')}>
          {strong ? 'Strongest' : 'Needs most attention'}
        </span>
        <span className="font-medium">{area.name}</span>
      </span>
      <span className="shrink-0 text-xs text-musper-cream/70">{area.score}/{area.max}</span>
    </div>
  );
}

// ── Money Habits ────────────────────────────────────────────

function ScorePips({ score, max = 3, weak }) {
  return (
    <span className="inline-flex gap-1" role="img" aria-label={score === null || score === undefined ? 'Not scored' : `${score} out of ${max}`}>
      {Array.from({ length: max }, (_, i) => (
        <span key={i} className={[
          'h-2 w-5 rounded-full',
          score !== null && score !== undefined && i < score
            ? (weak ? 'bg-musper-orange' : 'bg-musper-green')
            : 'bg-musper-line',
        ].join(' ')} />
      ))}
    </span>
  );
}

function MoneyHabitRow({ habit, showRationale }) {
  const { name, score, summary, recommendation, weak, unclear, rationale } = habit;
  return (
    <li className={[
      'rounded-2xl border bg-white p-5',
      weak ? 'border-musper-orange/40 border-l-4 border-l-musper-orange' : 'border-musper-line',
    ].join(' ')}>
      <div className="flex flex-wrap items-center justify-between gap-x-4 gap-y-2">
        <p className="font-medium text-musper-ink">{name}</p>
        <span className="inline-flex items-center gap-2.5">
          <ScorePips score={score} weak={weak} />
          <span className="text-xs text-musper-muted">{score ?? '-'}/3</span>
        </span>
      </div>
      <p className="mt-2 text-sm leading-relaxed text-musper-ink/80">{summary || NO_SUMMARY}</p>
      {unclear && (
        <p className="mt-1.5 text-xs italic text-musper-orange-dark">
          The answer here stayed unclear, which is itself worth talking through.
        </p>
      )}
      {recommendation && (
        <p className={['mt-3 rounded-xl px-3.5 py-2.5 text-sm leading-relaxed', weak ? 'bg-musper-orange-soft text-musper-ink' : 'bg-musper-green-soft text-musper-ink/85'].join(' ')}>
          <span className={['font-medium', weak ? 'text-musper-orange-dark' : 'text-musper-green'].join(' ')}>Recommended: </span>
          {recommendation}
        </p>
      )}
      {showRationale && rationale && (
        <p className="mt-2 text-xs leading-relaxed text-musper-muted">
          <span className="font-medium">Scoring note: </span>{rationale}
        </p>
      )}
    </li>
  );
}

function FinancialHealthScanRow({ row }) {
  const pct = row.assessed ? row.pct : 0;
  const tone = row.band === 'A' ? 'bg-musper-green' : row.band === 'B' ? 'bg-musper-green-mid' : 'bg-musper-orange';
  return (
    <div className="rounded-2xl border border-musper-green/20 bg-musper-green-soft p-4 sm:col-span-2">
      <div className="flex items-baseline justify-between gap-3">
        <p className="text-sm font-medium tracking-tight text-musper-ink">
          <span className="mr-1.5 font-mono text-xs text-musper-muted-soft">G</span>
          {row.name}
        </p>
        <p className="text-xs text-musper-muted">
          {row.assessed ? (
            <>
              <span className="font-display text-lg font-medium italic text-musper-ink">{row.pct}</span>
              <span className="ml-0.5">/100 · {row.band} {row.band_label}</span>
            </>
          ) : 'Not assessed'}
        </p>
      </div>
      <div className="mt-2 h-1.5 w-full overflow-hidden rounded-full bg-musper-line">
        {row.assessed && <div className={`h-full ${tone}`} style={{ width: `${pct}%` }} />}
      </div>
      <p className="mt-2 text-sm leading-relaxed text-musper-ink/80">
        {row.summary}{' '}
        {row.assessed && <a href="#money-habits" className="font-medium text-musper-green underline underline-offset-2">Go to Money habits</a>}
      </p>
    </div>
  );
}

function EngRow({ label, value }) {
  if (!value) return null;
  return (
    <div className="rounded-xl bg-white/70 px-4 py-3">
      <p className="text-[0.65rem] uppercase tracking-eyebrow text-musper-muted">{label}</p>
      <p className="mt-1 text-sm leading-relaxed text-musper-ink/90">{value}</p>
    </div>
  );
}

export function ReportCard({ report, showRationales = false }) {
  if (!report) return null;
  if (report.report_type === 'root_cause') {
    return <RootCauseReport report={report} showRationales={showRationales} />;
  }
  const { headline, domains, summary, red_flags, priority_actions, suggested_topics } = report;

  return (
    <article className="rounded-[2rem] border border-musper-line bg-musper-cream-soft/70 p-7 sm:p-10">
      <header>
        <p className="eyebrow">Diagnostic report</p>
        <h2 className="mt-4 font-display text-3xl leading-tight tracking-editorial sm:text-4xl">
          Where the business stands.
        </h2>
      </header>

      {/* Headline */}
      <div className="mt-10 grid gap-6 sm:grid-cols-2">
        <div className="rounded-2xl border border-musper-line bg-white p-6">
          <p className="text-xs uppercase tracking-eyebrow text-musper-muted">GROW Overall</p>
          <div className="mt-4">
            <ScoreBand
              band={headline.grow_band}
              score={headline.grow_overall}
              size="lg"
            />
          </div>
          <p className="mt-4 text-xs text-musper-muted">
            Composite across Strategy, Customers, Money, Operations, Talent.
          </p>
        </div>
        <div className="rounded-2xl border border-musper-line bg-white p-6">
          <p className="text-xs uppercase tracking-eyebrow text-musper-muted">Finance Readiness</p>
          <div className="mt-4">
            <ScoreBand
              band={headline.finance_band}
              score={headline.finance_readiness}
              size="lg"
            />
          </div>
          <p className="mt-4 text-xs text-musper-muted">
            Weighted toward Money + Operations + Strategy.
          </p>
        </div>
      </div>

      {/* Domains */}
      <div className="mt-10">
        <p className="text-xs uppercase tracking-eyebrow text-musper-muted">Domain breakdown</p>
        <div className="mt-5 grid gap-5 sm:grid-cols-2 lg:grid-cols-5">
          {['strategy', 'customers', 'money', 'operations', 'talent'].map((d) => (
            <DomainGauge key={d} name={d} score={domains?.[d]} />
          ))}
        </div>
      </div>

      {/* Summary */}
      {summary && (
        <div className="mt-10 rounded-2xl border border-musper-green/15 bg-musper-green-soft px-6 py-5">
          <p className="text-xs uppercase tracking-eyebrow text-musper-green">Summary</p>
          <p className="mt-3 text-base leading-relaxed text-musper-ink/90 text-pretty">{summary}</p>
        </div>
      )}

      {/* Red flags */}
      {red_flags?.length > 0 && (
        <div className="mt-10">
          <p className="text-xs uppercase tracking-eyebrow text-musper-orange-dark">Red flags</p>
          <ul className="mt-4 space-y-2.5">
            {red_flags.map((f, i) => (
              <li key={i} className="flex items-start gap-3 rounded-xl border border-musper-orange/20 bg-musper-orange-soft px-4 py-3 text-sm text-musper-ink/90">
                <span className="mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full bg-musper-orange" />
                {f}
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Priority actions */}
      {priority_actions?.length > 0 && (
        <div className="mt-10">
          <p className="text-xs uppercase tracking-eyebrow text-musper-green">Priority actions</p>
          <ol className="mt-5 space-y-4">
            {priority_actions.map((a, i) => (
              <li key={i} className="rounded-2xl border border-musper-line bg-white p-5">
                <div className="flex items-start gap-4">
                  <span className="font-mono text-xs text-musper-muted pt-0.5">0{i + 1}</span>
                  <div className="flex-1">
                    <p className="font-display text-lg leading-tight tracking-editorial">{a.title}</p>
                    {a.detail && (
                      <p className="mt-2 text-sm leading-relaxed text-musper-muted">{a.detail}</p>
                    )}
                    <div className="mt-4 flex flex-wrap gap-4 text-xs">
                      {a.owner && (
                        <span className="flex items-center gap-1.5 text-musper-muted">
                          <span className="text-musper-muted-soft">Owner:</span>
                          <span className="text-musper-ink/80">{a.owner}</span>
                        </span>
                      )}
                      {a.horizon && (
                        <span className="flex items-center gap-1.5 text-musper-muted">
                          <span className="text-musper-muted-soft">Horizon:</span>
                          <span className="text-musper-ink/80">{a.horizon}</span>
                        </span>
                      )}
                    </div>
                  </div>
                </div>
              </li>
            ))}
          </ol>
        </div>
      )}

      {/* Coaching topics */}
      {suggested_topics?.length > 0 && (
        <div className="mt-10">
          <p className="text-xs uppercase tracking-eyebrow text-musper-green">Suggested coaching topics</p>
          <ul className="mt-4 flex flex-wrap gap-2">
            {suggested_topics.map((t, i) => (
              <li key={i} className="rounded-full border border-musper-line bg-white px-3.5 py-1.5 text-sm text-musper-ink/80">
                {t}
              </li>
            ))}
          </ul>
        </div>
      )}
    </article>
  );
}

export function EmptyState({ icon: Icon, title, body, action }) {
  return (
    <div className="rounded-3xl border border-dashed border-musper-line bg-musper-cream-soft/60 p-12 text-center">
      {Icon && (
        <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-full bg-musper-green-soft text-musper-green">
          <Icon size={22} strokeWidth={1.5} />
        </div>
      )}
      <h3 className="mt-6 font-display text-2xl leading-tight tracking-editorial">{title}</h3>
      {body && <p className="mx-auto mt-3 max-w-md text-sm text-musper-muted">{body}</p>}
      {action && <div className="mt-8">{action}</div>}
    </div>
  );
}

export function ChatTranscript({ messages }) {
  if (!messages?.length) return null;
  return (
    <div className="space-y-4">
      {messages.map((m) => {
        const isAssistant = m.role === 'assistant';
        return (
          <div key={m.id} className={isAssistant ? '' : 'pl-6 sm:pl-10'}>
            <div className="mb-1 flex items-center gap-2 text-xs uppercase tracking-eyebrow">
              <span className={isAssistant ? 'text-musper-green' : 'text-musper-orange'}>
                {isAssistant ? 'MusperSolutions' : 'Client'}
              </span>
              <span className="text-musper-muted-soft">
                {new Date(m.created_at).toLocaleString([], { dateStyle: 'short', timeStyle: 'short' })}
              </span>
            </div>
            <div
              className={[
                'rounded-2xl border px-4 py-3 text-[0.95rem] leading-relaxed',
                isAssistant
                  ? 'border-musper-line bg-musper-cream-soft text-musper-ink/90'
                  : 'border-musper-orange/25 bg-musper-orange-soft text-musper-ink/90',
              ].join(' ')}
            >
              {m.content}
            </div>
          </div>
        );
      })}
    </div>
  );
}

export function PageHeading({ eyebrow, title, description, action }) {
  return (
    <header className="flex flex-col gap-6 sm:flex-row sm:items-end sm:justify-between">
      <div>
        {eyebrow && <p className="eyebrow">{eyebrow}</p>}
        <h1 className="mt-3 font-display text-[2.25rem] leading-[1.05] tracking-editorial sm:text-[3rem]">
          {title}
        </h1>
        {description && (
          <p className="mt-4 max-w-2xl text-base leading-relaxed text-musper-muted">{description}</p>
        )}
      </div>
      {action && <div className="shrink-0">{action}</div>}
    </header>
  );
}

export function StatusPill({ status }) {
  const styles = {
    completed: 'bg-musper-green-soft text-musper-green border-musper-green/20',
    in_progress: 'bg-musper-orange-soft text-musper-orange-dark border-musper-orange/30',
    pending: 'bg-musper-cream-soft text-musper-muted border-musper-line',
    abandoned: 'bg-musper-cream-soft text-musper-muted border-musper-line',
    shared: 'bg-musper-green text-musper-cream border-musper-green',
    not_shared: 'bg-musper-cream-soft text-musper-muted border-musper-line',
  };
  const labels = {
    completed: 'Completed',
    in_progress: 'In progress',
    pending: 'Pending',
    abandoned: 'Abandoned',
    shared: 'Shared',
    not_shared: 'Private',
  };
  return (
    <span
      className={[
        'inline-flex items-center gap-1.5 rounded-full border px-2.5 py-1 text-xs font-medium',
        styles[status] || styles.pending,
      ].join(' ')}
    >
      {labels[status] || status}
    </span>
  );
}

export function formatRelative(value) {
  if (!value) return '-';
  const d = typeof value === 'string' ? new Date(value) : value;
  const diff = Date.now() - d.getTime();
  const days = Math.floor(diff / 86400000);
  if (days <= 0) return 'today';
  if (days === 1) return 'yesterday';
  if (days < 7) return `${days} days ago`;
  if (days < 30) return `${Math.floor(days / 7)} weeks ago`;
  return d.toLocaleDateString([], { day: 'numeric', month: 'short', year: 'numeric' });
}
