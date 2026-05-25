import { motion } from 'framer-motion';
import { Quote } from 'lucide-react';
import Button from '../components/Button';
import ChatCTA from '../components/ChatCTA';
import Reveal from '../components/Reveal';
import { brand, founder, stats, values, images } from '../data/site';

export default function About() {
  return (
    <div className="overflow-x-hidden">
      {/* HERO */}
      <section className="pt-24 pb-20 lg:pt-32 lg:pb-24">
        <div className="container">
          <Reveal>
            <p className="eyebrow">About Musper</p>
          </Reveal>
          <Reveal delay={0.05}>
            <h1 className="mt-6 max-w-4xl font-display text-[2.5rem] font-medium leading-[1.05] tracking-editorial sm:text-[4rem] lg:text-[5rem] text-balance">
              We exist to close the distance between{' '}
              <span className="italic font-light text-musper-green">African potential</span>{' '}
              and the systems it takes to{' '}
              <span className="ink-underline">scale</span>.
            </h1>
          </Reveal>
          <Reveal delay={0.15}>
            <p className="mt-10 max-w-2xl text-lg leading-relaxed text-musper-muted text-pretty">
              Since {brand.founded}, Musper Solutions has worked alongside
              founders, financial institutions, and development partners — building
              the strategies, training, and systems that turn ambition into
              durable, profitable, locally-owned businesses.
            </p>
          </Reveal>
        </div>
      </section>

      {/* STATS BAND */}
      <section className="border-y border-musper-line bg-musper-cream-soft/70 py-14">
        <div className="container grid grid-cols-2 gap-x-8 gap-y-10 sm:grid-cols-4">
          {stats.map((s, i) => (
            <Reveal key={s.label} delay={i * 0.06}>
              <div>
                <p className="font-display text-[3rem] font-medium leading-none tracking-editorial text-musper-green">
                  <span className="italic font-light">{s.value}</span>
                </p>
                <p className="mt-3 text-xs font-medium uppercase tracking-eyebrow text-musper-ink">
                  {s.label}
                </p>
                <p className="mt-1 text-sm text-musper-muted">{s.detail}</p>
              </div>
            </Reveal>
          ))}
        </div>
      </section>

      {/* FOUNDER */}
      <section className="py-28 lg:py-36">
        <div className="container grid gap-12 lg:grid-cols-12">
          <Reveal className="lg:col-span-5">
            <div className="relative">
              <motion.div
                initial={{ scale: 1.06 }}
                whileInView={{ scale: 1 }}
                viewport={{ once: true, amount: 0.3 }}
                transition={{ duration: 1.4, ease: [0.22, 1, 0.36, 1] }}
                className="relative aspect-[4/5] overflow-hidden rounded-[2rem] bg-musper-green"
              >
                <img
                  src={images.founderPortrait}
                  alt={founder.name}
                  className="h-full w-full object-cover"
                />
                <div className="pointer-events-none absolute inset-0 bg-gradient-to-t from-musper-green/45 via-transparent to-transparent" />
              </motion.div>
              <div className="absolute -bottom-6 -right-4 max-w-[15rem] rounded-2xl border border-musper-line bg-musper-cream-soft px-5 py-4 shadow-soft lg:-bottom-8 lg:-right-8">
                <p className="font-display text-lg leading-tight tracking-editorial">
                  {founder.name}
                </p>
                <p className="mt-1 text-xs uppercase tracking-eyebrow text-musper-green">
                  {founder.role}
                </p>
              </div>
            </div>
          </Reveal>

          <div className="lg:col-span-7 lg:pl-8">
            <Reveal>
              <p className="eyebrow">Founder</p>
              <h2 className="mt-6 font-display text-4xl leading-[1.05] tracking-editorial sm:text-5xl text-balance">
                {founder.blurb}
              </h2>
            </Reveal>
            <Reveal delay={0.1}>
              <div className="mt-8 space-y-6 text-lg leading-relaxed text-musper-ink/85 text-pretty">
                {founder.bio.map((p, i) => (
                  <p key={i} className={i > 0 ? 'text-musper-muted' : ''}>{p}</p>
                ))}
              </div>
              <div className="mt-10 flex flex-wrap gap-3">
                <Button to="/contact">Get in touch with Penny</Button>
                <ChatCTA />
              </div>
            </Reveal>
          </div>
        </div>
      </section>

      {/* MISSION / VISION (dark) */}
      <section className="relative overflow-hidden surface-dark py-28 lg:py-36">
        <div className="pointer-events-none absolute inset-0 bg-grain opacity-30 mix-blend-overlay" />
        <div className="pointer-events-none absolute -bottom-32 -left-32 h-96 w-96 rounded-full bg-musper-orange/15 blur-3xl" />
        <div className="container relative grid gap-16 lg:grid-cols-2">
          <Reveal>
            <p className="eyebrow !text-musper-orange">Mission</p>
            <p className="mt-6 font-display text-3xl leading-[1.15] tracking-editorial text-musper-cream sm:text-4xl text-balance">
              To strengthen African entrepreneurship by delivering practical
              advisory, structured training, and ecosystem partnerships that
              produce measurable business outcomes.
            </p>
          </Reveal>
          <Reveal delay={0.1}>
            <p className="eyebrow !text-musper-orange">Vision</p>
            <p className="mt-6 font-display text-3xl leading-[1.15] tracking-editorial text-musper-cream sm:text-4xl text-balance">
              A continent where every growth-minded entrepreneur has access to
              the systems, capital, and counsel they need to build a business
              that lasts.
            </p>
          </Reveal>
        </div>
      </section>

      {/* VALUES */}
      <section className="py-28 lg:py-36">
        <div className="container">
          <Reveal>
            <p className="eyebrow">Our values</p>
            <h2 className="mt-6 max-w-2xl font-display text-4xl leading-[1.05] tracking-editorial sm:text-5xl text-balance">
              Four words we measure ourselves against — every project, every season.
            </h2>
          </Reveal>
          <div className="mt-16 grid gap-12 sm:grid-cols-2 lg:grid-cols-4">
            {values.map((v, i) => (
              <Reveal key={v.title} delay={i * 0.08}>
                <div className="border-t border-musper-line pt-8">
                  <p className="font-mono text-xs tracking-tight text-musper-muted">
                    0{i + 1}
                  </p>
                  <h3 className="mt-4 font-display text-2xl leading-tight tracking-editorial">
                    {v.title}
                  </h3>
                  <p className="mt-4 text-base leading-relaxed text-musper-muted">{v.body}</p>
                </div>
              </Reveal>
            ))}
          </div>
        </div>
      </section>

      {/* TEAM PLACEHOLDER */}
      <section className="border-t border-musper-line bg-musper-cream-soft py-28 lg:py-36">
        <div className="container">
          <div className="grid gap-12 lg:grid-cols-12">
            <div className="lg:col-span-4">
              <Reveal>
                <p className="eyebrow">The team</p>
                <h2 className="mt-6 font-display text-4xl leading-[1.05] tracking-editorial sm:text-5xl text-balance">
                  Small team. Deep bench.
                </h2>
              </Reveal>
            </div>
            <div className="lg:col-span-7 lg:col-start-6">
              <Reveal delay={0.1}>
                <p className="text-lg leading-relaxed text-musper-muted text-pretty">
                  Musper draws on a network of senior advisors, certified
                  trainers, and sector specialists — assembled per engagement
                  to match the brief. We're building out the public team page;
                  in the meantime, the easiest way to meet us is to start a
                  conversation.
                </p>
                <div className="mt-8 flex flex-wrap gap-3">
                  <Button to="/contact">Start a conversation</Button>
                  <Button variant="outline" to="/services">See our services</Button>
                </div>
              </Reveal>
            </div>
          </div>
        </div>
      </section>

      {/* CLOSING PULL-QUOTE */}
      <section className="py-28 lg:py-36">
        <div className="container">
          <Reveal>
            <div className="mx-auto max-w-4xl text-center">
              <Quote size={28} className="mx-auto text-musper-orange" />
              <p className="mt-8 font-display text-3xl leading-[1.2] tracking-editorial sm:text-[2.5rem] text-balance">
                The work is the proof. The numbers come after.
              </p>
              <p className="mt-6 text-sm uppercase tracking-eyebrow text-musper-muted">
                — A line we keep coming back to.
              </p>
            </div>
          </Reveal>
        </div>
      </section>
    </div>
  );
}
