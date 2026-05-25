import { Link } from 'react-router-dom';
import { useState } from 'react';
import { ArrowUpRight, Mail, Phone, MapPin } from 'lucide-react';
import { brand, contactInfo, navLinks } from '../data/site';

export default function Footer() {
  const [email, setEmail] = useState('');
  const [submitted, setSubmitted] = useState(false);

  // Placeholder newsletter handler — Mailchimp wiring lands in a later phase.
  const onSubscribe = (e) => {
    e.preventDefault();
    if (!email) return;
    setSubmitted(true);
    setEmail('');
  };

  return (
    <footer className="relative mt-32 surface-dark">
      <div className="pointer-events-none absolute inset-0 bg-grain opacity-30 mix-blend-overlay" />

      <div className="container relative grid gap-16 py-20 lg:grid-cols-12 lg:gap-12">
        {/* Wordmark + tagline */}
        <div className="lg:col-span-5">
          <div className="flex items-center gap-3">
            <span className="relative flex h-10 w-10 items-center justify-center rounded-full bg-musper-cream text-musper-green font-display text-xl font-semibold">
              M
              <span className="absolute -top-0.5 -right-0.5 h-2.5 w-2.5 rounded-full bg-musper-orange" />
            </span>
            <span className="font-display text-2xl font-semibold tracking-editorial text-musper-cream">
              Musper Solutions
            </span>
          </div>
          <p className="mt-8 max-w-md font-display text-2xl leading-tight tracking-editorial text-musper-cream/90 text-balance">
            {brand.tagline}
          </p>
          <p className="mt-6 text-sm text-musper-cream/55 max-w-md">
            A Rwandan-built consultancy partnering with entrepreneurs, financial institutions, and
            development partners across the continent.
          </p>
        </div>

        {/* Newsletter */}
        <div className="lg:col-span-4">
          <p className="eyebrow !text-musper-orange">Newsletter</p>
          <h3 className="mt-4 font-display text-3xl tracking-editorial text-musper-cream">
            Thinking in our inbox.
          </h3>
          <p className="mt-3 text-sm text-musper-cream/55">
            Quarterly notes on entrepreneurship, SME finance, and what's working in African business.
          </p>
          {submitted ? (
            <p className="mt-6 rounded-2xl border border-musper-cream/15 bg-musper-cream/5 px-5 py-4 text-sm text-musper-cream/85">
              Thanks — we'll be in touch when the next dispatch is ready.
            </p>
          ) : (
            <form onSubmit={onSubscribe} className="mt-6 flex items-center gap-2 rounded-full border border-musper-cream/20 bg-musper-cream/5 p-1.5 focus-within:border-musper-orange/60">
              <input
                type="email"
                required
                placeholder="you@company.com"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="flex-1 bg-transparent px-4 py-2 text-sm text-musper-cream placeholder:text-musper-cream/40 focus:outline-none"
              />
              <button
                type="submit"
                className="flex items-center gap-1.5 rounded-full bg-musper-orange px-4 py-2 text-sm font-medium text-musper-cream transition-colors hover:bg-musper-orange-dark"
              >
                Subscribe <ArrowUpRight size={14} />
              </button>
            </form>
          )}
        </div>

        {/* Sitemap + contact */}
        <div className="lg:col-span-3">
          <p className="eyebrow !text-musper-orange">Navigate</p>
          <ul className="mt-4 grid grid-cols-2 gap-y-2 lg:grid-cols-1">
            {navLinks.map((link) => (
              <li key={link.to}>
                <Link
                  to={link.to}
                  className="group inline-flex items-center gap-1 text-sm text-musper-cream/80 transition-colors hover:text-musper-orange"
                >
                  {link.label}
                  <ArrowUpRight
                    size={13}
                    className="opacity-0 transition-all duration-300 group-hover:translate-x-0.5 group-hover:-translate-y-0.5 group-hover:opacity-100"
                  />
                </Link>
              </li>
            ))}
          </ul>
        </div>
      </div>

      <div className="rule !bg-musper-line-on-dark" />

      <div className="container relative grid gap-8 py-8 text-sm text-musper-cream/65 lg:grid-cols-3">
        <div className="flex items-center gap-2">
          <MapPin size={14} className="text-musper-orange" />
          <span>{contactInfo.address.line1}, {contactInfo.address.line2}</span>
        </div>
        <div className="flex items-center gap-2">
          <Mail size={14} className="text-musper-orange" />
          <a href={`mailto:${contactInfo.email}`} className="hover:text-musper-cream">{contactInfo.email}</a>
        </div>
        <div className="flex items-center gap-2 lg:justify-end">
          <Phone size={14} className="text-musper-orange" />
          <a href={`tel:${contactInfo.phone.replace(/\s/g, '')}`} className="hover:text-musper-cream">{contactInfo.phone}</a>
        </div>
      </div>

      <div className="rule !bg-musper-line-on-dark" />

      <div className="container relative flex flex-col gap-3 py-6 text-xs text-musper-cream/45 sm:flex-row sm:items-center sm:justify-between">
        <p>© {new Date().getFullYear()} {brand.legalName}. All rights reserved.</p>
        <div className="flex items-center gap-5">
          {contactInfo.socials.map((s) => (
            <a key={s.label} href={s.href} target="_blank" rel="noreferrer" className="hover:text-musper-orange">
              {s.label}
            </a>
          ))}
        </div>
      </div>
    </footer>
  );
}
