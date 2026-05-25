import { Link } from 'react-router-dom';
import { motion } from 'framer-motion';

// Shared editorial container for the auth pages.
// Left: brand panel with quote / artwork. Right: the form.
export default function AuthShell({ eyebrow, title, accent, children, footer }) {
  return (
    <section className="relative min-h-[calc(100vh-5rem)] overflow-hidden">
      <div className="container grid items-stretch gap-10 py-16 lg:grid-cols-12 lg:gap-16 lg:py-24">
        {/* Brand panel */}
        <motion.aside
          initial={{ opacity: 0, x: -16 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ duration: 0.7, ease: [0.22, 1, 0.36, 1] }}
          className="relative hidden overflow-hidden rounded-[2.5rem] surface-dark p-10 lg:col-span-5 lg:flex lg:flex-col lg:justify-between"
        >
          <div className="pointer-events-none absolute inset-0 bg-grain opacity-30 mix-blend-overlay" />
          <div className="pointer-events-none absolute -top-32 -right-24 h-72 w-72 rounded-full bg-musper-orange/15 blur-3xl" />
          <Link to="/" className="relative flex items-center gap-3">
            <span className="relative flex h-10 w-10 items-center justify-center rounded-full bg-musper-cream text-musper-green font-display text-xl font-semibold">
              M
              <span className="absolute -top-0.5 -right-0.5 h-2.5 w-2.5 rounded-full bg-musper-orange" />
            </span>
            <span className="font-display text-xl font-semibold tracking-editorial text-musper-cream">
              Musper Solutions
            </span>
          </Link>

          <div className="relative">
            <p className="text-eyebrow uppercase tracking-eyebrow text-musper-orange">A practical practice</p>
            <p className="mt-6 font-display text-3xl leading-[1.15] tracking-editorial text-musper-cream sm:text-4xl text-balance">
              "Equipping African businesses to scale through strategy and systems."
            </p>
            <p className="mt-6 text-sm text-musper-cream/55">
              Welcome. Sign in to your account or create one to access tools, sessions, and reports tailored to your business.
            </p>
          </div>

          <div className="relative flex flex-wrap items-center gap-x-6 gap-y-2 text-xs text-musper-cream/45">
            <span>Kigali · Rwanda</span>
            <span className="text-musper-cream/30">·</span>
            <span>est. 2011</span>
            <span className="text-musper-cream/30">·</span>
            <span>{accent || 'Phase 3 — Authentication'}</span>
          </div>
        </motion.aside>

        {/* Form panel */}
        <motion.div
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.7, delay: 0.06, ease: [0.22, 1, 0.36, 1] }}
          className="lg:col-span-7"
        >
          <div className="mx-auto max-w-xl">
            {eyebrow && <p className="eyebrow">{eyebrow}</p>}
            <h1 className="mt-6 font-display text-[2.25rem] leading-[1.05] tracking-editorial sm:text-[3rem] text-balance">
              {title}
            </h1>
            <div className="mt-10">{children}</div>
            {footer && <div className="mt-10 text-sm text-musper-muted">{footer}</div>}
          </div>
        </motion.div>
      </div>
    </section>
  );
}
