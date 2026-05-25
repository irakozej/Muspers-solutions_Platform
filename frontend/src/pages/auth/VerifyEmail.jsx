import { useEffect, useState } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import { CheckCircle2, AlertCircle, Loader2 } from 'lucide-react';
import AuthShell from '../../components/AuthShell';
import FormField from '../../components/FormField';
import { authApi } from '../../services/auth';

export default function VerifyEmail() {
  const [params] = useSearchParams();
  const initialToken = params.get('token') || '';
  const [token, setToken] = useState(initialToken);
  const [status, setStatus] = useState({ state: 'idle', message: '' });

  const submit = async (raw) => {
    if (!raw) return;
    setStatus({ state: 'submitting', message: '' });
    try {
      const data = await authApi.verifyEmail(raw);
      setStatus({
        state: 'success',
        message: `Verified — welcome, ${data?.full_name || data?.email}.`,
      });
    } catch (err) {
      setStatus({ state: 'error', message: err?.message || 'Verification failed.' });
    }
  };

  // If a token was supplied via the URL, verify automatically.
  useEffect(() => {
    if (initialToken) submit(initialToken);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const onSubmit = (e) => { e.preventDefault(); submit(token); };

  return (
    <AuthShell
      eyebrow="Email verification"
      title="Confirm your email."
      accent="Verify email"
      footer={
        <p>
          <Link to="/login" className="text-musper-green underline decoration-musper-orange/60 underline-offset-4 hover:text-musper-green-deep">
            Back to sign in
          </Link>
        </p>
      }
    >
      {status.state === 'success' ? (
        <div className="rounded-3xl border border-musper-green/20 bg-musper-green-soft p-6 text-musper-green">
          <div className="flex items-start gap-3">
            <CheckCircle2 size={18} className="mt-0.5" />
            <div>
              <p className="font-medium">{status.message}</p>
              <p className="mt-3 text-sm text-musper-ink/80">
                You can now sign in and access your profile.
              </p>
            </div>
          </div>
        </div>
      ) : (
        <form onSubmit={onSubmit} className="space-y-5">
          <p className="text-base leading-relaxed text-musper-muted">
            Paste the verification token from your email below — or just open the link directly.
            <span className="block mt-2 text-xs text-musper-muted-soft">
              In dev mode, new accounts are auto-verified, so this step is informational only.
            </span>
          </p>
          <FormField
            label="Verification token"
            name="token"
            value={token}
            onChange={(e) => setToken(e.target.value)}
            required
          />

          {status.state === 'error' && (
            <div className="flex items-start gap-3 rounded-2xl border border-musper-orange/30 bg-musper-orange-soft px-4 py-3 text-sm text-musper-orange-dark">
              <AlertCircle size={16} className="mt-0.5 shrink-0" />
              <span>{status.message}</span>
            </div>
          )}
          <button
            type="submit"
            disabled={status.state === 'submitting'}
            className="inline-flex w-full items-center justify-center gap-2 rounded-full bg-musper-green px-6 py-3.5 text-sm font-medium text-musper-cream shadow-soft transition-all duration-300 hover:bg-musper-green-deep disabled:cursor-not-allowed disabled:opacity-60"
          >
            {status.state === 'submitting' && <Loader2 size={15} className="animate-spin" />}
            {status.state === 'submitting' ? 'Verifying…' : 'Verify email'}
          </button>
        </form>
      )}
    </AuthShell>
  );
}
