import { Link } from 'react-router-dom';
import { motion } from 'framer-motion';
import { ArrowUpRight, Building2, Landmark, Users, Sparkles } from 'lucide-react';
import Button from '../components/Button';
import ChatCTA from '../components/ChatCTA';
import Reveal from '../components/Reveal';
import {
  brand,
  contactInfo,
  services,
  programs,
  testimonials,
  stats,
  audiences,
  images,
} from '../data/site';

export default function Home() {
  return (
    <div className="overflow-x-hidden">
      {/* ───────────────────── HERO ───────────────────── */}
      <section className="relative pt-24 pb-24 lg:pt-32 lg:pb-32">
        <div className="container relative grid items-end gap-12 lg:grid-cols-12 lg:gap-10">
          <div className="lg:col-span-7">
            <Reveal>
              <p className="eyebrow">
                <span>Kigali · Rwanda · est. {brand.founded}</span>
              </p>
            </Reveal>
            <Reveal delay={0.05}>
              <h1 className="mt-6 font-display text-[2.75rem] font-medium leading-[1.02] tracking-editorial sm:text-[4rem] lg:text-[5.5rem] text-balance">
                Equipping African businesses to{' '}
                <span className="italic font-light text-musper-green">
                  scale
                </span>{' '}
                through{' '}
                <span className="ink-underline">strategy</span>
                <br className="hidden sm:block" /> and{' '}
                <span className="ink-underline">systems</span>.
              </h1>
            </Reveal>
            <Reveal delay={0.15}>
              <p className="mt-8 max-w-xl text-lg leading-relaxed text-musper-muted text-pretty">
                Musper Solutions is a Rwandan business development consultancy.
                We partner with entrepreneurs, financial institutions, and
                development partners to build the strategies, systems, and skills
                that move businesses from idea to investment-ready — and beyond.
              </p>
            </Reveal>
            <Reveal delay={0.25}>
              <div className="mt-10 flex flex-wrap items-center gap-3">
                <ChatCTA />
                <Button variant="outline" to="/services">
                  Explore our services
                </Button>
              </div>
            </Reveal>
          </div>

          {/* Hero image card with floating stat badge */}
          <Reveal delay={0.15} className="lg:col-span-5">
            <div className="relative">
              <motion.div
                initial={{ scale: 1.06 }}
                animate={{ scale: 1 }}
                transition={{ duration: 1.4, ease: [0.22, 1, 0.36, 1] }}
                className="relative aspect-[4/5] overflow-hidden rounded-[2rem] bg-musper-green"
              >
                <img
                  src={images.workshop}
                  alt="A working session — practical advisory in action"
                  className="h-full w-full object-cover opacity-95"
                  loading="eager"
                />
                <div className="pointer-events-none absolute inset-0 bg-gradient-to-t from-musper-green/55 via-transparent to-transparent" />
                <div className="absolute bottom-5 left-5 right-5 flex items-end justify-between text-musper-cream">
                  <div>
                    <p className="text-eyebrow uppercase tracking-eyebrow text-musper-cream/70">
                      In the room
                    </p>
                    <p className="mt-1 font-display text-xl leading-tight tracking-editorial">
                      Practical advisory, not theatre.
                    </p>
                  </div>
                </div>
              </motion.div>

              {/* Floating stat badge */}
              <motion.div
                initial={{ opacity: 0, y: 24 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.8, ease: [0.22, 1, 0.36, 1], delay: 0.5 }}
                className="absolute -left-4 -bottom-6 max-w-[12rem] rounded-2xl border border-musper-line bg-musper-cream-soft px-5 py-4 shadow-soft lg:-left-12 lg:-bottom-8"
              >
                <p className="font-display text-4xl font-medium leading-none tracking-editorial text-musper-green">
                  300+
                </p>
                <p className="mt-2 text-xs leading-snug text-musper-muted">
                  entrepreneurs trained across Rwanda and the region.
                </p>
              </motion.div>

              {/* Decorative outline ring */}
              <div className="pointer-events-none absolute -right-6 -top-6 hidden h-28 w-28 rounded-full border border-musper-orange/40 lg:block" />
            </div>
          </Reveal>
        </div>
      </section>

      {/* ───────────────────── TRUSTED-BY / AUDIENCES STRIP ───────────────────── */}
      <section className="border-y border-musper-line bg-musper-cream-soft/60 py-8">
        <div className="container flex flex-col items-start gap-4 sm:flex-row sm:items-center sm:justify-between">
          <p className="eyebrow">Who we work with</p>
          <ul className="flex flex-wrap items-center gap-x-8 gap-y-3 text-sm font-medium text-musper-ink/70">
            <li>Commercial banks</li>
            <li className="text-musper-muted-soft">·</li>
            <li>Microfinance &amp; SACCOs</li>
            <li className="text-musper-muted-soft">·</li>
            <li>Development partners</li>
            <li className="text-musper-muted-soft">·</li>
            <li>Government institutions</li>
            <li className="text-musper-muted-soft">·</li>
            <li>Growth-stage SMEs</li>
          </ul>
        </div>
      </section>

      {/* ───────────────────── INTRO ───────────────────── */}
      <section className="py-28 lg:py-36">
        <div className="container grid gap-12 lg:grid-cols-12">
          <div className="lg:col-span-4">
            <Reveal>
              <p className="eyebrow">Who we are</p>
              <h2 className="mt-6 font-display text-4xl leading-[1.05] tracking-editorial sm:text-5xl text-balance">
                A consultancy built for the realities of{' '}
                <span className="italic font-light text-musper-green">
                  African business
                </span>.
              </h2>
            </Reveal>
          </div>
          <div className="lg:col-span-7 lg:col-start-6">
            <Reveal delay={0.1}>
              <p className="text-lg leading-relaxed text-musper-ink/85 text-pretty">
                We combine practical business advisory, structured training
                methodologies — including ILO's globally-recognised SIYB curriculum —
                and ecosystem partnerships to deliver solutions that meet
                entrepreneurs and institutions exactly where they are.
              </p>
              <p className="mt-6 text-lg leading-relaxed text-musper-muted text-pretty">
                Founded by Penny Burabyo Musoni in {brand.founded}, Musper has grown into
                a trusted partner for the institutions shaping Rwanda's
                entrepreneurship ecosystem — and a steady hand for the founders
                building inside it.
              </p>
              <div className="mt-8 flex flex-wrap gap-3">
                <Button variant="outline" to="/about">About Musper</Button>
                <Button variant="ghost" to="/about" icon={ArrowUpRight}>Meet the founder</Button>
              </div>
            </Reveal>
          </div>
        </div>
      </section>

      {/* ───────────────────── STATS ───────────────────── */}
      <section className="border-y border-musper-line bg-musper-cream-soft/70 py-16">
        <div className="container grid grid-cols-2 gap-x-8 gap-y-10 sm:grid-cols-4">
          {stats.map((s, i) => (
            <Reveal key={s.label} delay={i * 0.06}>
              <div>
                <p className="font-display text-[3.25rem] font-medium leading-none tracking-editorial text-musper-green">
                  <span className="italic font-light">{s.value}</span>
                </p>
                <p className="mt-3 text-sm font-medium uppercase tracking-eyebrow text-musper-ink">
                  {s.label}
                </p>
                <p className="mt-1 text-sm text-musper-muted">{s.detail}</p>
              </div>
            </Reveal>
          ))}
        </div>
      </section>

      {/* ───────────────────── SERVICES PREVIEW ───────────────────── */}
      <section className="py-28 lg:py-36">
        <div className="container">
          <div className="flex flex-col items-start justify-between gap-8 sm:flex-row sm:items-end">
            <Reveal>
              <p className="eyebrow">What we do</p>
              <h2 className="mt-6 max-w-2xl font-display text-4xl leading-[1.05] tracking-editorial sm:text-5xl text-balance">
                Five practices.{' '}
                <span className="italic font-light text-musper-green">One playbook.</span>
              </h2>
            </Reveal>
            <Reveal delay={0.1}>
              <Button variant="outline" to="/services">All services</Button>
            </Reveal>
          </div>

          <div className="mt-14 grid gap-6 md:grid-cols-2 lg:grid-cols-3">
            {services.slice(0, 3).map((service, i) => (
              <Reveal key={service.id} delay={i * 0.08}>
                <Link
                  to="/services"
                  className="group relative flex h-full flex-col rounded-3xl border border-musper-line bg-musper-cream-soft/70 p-7 transition-all duration-500 ease-editorial hover:-translate-y-1 hover:border-musper-green/30 hover:bg-musper-cream-soft hover:shadow-soft"
                >
                  <div className="flex items-start justify-between">
                    <span className="font-mono text-xs tracking-tight text-musper-muted">
                      {service.number}
                    </span>
                    <ArrowUpRight
                      size={18}
                      className="text-musper-muted-soft transition-all duration-500 ease-editorial group-hover:-translate-y-0.5 group-hover:translate-x-0.5 group-hover:text-musper-orange"
                    />
                  </div>
                  <h3 className="mt-10 font-display text-2xl leading-tight tracking-editorial">
                    {service.title}
                  </h3>
                  <p className="mt-4 text-sm leading-relaxed text-musper-muted">
                    {service.summary}
                  </p>
                  <p className="mt-8 text-xs uppercase tracking-eyebrow text-musper-green/80">
                    Outcome → <span className="text-musper-ink/80 normal-case tracking-tight font-normal">{service.outcome}</span>
                  </p>
                </Link>
              </Reveal>
            ))}
          </div>
        </div>
      </section>

      {/* ───────────────────── PROGRAMS PREVIEW (dark) ───────────────────── */}
      <section className="relative overflow-hidden surface-dark py-28 lg:py-36">
        <div className="pointer-events-none absolute inset-0 bg-grain opacity-30 mix-blend-overlay" />
        <div className="pointer-events-none absolute -top-32 -right-32 h-96 w-96 rounded-full bg-musper-orange/15 blur-3xl" />

        <div className="container relative">
          <div className="grid items-end gap-8 lg:grid-cols-2">
            <Reveal>
              <p className="eyebrow !text-musper-orange">Flagship programs</p>
              <h2 className="mt-6 max-w-xl font-display text-4xl leading-[1.05] tracking-editorial sm:text-5xl text-balance">
                Programs designed for{' '}
                <span className="italic font-light text-musper-cream/85">impact at scale.</span>
              </h2>
            </Reveal>
            <Reveal delay={0.1}>
              <p className="text-base leading-relaxed text-musper-cream/70 lg:max-w-md lg:justify-self-end">
                At Musper, we design and implement initiatives that strengthen
                entrepreneurship, empower businesses, and promote inclusive
                economic growth — across Rwanda and the region.
              </p>
            </Reveal>
          </div>

          <div className="mt-16 grid gap-px overflow-hidden rounded-3xl bg-musper-cream/10 lg:grid-cols-3">
            {programs.map((program, i) => (
              <Reveal key={program.id} delay={i * 0.08}>
                <Link
                  to="/programs"
                  className="group flex h-full flex-col bg-musper-green p-8 transition-colors duration-500 ease-editorial hover:bg-musper-green-deep"
                >
                  <p className="text-eyebrow uppercase tracking-eyebrow text-musper-orange">
                    {program.eyebrow}
                  </p>
                  <h3 className="mt-6 font-display text-2xl leading-tight tracking-editorial text-musper-cream">
                    {program.name}
                  </h3>
                  <p className="mt-4 text-sm leading-relaxed text-musper-cream/65">
                    {program.summary}
                  </p>
                  <span className="mt-8 inline-flex items-center gap-2 text-sm text-musper-orange transition-transform duration-500 ease-editorial group-hover:translate-x-1">
                    Explore program <ArrowUpRight size={14} />
                  </span>
                </Link>
              </Reveal>
            ))}
          </div>

          <div className="mt-12 flex justify-center">
            <Button variant="outlineLight" to="/programs">View all programs</Button>
          </div>
        </div>
      </section>

      {/* ───────────────────── AUDIENCES STRIP ───────────────────── */}
      <section className="py-28 lg:py-36">
        <div className="container">
          <Reveal>
            <p className="eyebrow">Who we serve</p>
            <h2 className="mt-6 max-w-3xl font-display text-4xl leading-[1.05] tracking-editorial sm:text-5xl text-balance">
              Three audiences.{' '}
              <span className="italic font-light text-musper-green">One commitment.</span>
            </h2>
          </Reveal>
          <div className="mt-14 grid gap-10 md:grid-cols-3">
            {audiences.map((a, i) => {
              const Icon = [Users, Landmark, Building2][i] || Sparkles;
              return (
                <Reveal key={a.title} delay={i * 0.08}>
                  <div className="flex h-full flex-col border-t border-musper-line pt-8">
                    <Icon size={26} className="text-musper-orange" strokeWidth={1.5} />
                    <h3 className="mt-6 font-display text-2xl leading-tight tracking-editorial">
                      {a.title}
                    </h3>
                    <p className="mt-4 text-base leading-relaxed text-musper-muted">{a.body}</p>
                  </div>
                </Reveal>
              );
            })}
          </div>
        </div>
      </section>

      {/* ───────────────────── TESTIMONIAL PULL-QUOTE ───────────────────── */}
      <section className="border-t border-musper-line bg-musper-cream-soft py-28 lg:py-36">
        <div className="container grid gap-16 lg:grid-cols-12">
          <div className="lg:col-span-3">
            <Reveal>
              <p className="eyebrow">In their words</p>
              <p className="mt-6 text-sm leading-relaxed text-musper-muted">
                A selection of feedback from entrepreneurs and organizations we
                have worked with.
              </p>
              <div className="mt-8">
                <Button variant="ghost" to="/testimonials" icon={ArrowUpRight}>
                  Read all voices
                </Button>
              </div>
            </Reveal>
          </div>
          <div className="lg:col-span-9">
            <Reveal delay={0.1}>
              <figure>
                <p className="font-display text-3xl leading-[1.18] tracking-editorial text-musper-ink/90 sm:text-[2.5rem] sm:leading-[1.15] text-balance">
                  <span className="text-musper-orange">“</span>
                  {testimonials[1].quote}
                  <span className="text-musper-orange">”</span>
                </p>
                <figcaption className="mt-8 flex items-center gap-3 text-sm text-musper-muted">
                  <span className="h-px w-10 bg-musper-orange" />
                  <span className="uppercase tracking-eyebrow">{testimonials[1].name}</span>
                  <span className="text-musper-muted-soft">·</span>
                  <span>{testimonials[1].role}</span>
                </figcaption>
              </figure>
            </Reveal>
          </div>
        </div>
      </section>

      {/* ───────────────────── FINAL CTA ───────────────────── */}
      <section className="relative overflow-hidden py-28 lg:py-36">
        <div className="container">
          <div className="relative overflow-hidden rounded-[2.5rem] bg-musper-green px-8 py-16 sm:px-14 sm:py-20 lg:px-20 lg:py-24">
            <div className="pointer-events-none absolute inset-0 bg-grain opacity-30 mix-blend-overlay" />
            <div className="pointer-events-none absolute -right-24 -top-24 h-72 w-72 rounded-full border border-musper-cream/15" />
            <div className="pointer-events-none absolute -right-12 -top-12 h-48 w-48 rounded-full border border-musper-orange/40" />

            <div className="relative grid gap-10 lg:grid-cols-12 lg:items-end">
              <div className="lg:col-span-8">
                <Reveal>
                  <p className="eyebrow !text-musper-orange">Let's begin</p>
                  <h2 className="mt-6 font-display text-4xl leading-[1.05] tracking-editorial text-musper-cream sm:text-[3.5rem] text-balance">
                    Have a business challenge worth solving?{' '}
                    <span className="italic font-light text-musper-cream/85">Let's talk.</span>
                  </h2>
                </Reveal>
              </div>
              <div className="lg:col-span-4 lg:justify-self-end">
                <Reveal delay={0.1}>
                  <div className="flex flex-col gap-3 sm:flex-row sm:flex-wrap lg:flex-col">
                    <ChatCTA tone="dark" />
                    <Button variant="outlineLight" to="/contact">
                      Book a consultation
                    </Button>
                  </div>
                  <p className="mt-6 text-sm text-musper-cream/55">
                    Or reach Penny directly on{' '}
                    <a className="underline decoration-musper-orange/60 underline-offset-4 hover:text-musper-cream" href={`tel:${contactInfo.phone.replace(/\s/g, '')}`}>{contactInfo.phone}</a>.
                  </p>
                </Reveal>
              </div>
            </div>
          </div>
        </div>
      </section>
    </div>
  );
}
