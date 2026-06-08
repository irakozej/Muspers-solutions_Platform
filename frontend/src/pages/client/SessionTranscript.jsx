import { useEffect, useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import { ArrowLeft, Star, MessageSquare } from 'lucide-react';
import { clientApi } from '../../services/dashboard';
import {
  ChatTranscript, PageHeading, StatusPill, formatRelative,
} from '../../components/dashboard/ReportShared';

export default function SessionTranscript() {
  const { id } = useParams();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [rateScore, setRateScore] = useState(0);
  const [rateHover, setRateHover] = useState(0);
  const [feedback, setFeedback] = useState('');
  const [rateBusy, setRateBusy] = useState(false);
  const [rateError, setRateError] = useState(null);

  const load = () =>
    clientApi.transcript(id).then((d) => {
      setData(d);
      setRateScore(d?.rating?.score || 0);
      setFeedback(d?.rating?.feedback || '');
      setLoading(false);
    }).catch((e) => { setRateError(e.message); setLoading(false); });

  useEffect(() => { setLoading(true); load(); /* eslint-disable-next-line */ }, [id]);

  const onSubmitRating = async (e) => {
    e.preventDefault();
    if (!rateScore) return;
    setRateBusy(true);
    setRateError(null);
    try {
      await clientApi.rate(id, rateScore, feedback || null);
      await load();
    } catch (err) {
      setRateError(err?.message || 'Failed to save rating.');
    } finally { setRateBusy(false); }
  };

  if (loading) return <p className="text-sm text-musper-muted">Loading...</p>;
  if (!data) return <p className="text-sm text-musper-muted">Session not found.</p>;

  return (
    <div className="space-y-10">
      <Link to="/dashboard/history" className="inline-flex items-center gap-1.5 text-sm text-musper-green hover:text-musper-green-deep">
        <ArrowLeft size={14} /> Back to history
      </Link>

      <PageHeading
        eyebrow="Session transcript"
        title={`Diagnostic from ${new Date(data.started_at).toLocaleDateString([], { day: 'numeric', month: 'long', year: 'numeric' })}`}
        description={data.completed_at ? `Completed ${formatRelative(data.completed_at)}` : 'In progress'}
        action={<StatusPill status={data.status} />}
      />

      {/* Transcript */}
      <section className="rounded-3xl border border-musper-line bg-musper-cream-soft/70 p-6 sm:p-8">
        <div className="flex items-baseline gap-3">
          <p className="eyebrow">Conversation</p>
          <p className="text-xs text-musper-muted">{data.messages.length} messages</p>
        </div>
        <h2 className="mt-3 font-display text-2xl tracking-editorial flex items-center gap-2">
          <MessageSquare size={20} className="text-musper-orange" />
          Full transcript
        </h2>
        <div className="mt-6">
          <ChatTranscript messages={data.messages} />
        </div>
      </section>

      {/* Rating form */}
      {data.status === 'completed' && (
        <section className="rounded-3xl border border-musper-orange/25 bg-musper-orange-soft/60 p-6 sm:p-8">
          <p className="eyebrow">{data.rating ? 'Update your rating' : 'Rate this session'}</p>
          <h2 className="mt-3 font-display text-2xl tracking-editorial">
            {data.rating ? 'Thanks for the feedback.' : 'How was this session?'}
          </h2>

          <form onSubmit={onSubmitRating} className="mt-6 space-y-5">
            <div className="flex items-center gap-2">
              {[1, 2, 3, 4, 5].map((n) => (
                <button
                  key={n}
                  type="button"
                  onMouseEnter={() => setRateHover(n)}
                  onMouseLeave={() => setRateHover(0)}
                  onClick={() => setRateScore(n)}
                  className="p-1 transition-transform duration-200 hover:scale-110"
                >
                  <Star
                    size={28}
                    fill={n <= (rateHover || rateScore) ? '#E07B1F' : 'none'}
                    stroke="#E07B1F"
                  />
                </button>
              ))}
              {rateScore > 0 && (
                <span className="ml-3 text-sm font-medium">{rateScore} / 5</span>
              )}
            </div>

            <label className="block">
              <span className="text-xs uppercase tracking-eyebrow text-musper-muted">
                Comments (optional)
              </span>
              <textarea
                value={feedback}
                onChange={(e) => setFeedback(e.target.value)}
                rows={4}
                placeholder="What worked? What could be improved?"
                className="mt-2 w-full resize-y rounded-2xl border border-musper-line bg-white px-4 py-3 text-sm focus:border-musper-green focus:outline-none focus:ring-2 focus:ring-musper-green/15"
              />
            </label>

            {rateError && (
              <p className="text-sm text-musper-orange-dark">{rateError}</p>
            )}

            <div className="flex items-center gap-3">
              <button
                type="submit"
                disabled={rateBusy || !rateScore}
                className="rounded-full bg-musper-orange px-6 py-3 text-sm font-medium text-musper-cream shadow-cta transition-all duration-300 hover:-translate-y-0.5 hover:bg-musper-orange-dark disabled:cursor-not-allowed disabled:opacity-60"
              >
                {rateBusy ? 'Saving...' : data.rating ? 'Update rating' : 'Submit rating'}
              </button>
              {data.rating && (
                <p className="text-xs text-musper-muted">
                  Last updated {formatRelative(data.rating.created_at)}
                </p>
              )}
            </div>
          </form>
        </section>
      )}
    </div>
  );
}
