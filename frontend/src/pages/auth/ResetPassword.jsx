import { useState } from 'react';
import { Link, useSearchParams, useNavigate } from 'react-router-dom';
import { AlertCircle, CheckCircle2 } from 'lucide-react';
import AuthShell from '../../components/AuthShell';
import FormField from '../../components/FormField';
import { authApi } from '../../services/auth';

export default function ResetPassword() {
  const [params] = useSearchParams();
  const navigate = useNavigate();
  const tokenFromUrl = params.get('token') || '';

  const [form, setForm] = useState({ token: tokenFromUrl, password: '' });
  const [status, setStatus] = useState({ state: 'idle', message: '' });

  const onChange = (e) => {
    const { name, value } = e.target;
    setForm((f) => ({ ...f, [name]: value }));
  };

  const onSubmit = async (e) => {
    e.preventDefault();
    if (form.password.length < 8) {
      setStatus({ state: 'error', message: 'Password must be at least 8 characters.' });
      return;
    }
    setStatus({ state: 'submitting', message: '' });
    try {
      await authApi.resetPassword(form.token, form.password);
      setStatus({ state: 'success', message: 'Password updated. Redirecting to sign in…' });
      setTimeout(() => navigate('/login'), 1500);
    } catch (err) {
      setStatus({ state: 'error', message: err?.message || 'Reset failed.' });
    }
  };

  return (
    <AuthShell
      eyebrow="Set a new password"
      title="Choose a new password."
      accent="Reset password"
      footer={
        <p>
          <Link to="/login" className="text-musper-green underline decoration-musper-orange/60 underline-offset-4 hover:text-musper-green-deep">
            Back to sign in
          </Link>
        </p>
      }
    >
      <form onSubmit={onSubmit} className="space-y-5">
        <FormField
          label="Reset token"
          name="token"
          value={form.token}
          onChange={onChange}
          hint="Auto-filled from the reset link"
          required
        />
        <FormField
          label="New password"
          type="password"
          name="password"
          value={form.password}
          onChange={onChange}
          autoComplete="new-password"
          hint="min. 8 characters"
          required
        />

        {status.state === 'error' && (
          <div className="flex items-start gap-3 rounded-2xl border border-musper-orange/30 bg-musper-orange-soft px-4 py-3 text-sm text-musper-orange-dark">
            <AlertCircle size={16} className="mt-0.5 shrink-0" />
            <span>{status.message}</span>
          </div>
        )}
        {status.state === 'success' && (
          <div className="flex items-start gap-3 rounded-2xl border border-musper-green/20 bg-musper-green-soft px-4 py-3 text-sm text-musper-green">
            <CheckCircle2 size={16} className="mt-0.5 shrink-0" />
            <span>{status.message}</span>
          </div>
        )}

        <button
          type="submit"
          disabled={status.state === 'submitting'}
          className="w-full rounded-full bg-musper-green px-6 py-3.5 text-sm font-medium text-musper-cream shadow-soft transition-all duration-300 hover:bg-musper-green-deep disabled:cursor-not-allowed disabled:opacity-60"
        >
          {status.state === 'submitting' ? 'Updating…' : 'Update password'}
        </button>
      </form>
    </AuthShell>
  );
}
