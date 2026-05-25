import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { AlertCircle, CheckCircle2 } from 'lucide-react';
import AuthShell from '../../components/AuthShell';
import FormField from '../../components/FormField';
import { useAuth } from '../../context/AuthContext';

export default function Signup() {
  const { register } = useAuth();
  const navigate = useNavigate();

  const [form, setForm] = useState({ full_name: '', email: '', password: '' });
  const [error, setError] = useState(null);
  const [busy, setBusy] = useState(false);

  const onChange = (e) => {
    const { name, value } = e.target;
    setForm((f) => ({ ...f, [name]: value }));
  };

  const onSubmit = async (e) => {
    e.preventDefault();
    if (form.password.length < 8) {
      setError('Password must be at least 8 characters.');
      return;
    }
    setBusy(true);
    setError(null);
    try {
      await register(form.email, form.password, form.full_name);
      navigate('/profile', { replace: true });
    } catch (err) {
      setError(err?.message || 'We couldn\'t create your account. Please try again.');
    } finally {
      setBusy(false);
    }
  };

  return (
    <AuthShell
      eyebrow="Create account"
      title="Begin your business journey."
      accent="Create account"
      footer={
        <p>
          Already have an account?{' '}
          <Link to="/login" className="text-musper-green underline decoration-musper-orange/60 underline-offset-4 hover:text-musper-green-deep">
            Sign in instead
          </Link>
          .
        </p>
      }
    >
      <form onSubmit={onSubmit} className="space-y-5">
        <FormField
          label="Full name"
          name="full_name"
          value={form.full_name}
          onChange={onChange}
          autoComplete="name"
          required
        />
        <FormField
          label="Email"
          type="email"
          name="email"
          value={form.email}
          onChange={onChange}
          autoComplete="email"
          required
        />
        <FormField
          label="Password"
          type="password"
          name="password"
          value={form.password}
          onChange={onChange}
          autoComplete="new-password"
          required
          hint="min. 8 characters"
        />

        <div className="flex items-start gap-2 text-xs text-musper-muted">
          <CheckCircle2 size={14} className="mt-0.5 shrink-0 text-musper-green" />
          <span>
            By creating an account you agree to our terms and our handling of your details.
            We never share contact information.
          </span>
        </div>

        {error && (
          <div className="flex items-start gap-3 rounded-2xl border border-musper-orange/30 bg-musper-orange-soft px-4 py-3 text-sm text-musper-orange-dark">
            <AlertCircle size={16} className="mt-0.5 shrink-0" />
            <span>{error}</span>
          </div>
        )}

        <button
          type="submit"
          disabled={busy}
          className="w-full rounded-full bg-musper-green px-6 py-3.5 text-sm font-medium text-musper-cream shadow-soft transition-all duration-300 hover:bg-musper-green-deep disabled:cursor-not-allowed disabled:opacity-60"
        >
          {busy ? 'Creating account…' : 'Create my account'}
        </button>
      </form>
    </AuthShell>
  );
}
