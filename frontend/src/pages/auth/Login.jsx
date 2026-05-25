import { useState } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { AlertCircle } from 'lucide-react';
import AuthShell from '../../components/AuthShell';
import FormField from '../../components/FormField';
import { useAuth } from '../../context/AuthContext';

export default function Login() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const redirectTo = location.state?.from || '/profile';

  const [form, setForm] = useState({ email: '', password: '', remember: true });
  const [error, setError] = useState(null);
  const [busy, setBusy] = useState(false);

  const onChange = (e) => {
    const { name, value, type, checked } = e.target;
    setForm((f) => ({ ...f, [name]: type === 'checkbox' ? checked : value }));
  };

  const onSubmit = async (e) => {
    e.preventDefault();
    setBusy(true);
    setError(null);
    try {
      await login(form.email, form.password, form.remember);
      navigate(redirectTo, { replace: true });
    } catch (err) {
      setError(err?.message || 'We couldn\'t sign you in. Please try again.');
    } finally {
      setBusy(false);
    }
  };

  return (
    <AuthShell
      eyebrow="Sign in"
      title="Welcome back."
      accent="Sign in"
      footer={
        <p>
          New here?{' '}
          <Link to="/signup" className="text-musper-green underline decoration-musper-orange/60 underline-offset-4 hover:text-musper-green-deep">
            Create an account
          </Link>
          .
        </p>
      }
    >
      <form onSubmit={onSubmit} className="space-y-5">
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
          autoComplete="current-password"
          required
        />
        <div className="flex items-center justify-between">
          <label className="flex items-center gap-2 text-sm text-musper-ink/85">
            <input
              type="checkbox"
              name="remember"
              checked={form.remember}
              onChange={onChange}
              className="h-4 w-4 rounded border-musper-line text-musper-green focus:ring-musper-green/30"
            />
            Remember me for 30 days
          </label>
          <Link to="/forgot-password" className="text-sm text-musper-green hover:text-musper-green-deep">
            Forgot password?
          </Link>
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
          {busy ? 'Signing in…' : 'Sign in'}
        </button>
      </form>
    </AuthShell>
  );
}
