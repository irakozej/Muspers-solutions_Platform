import { motion } from 'framer-motion';
import { Sparkles, ArrowLeft } from 'lucide-react';
import Button from '../components/Button';

export default function Diagnostic() {
  return (
    <section className="relative flex min-h-[calc(100vh-5rem)] items-center justify-center overflow-hidden surface-dark">
      <div className="pointer-events-none absolute inset-0 bg-grain opacity-30 mix-blend-overlay" />
      <div className="pointer-events-none absolute -top-32 left-1/2 h-[36rem] w-[36rem] -translate-x-1/2 rounded-full bg-musper-orange/15 blur-3xl" />

      <div className="container relative text-center">
        <motion.div
          initial={{ opacity: 0, scale: 0.85 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 0.8, ease: [0.22, 1, 0.36, 1] }}
          className="mx-auto flex h-20 w-20 items-center justify-center rounded-full border border-musper-orange/40 bg-musper-cream/5 text-musper-orange"
        >
          <Sparkles size={28} strokeWidth={1.5} />
        </motion.div>

        <motion.p
          initial={{ opacity: 0, y: 14 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.7, delay: 0.1, ease: [0.22, 1, 0.36, 1] }}
          className="mt-10 text-eyebrow uppercase tracking-eyebrow text-musper-orange"
        >
          The Musper Assistant
        </motion.p>

        <motion.h1
          initial={{ opacity: 0, y: 18 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, delay: 0.18, ease: [0.22, 1, 0.36, 1] }}
          className="mx-auto mt-6 max-w-3xl font-display text-[2.5rem] leading-[1.05] tracking-editorial text-musper-cream sm:text-[4rem] text-balance"
        >
          A guided business diagnostic, coming{' '}
          <span className="italic font-light text-musper-cream/80">soon</span>.
        </motion.h1>

        <motion.p
          initial={{ opacity: 0, y: 18 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, delay: 0.26, ease: [0.22, 1, 0.36, 1] }}
          className="mx-auto mt-8 max-w-2xl text-lg leading-relaxed text-musper-cream/70 text-pretty"
        >
          We're building an AI-powered assistant that walks founders through a
          short business diagnostic and points them to the right Musper service
          or program. Until it lands, the fastest way to talk to us is the form
          on our contact page.
        </motion.p>

        <motion.div
          initial={{ opacity: 0, y: 18 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, delay: 0.34, ease: [0.22, 1, 0.36, 1] }}
          className="mt-12 flex flex-wrap justify-center gap-3"
        >
          <Button variant="orange" to="/contact">Talk to us instead</Button>
          <Button variant="outlineLight" to="/" icon={ArrowLeft}>Back to home</Button>
        </motion.div>

        <motion.p
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 1, delay: 0.6 }}
          className="mt-16 text-xs uppercase tracking-eyebrow text-musper-cream/40"
        >
          Phase 4 · in development
        </motion.p>
      </div>
    </section>
  );
}
