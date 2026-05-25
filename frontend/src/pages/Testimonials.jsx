import { Quote } from 'lucide-react';
import Button from '../components/Button';
import ChatCTA from '../components/ChatCTA';
import Reveal from '../components/Reveal';
import { testimonials } from '../data/site';

export default function Testimonials() {
  const [feature, ...rest] = testimonials;

  return (
    <div className="overflow-x-hidden">
      {/* HERO */}
      <section className="pt-24 pb-12 lg:pt-32 lg:pb-16">
        <div className="container">
          <Reveal>
            <p className="eyebrow">Voices</p>
          </Reveal>
          <Reveal delay={0.05}>
            <h1 className="mt-6 max-w-5xl font-display text-[2.5rem] font-medium leading-[1.05] tracking-editorial sm:text-[4rem] lg:text-[5.5rem] text-balance">
              The receipts.{' '}
              <span className="italic font-light text-musper-green">In their words.</span>
            </h1>
          </Reveal>
          <Reveal delay={0.15}>
            <p className="mt-10 max-w-2xl text-lg leading-relaxed text-musper-muted text-pretty">
              We measure success in what our clients say about the work — once
              it's over, once it's tested, once the impact has had time to land.
            </p>
          </Reveal>
        </div>
      </section>

      {/* FEATURED PULL-QUOTE */}
      <section className="py-20 lg:py-24">
        <div className="container">
          <Reveal>
            <figure className="relative mx-auto max-w-5xl rounded-[2.5rem] border border-musper-line bg-musper-cream-soft px-8 py-16 sm:px-16 sm:py-20">
              <Quote size={36} className="text-musper-orange" />
              <p className="mt-8 font-display text-3xl leading-[1.18] tracking-editorial text-musper-ink sm:text-[2.5rem] sm:leading-[1.18] text-balance">
                {feature.quote}
              </p>
              <figcaption className="mt-10 flex items-center gap-3 text-sm text-musper-muted">
                <span className="h-px w-10 bg-musper-orange" />
                <span className="uppercase tracking-eyebrow text-musper-ink/80">{feature.name}</span>
                <span className="text-musper-muted-soft">·</span>
                <span>{feature.role}</span>
              </figcaption>
            </figure>
          </Reveal>
        </div>
      </section>

      {/* GRID OF QUOTES — editorial, magazine columns */}
      <section className="py-12 lg:py-20">
        <div className="container">
          <div className="grid gap-8 lg:grid-cols-12">
            {rest.map((t, i) => (
              <Reveal
                key={t.name + i}
                delay={i * 0.08}
                className={[
                  'lg:col-span-6',
                  i === 1 ? 'lg:col-span-5 lg:col-start-7' : '',
                  i === 2 ? 'lg:col-span-7' : '',
                ].join(' ')}
              >
                <article className="flex h-full flex-col border-t border-musper-line pt-8">
                  <Quote size={22} className="text-musper-orange/70" />
                  <p className="mt-6 font-display text-2xl leading-[1.25] tracking-editorial text-musper-ink/90 sm:text-[1.75rem] sm:leading-[1.22] text-pretty">
                    {t.quote}
                  </p>
                  <div className="mt-8 flex items-center gap-3 text-sm text-musper-muted">
                    <span className="h-px w-8 bg-musper-orange" />
                    <span className="uppercase tracking-eyebrow text-musper-ink/80">{t.name}</span>
                  </div>
                  <p className="mt-2 pl-11 text-xs uppercase tracking-eyebrow text-musper-muted">{t.role}</p>
                </article>
              </Reveal>
            ))}
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="relative overflow-hidden border-t border-musper-line surface-dark py-28 lg:py-32">
        <div className="pointer-events-none absolute inset-0 bg-grain opacity-30 mix-blend-overlay" />
        <div className="container relative">
          <div className="mx-auto max-w-3xl text-center">
            <Reveal>
              <p className="eyebrow !text-musper-orange justify-center">Your story, next</p>
              <h2 className="mt-6 font-display text-4xl leading-[1.05] tracking-editorial text-musper-cream sm:text-[3rem] text-balance">
                We'd be glad to add yours to this page in a year.
              </h2>
              <div className="mt-10 flex flex-wrap justify-center gap-3">
                <ChatCTA tone="dark" />
                <Button variant="outlineLight" to="/contact">Book a consultation</Button>
              </div>
            </Reveal>
          </div>
        </div>
      </section>
    </div>
  );
}
