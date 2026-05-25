import { useState } from 'react';
import { Link } from 'react-router-dom';
import { AlertCircle, CheckCircle2 } from 'lucide-react';
import AuthShell from '../../components/AuthShell';
import FormField from '../../components/FormField';
import { authApi } from '../../services/auth';

export default function ForgotPassword() {
  const [email, setEmail] = useState('');
  const [status, setStatus] = useState({ state: 'idle', message: '' });

  const onSubmit = async (e) => {
    e.preventDefault();
    setStatus({ state: 'submitting', message: '' });
    try {
      const data = await authApi.forgotPassword(email);
      setStatus({
        state: 'success',
        message: data?.message || 'If an account exists, a reset link has been sent.',
      });
    } catch (err) {
      setStatus({ state: 'error', message: err?.message || 'Something went wrong.' });
    }
  };

  return (
    <AuthShell
      eyebrow="Forgot password"
      title="Reset your password."
      accent="Recover account"
      footer={
        <p>
          Remembered it?{' '}
          <Link to="/login" className="text-musper-green underline decoration-musper-orange/60 underline-offset-4 hover:text-musper-green-deep">
            Back to sign in
          </Link>
          .
        </p>
      }
    >
      {status.state === 'success' ? (
        <div className="rounded-3xl border border-musper-green/20 bg-musper-green-soft p-6">
          <div className="flex items-start gap-3 text-musper-green">
            <CheckCircle2 size={18} className="mt-0.5" />
            <div>
              <p className="font-medium">Reset link issued.</p>
              <p className="mt-1 text-sm text-musper-ink/80">{status.message}</p>
              <p className="mt-4 text-xs text-musper-muted">
                In development the link is logged to the backend console — check the uvicorn output.
              </p>
            </div>
          </div>
        </div>
      ) : (
        <form onSubmit={onSubmit} className="space-y-5">
          <p className="text-base leading-relaxed text-musper-muted">
            Enter the email address associated with your account, and we'll send you a link to reset your password.
          </p>
          <FormField
            label="Email"
            type="email"
            name="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            autoComplete="email"
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
            className="w-full rounded-full bg-musper-green px-6 py-3.5 text-sm font-medium text-musper-cream shadow-soft transition-all duration-300 hover:bg-musper-green-deep disabled:cursor-not-allowed disabled:opacity-60"
          >
            {status.state === 'submitting' ? 'Sending…' : 'Send reset link'}
          </button>
        </form>
      )}
    </AuthShell>
  );
}
