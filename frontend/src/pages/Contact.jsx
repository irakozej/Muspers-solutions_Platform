import { useState } from 'react';
import { Mail, Phone, MapPin, Calendar, MessageSquare, CheckCircle2, AlertCircle } from 'lucide-react';
import Reveal from '../components/Reveal';
import { contactInfo } from '../data/site';
import { api } from '../services/api';

const initialForm = {
  name: '',
  email: '',
  organization: '',
  subject: '',
  message: '',
};

export default function Contact() {
  const [form, setForm] = useState(initialForm);
  const [status, setStatus] = useState({ state: 'idle', message: '' });

  const onChange = (e) => {
    const { name, value } = e.target;
    setForm((f) => ({ ...f, [name]: value }));
  };

  const onSubmit = async (e) => {
    e.preventDefault();
    setStatus({ state: 'submitting', message: '' });
    try {
      await api.submitContact({
        name: form.name,
        email: form.email,
        organization: form.organization || null,
        subject: form.subject,
        message: form.message,
      });
      setStatus({ state: 'success', message: 'Thanks — your message is with us. We\'ll reply within two business days.' });
      setForm(initialForm);
    } catch (err) {
      setStatus({
        state: 'error',
        message: err?.message || 'Something went wrong. Please try again or email us directly.',
      });
    }
  };

  return (
    <div className="overflow-x-hidden">
      {/* HERO */}
      <section className="pt-24 pb-12 lg:pt-32 lg:pb-16">
        <div className="container">
          <Reveal>
            <p className="eyebrow">Contact</p>
          </Reveal>
          <Reveal delay={0.05}>
            <h1 className="mt-6 max-w-5xl font-display text-[2.5rem] font-medium leading-[1.05] tracking-editorial sm:text-[4rem] lg:text-[5rem] text-balance">
              Let's start a{' '}
              <span className="italic font-light text-musper-green">conversation</span>.
            </h1>
          </Reveal>
          <Reveal delay={0.15}>
            <p className="mt-10 max-w-2xl text-lg leading-relaxed text-musper-muted text-pretty">
              For partnerships, program collaborations, or advisory engagements
              — tell us a little about what you're working on. We reply within
              two business days.
            </p>
          </Reveal>
        </div>
      </section>

      {/* FORM + DETAILS */}
      <section className="border-t border-musper-line py-16 lg:py-24">
        <div className="container grid gap-14 lg:grid-cols-12 lg:gap-16">
          {/* Form */}
          <Reveal className="lg:col-span-7">
            <form
              onSubmit={onSubmit}
              className="rounded-[2rem] border border-musper-line bg-musper-cream-soft p-6 shadow-soft sm:p-10"
            >
              <p className="eyebrow">Send us a note</p>
              <h2 className="mt-4 font-display text-3xl leading-[1.1] tracking-editorial sm:text-4xl">
                Tell us about your project.
              </h2>

              <div className="mt-10 grid gap-6 sm:grid-cols-2">
                <Field label="Your name" name="name" value={form.name} onChange={onChange} required />
                <Field label="Email" type="email" name="email" value={form.email} onChange={onChange} required />
                <Field label="Organisation (optional)" name="organization" value={form.organization} onChange={onChange} />
                <Field label="Subject" name="subject" value={form.subject} onChange={onChange} required />
                <div className="sm:col-span-2">
                  <Field
                    label="Message"
                    name="message"
                    value={form.message}
                    onChange={onChange}
                    required
                    textarea
                  />
                </div>
              </div>

              {status.state === 'success' && (
                <div className="mt-6 flex items-start gap-3 rounded-2xl border border-musper-green/20 bg-musper-green-soft px-5 py-4 text-sm text-musper-green">
                  <CheckCircle2 size={18} className="mt-0.5 shrink-0" />
                  <span>{status.message}</span>
                </div>
              )}
              {status.state === 'error' && (
                <div className="mt-6 flex items-start gap-3 rounded-2xl border border-musper-orange/30 bg-musper-orange-soft px-5 py-4 text-sm text-musper-orange-dark">
                  <AlertCircle size={18} className="mt-0.5 shrink-0" />
                  <span>{status.message}</span>
                </div>
              )}

              <div className="mt-8 flex flex-wrap items-center justify-between gap-4">
                <p className="text-xs text-musper-muted">
                  By submitting you agree to our handling of this enquiry. We don't share contact details.
                </p>
                <button
                  type="submit"
                  disabled={status.state === 'submitting'}
                  className="inline-flex items-center gap-2 rounded-full bg-musper-green px-6 py-3 text-sm font-medium text-musper-cream shadow-soft transition-all duration-300 hover:-translate-y-0.5 hover:bg-musper-green-deep disabled:cursor-not-allowed disabled:opacity-60"
                >
                  {status.state === 'submitting' ? 'Sending…' : 'Send message'}
                </button>
              </div>
            </form>
          </Reveal>

          {/* Details + map */}
          <div className="lg:col-span-5 lg:pl-4">
            <Reveal>
              <p className="eyebrow">Reach us directly</p>
              <ul className="mt-6 space-y-5 text-base">
                <DetailRow icon={MapPin} label="Office">
                  {contactInfo.address.line1}<br />{contactInfo.address.line2}
                </DetailRow>
                <DetailRow icon={Phone} label="Phone">
                  <a href={`tel:${contactInfo.phone.replace(/\s/g, '')}`} className="hover:text-musper-green">
                    {contactInfo.phone}
                  </a>
                </DetailRow>
                <DetailRow icon={Mail} label="Email">
                  <a href={`mailto:${contactInfo.email}`} className="hover:text-musper-green">
                    {contactInfo.email}
                  </a>
                </DetailRow>
                <DetailRow icon={MessageSquare} label="WhatsApp">
                  <a href={contactInfo.whatsapp} target="_blank" rel="noreferrer" className="hover:text-musper-green">
                    Open a chat
                  </a>
                </DetailRow>
                <DetailRow icon={Calendar} label="Book a consultation">
                  <span className="text-musper-muted">Calendar booking coming soon — drop us a note in the meantime.</span>
                </DetailRow>
              </ul>
            </Reveal>

            <Reveal delay={0.1}>
              <div className="mt-10 overflow-hidden rounded-[2rem] border border-musper-line shadow-soft">
                <iframe
                  title="Musper Solutions office — Kigali, Rwanda"
                  src="https://www.google.com/maps?q=Nyarugenge,Kigali,Rwanda&z=14&output=embed"
                  width="100%"
                  height="320"
                  style={{ border: 0, filter: 'grayscale(0.25) contrast(1.02)' }}
                  loading="lazy"
                  referrerPolicy="no-referrer-when-downgrade"
                  allowFullScreen
                />
              </div>
            </Reveal>
          </div>
        </div>
      </section>
    </div>
  );
}

function Field({ label, name, value, onChange, type = 'text', required, textarea }) {
  const cls =
    'w-full rounded-2xl border border-musper-line bg-white px-4 py-3 text-sm text-musper-ink placeholder:text-musper-muted-soft transition-colors duration-300 focus:border-musper-green focus:outline-none focus:ring-2 focus:ring-musper-green/15';
  return (
    <label className="block">
      <span className="block text-xs font-medium uppercase tracking-eyebrow text-musper-muted">
        {label}
      </span>
      {textarea ? (
        <textarea
          name={name}
          value={value}
          onChange={onChange}
          required={required}
          rows={6}
          className={`${cls} mt-2 resize-y`}
          placeholder="Tell us a little about the project — goals, timeline, who's involved."
        />
      ) : (
        <input
          type={type}
          name={name}
          value={value}
          onChange={onChange}
          required={required}
          className={`${cls} mt-2`}
        />
      )}
    </label>
  );
}

function DetailRow({ icon: Icon, label, children }) {
  return (
    <li className="flex items-start gap-4">
      <span className="mt-1 flex h-9 w-9 shrink-0 items-center justify-center rounded-full border border-musper-line bg-musper-cream-soft text-musper-green">
        <Icon size={16} />
      </span>
      <div>
        <p className="text-xs uppercase tracking-eyebrow text-musper-muted">{label}</p>
        <div className="mt-1 text-musper-ink/90">{children}</div>
      </div>
    </li>
  );
}
