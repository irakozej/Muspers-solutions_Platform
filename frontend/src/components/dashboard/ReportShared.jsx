// Shared visual primitives used by both the advisor and client report views.
import { SCORE_BAND, DOMAIN_LABELS } from '../../services/dashboard';

export function ScoreBand({ band, score, size = 'md', label }) {
  const meta = SCORE_BAND[band || '—'] || SCORE_BAND['—'];
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

export function ReportCard({ report }) {
  if (!report) return null;
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
                {isAssistant ? 'Musper' : 'Client'}
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
  if (!value) return '—';
  const d = typeof value === 'string' ? new Date(value) : value;
  const diff = Date.now() - d.getTime();
  const days = Math.floor(diff / 86400000);
  if (days <= 0) return 'today';
  if (days === 1) return 'yesterday';
  if (days < 7) return `${days} days ago`;
  if (days < 30) return `${Math.floor(days / 7)} weeks ago`;
  return d.toLocaleDateString([], { day: 'numeric', month: 'short', year: 'numeric' });
}
