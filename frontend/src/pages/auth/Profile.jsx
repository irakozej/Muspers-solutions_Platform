import { useState } from 'react';
import { motion } from 'framer-motion';
import { ShieldCheck, User as UserIcon, CheckCircle2, AlertCircle, LogOut } from 'lucide-react';
import FormField from '../../components/FormField';
import { useAuth } from '../../context/AuthContext';
import { authApi } from '../../services/auth';

export default function Profile() {
  const { user, updateProfile, logout } = useAuth();

  const [profileForm, setProfileForm] = useState({
    full_name: user?.full_name || '',
    email: user?.email || '',
  });
  const [profileStatus, setProfileStatus] = useState({ state: 'idle', message: '' });

  const [pwForm, setPwForm] = useState({ current_password: '', new_password: '' });
  const [pwStatus, setPwStatus] = useState({ state: 'idle', message: '' });

  const onSaveProfile = async (e) => {
    e.preventDefault();
    setProfileStatus({ state: 'submitting', message: '' });
    try {
      await updateProfile(profileForm);
      setProfileStatus({ state: 'success', message: 'Profile updated.' });
    } catch (err) {
      setProfileStatus({ state: 'error', message: err?.message || 'Update failed.' });
    }
  };

  const onChangePassword = async (e) => {
    e.preventDefault();
    if (pwForm.new_password.length < 8) {
      setPwStatus({ state: 'error', message: 'New password must be at least 8 characters.' });
      return;
    }
    setPwStatus({ state: 'submitting', message: '' });
    try {
      await authApi.changePassword(pwForm.current_password, pwForm.new_password);
      setPwStatus({ state: 'success', message: 'Password updated.' });
      setPwForm({ current_password: '', new_password: '' });
    } catch (err) {
      setPwStatus({ state: 'error', message: err?.message || 'Password change failed.' });
    }
  };

  if (!user) return null;
  const isAdvisor = user.role === 'advisor';

  return (
    <section className="container py-16 lg:py-24">
      {/* HEADER */}
      <motion.div
        initial={{ opacity: 0, y: 14 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6, ease: [0.22, 1, 0.36, 1] }}
        className="grid items-end gap-8 lg:grid-cols-12"
      >
        <div className="lg:col-span-8">
          <p className="eyebrow">Your account</p>
          <h1 className="mt-6 font-display text-[2.5rem] leading-[1.05] tracking-editorial sm:text-[3.5rem] text-balance">
            Hello, <span className="italic font-light text-musper-green">{user.full_name?.split(' ')[0] || 'friend'}</span>.
          </h1>
          <div className="mt-6 flex flex-wrap items-center gap-3 text-sm">
            <span className="inline-flex items-center gap-1.5 rounded-full bg-musper-green-soft px-3 py-1 font-medium text-musper-green">
              {isAdvisor ? <ShieldCheck size={13} /> : <UserIcon size={13} />}
              {user.role}
            </span>
            <span className="inline-flex items-center gap-1.5 rounded-full bg-musper-cream-soft px-3 py-1 text-musper-muted">
              {user.is_verified ? 'Email verified' : 'Email pending verification'}
            </span>
          </div>
        </div>
        <div className="lg:col-span-4 lg:justify-self-end">
          <button
            type="button"
            onClick={logout}
            className="inline-flex items-center gap-2 rounded-full border border-musper-line bg-musper-cream-soft px-5 py-2.5 text-sm font-medium text-musper-ink transition-all duration-300 hover:border-musper-orange/50 hover:text-musper-orange-dark"
          >
            <LogOut size={14} /> Sign out
          </button>
        </div>
      </motion.div>

      {/* ROLE BANNER */}
      {isAdvisor && (
        <div className="mt-12 rounded-3xl border border-musper-green/20 bg-musper-green-soft px-6 py-5">
          <p className="text-xs uppercase tracking-eyebrow text-musper-green">Advisor</p>
          <p className="mt-2 text-base text-musper-ink/85">
            You're signed in as a Musper advisor. The advisor dashboard lands in Phase 6 —
            for now your account is provisioned and your sessions are secure.
          </p>
        </div>
      )}

      {/* TWO COLUMNS */}
      <div className="mt-16 grid gap-10 lg:grid-cols-2 lg:gap-12">
        {/* PROFILE FORM */}
        <Card title="Account details" eyebrow="Profile">
          <form onSubmit={onSaveProfile} className="space-y-5">
            <FormField
              label="Full name"
              name="full_name"
              value={profileForm.full_name}
              onChange={(e) => setProfileForm((f) => ({ ...f, full_name: e.target.value }))}
              required
            />
            <FormField
              label="Email"
              type="email"
              name="email"
              value={profileForm.email}
              onChange={(e) => setProfileForm((f) => ({ ...f, email: e.target.value }))}
              required
            />
            <StatusLine status={profileStatus} />
            <SubmitButton busy={profileStatus.state === 'submitting'}>Save profile</SubmitButton>
          </form>
        </Card>

        {/* PASSWORD FORM */}
        <Card title="Change password" eyebrow="Security">
          <form onSubmit={onChangePassword} className="space-y-5">
            <FormField
              label="Current password"
              type="password"
              name="current_password"
              value={pwForm.current_password}
              onChange={(e) => setPwForm((f) => ({ ...f, current_password: e.target.value }))}
              autoComplete="current-password"
              required
            />
            <FormField
              label="New password"
              type="password"
              name="new_password"
              value={pwForm.new_password}
              onChange={(e) => setPwForm((f) => ({ ...f, new_password: e.target.value }))}
              autoComplete="new-password"
              hint="min. 8 characters"
              required
            />
            <StatusLine status={pwStatus} />
            <SubmitButton busy={pwStatus.state === 'submitting'}>Update password</SubmitButton>
            <p className="text-xs text-musper-muted">
              Changing your password signs you out everywhere else.
            </p>
          </form>
        </Card>
      </div>
    </section>
  );
}

function Card({ eyebrow, title, children }) {
  return (
    <div className="rounded-[2rem] border border-musper-line bg-musper-cream-soft p-6 shadow-soft sm:p-8">
      <p className="eyebrow">{eyebrow}</p>
      <h2 className="mt-4 font-display text-2xl leading-tight tracking-editorial sm:text-3xl">{title}</h2>
      <div className="mt-8">{children}</div>
    </div>
  );
}

function StatusLine({ status }) {
  if (status.state === 'success') {
    return (
      <div className="flex items-start gap-3 rounded-2xl border border-musper-green/20 bg-musper-green-soft px-4 py-3 text-sm text-musper-green">
        <CheckCircle2 size={16} className="mt-0.5 shrink-0" />
        <span>{status.message}</span>
      </div>
    );
  }
  if (status.state === 'error') {
    return (
      <div className="flex items-start gap-3 rounded-2xl border border-musper-orange/30 bg-musper-orange-soft px-4 py-3 text-sm text-musper-orange-dark">
        <AlertCircle size={16} className="mt-0.5 shrink-0" />
        <span>{status.message}</span>
      </div>
    );
  }
  return null;
}

function SubmitButton({ children, busy }) {
  return (
    <button
      type="submit"
      disabled={busy}
      className="inline-flex items-center gap-2 rounded-full bg-musper-green px-5 py-3 text-sm font-medium text-musper-cream shadow-soft transition-all duration-300 hover:-translate-y-0.5 hover:bg-musper-green-deep disabled:cursor-not-allowed disabled:opacity-60"
    >
      {busy ? 'Saving…' : children}
    </button>
  );
}
