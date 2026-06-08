import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { CheckCircle2, AlertCircle, ArrowUpRight } from 'lucide-react';
import FormField from '../../components/FormField';
import { clientApi } from '../../services/dashboard';
import { useAuth } from '../../context/AuthContext';
import { PageHeading } from '../../components/dashboard/ReportShared';

export default function ClientProfile() {
  const { user } = useAuth();
  const [me, setMe] = useState(null);
  const [form, setForm] = useState({ business_name: '', sector: '', location: '', employee_count: '' });
  const [status, setStatus] = useState({ state: 'idle', message: '' });

  useEffect(() => {
    clientApi.me().then((d) => {
      setMe(d);
      // Fetch sessions has no business fields, we need the raw client row.
      // For now we keep the form prefill simple from /me.
      setForm({
        business_name: d.business_name || '',
        sector: d.sector || '',
        location: '',
        employee_count: '',
      });
    });
  }, []);

  const onChange = (e) => setForm((f) => ({ ...f, [e.target.name]: e.target.value }));

  const onSubmit = async (e) => {
    e.preventDefault();
    setStatus({ state: 'submitting', message: '' });
    try {
      const payload = {
        business_name: form.business_name || undefined,
        sector: form.sector || undefined,
        location: form.location || undefined,
        employee_count: form.employee_count ? Number(form.employee_count) : undefined,
      };
      const updated = await clientApi.updateBusinessProfile(payload);
      setMe(updated);
      setStatus({ state: 'success', message: 'Business profile updated.' });
    } catch (err) {
      setStatus({ state: 'error', message: err?.message || 'Update failed.' });
    }
  };

  return (
    <div className="space-y-12">
      <PageHeading
        eyebrow="Profile"
        title="Your business + account."
        description="Keep your business profile current, it's what Penny sees when she pulls up your case."
      />

      <div className="grid gap-8 lg:grid-cols-2">
        {/* Business profile */}
        <section className="rounded-3xl border border-musper-line bg-musper-cream-soft/70 p-6 sm:p-8">
          <p className="eyebrow">Business</p>
          <h2 className="mt-3 font-display text-2xl tracking-editorial">Your company.</h2>
          <form onSubmit={onSubmit} className="mt-6 space-y-5">
            <FormField label="Business name" name="business_name" value={form.business_name} onChange={onChange} required />
            <FormField label="Sector" name="sector" value={form.sector} onChange={onChange} />
            <FormField label="Location" name="location" value={form.location} onChange={onChange} />
            <FormField label="Employee count" name="employee_count" type="number" value={form.employee_count} onChange={onChange} />

            {status.state === 'success' && (
              <div className="flex items-start gap-3 rounded-2xl border border-musper-green/20 bg-musper-green-soft px-4 py-3 text-sm text-musper-green">
                <CheckCircle2 size={16} className="mt-0.5 shrink-0" />
                <span>{status.message}</span>
              </div>
            )}
            {status.state === 'error' && (
              <div className="flex items-start gap-3 rounded-2xl border border-musper-orange/30 bg-musper-orange-soft px-4 py-3 text-sm text-musper-orange-dark">
                <AlertCircle size={16} className="mt-0.5 shrink-0" />
                <span>{status.message}</span>
              </div>
            )}

            <button
              type="submit"
              disabled={status.state === 'submitting'}
              className="rounded-full bg-musper-green px-6 py-3 text-sm font-medium text-musper-cream shadow-soft hover:bg-musper-green-deep disabled:opacity-60"
            >
              {status.state === 'submitting' ? 'Saving...' : 'Save business profile'}
            </button>
          </form>
        </section>

        {/* Personal */}
        <section className="rounded-3xl border border-musper-line bg-musper-cream-soft/70 p-6 sm:p-8">
          <p className="eyebrow">Personal</p>
          <h2 className="mt-3 font-display text-2xl tracking-editorial">Account details.</h2>
          <div className="mt-6 space-y-3 text-sm">
            <Row label="Name" value={user?.full_name || '-'} />
            <Row label="Email" value={user?.email} />
            <Row label="Role" value={user?.role} />
          </div>
          <Link
            to="/profile"
            className="mt-6 inline-flex items-center gap-2 rounded-full bg-musper-green px-5 py-2.5 text-sm font-medium text-musper-cream hover:bg-musper-green-deep"
          >
            Manage personal account <ArrowUpRight size={14} />
          </Link>
        </section>
      </div>
    </div>
  );
}

function Row({ label, value }) {
  return (
    <div className="flex items-center justify-between rounded-xl border border-musper-line bg-white px-4 py-3">
      <span className="text-xs uppercase tracking-eyebrow text-musper-muted">{label}</span>
      <span className="truncate text-sm font-medium text-musper-ink">{value}</span>
    </div>
  );
}
