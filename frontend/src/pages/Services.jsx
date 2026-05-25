import { Check, ArrowDown } from 'lucide-react';
import Button from '../components/Button';
import ChatCTA from '../components/ChatCTA';
import Reveal from '../components/Reveal';
import { services } from '../data/site';

export default function Services() {
  return (
    <div className="overflow-x-hidden">
      {/* HERO */}
      <section className="pt-24 pb-16 lg:pt-32 lg:pb-20">
        <div className="container">
          <Reveal>
            <p className="eyebrow">Services</p>
          </Reveal>
          <Reveal delay={0.05}>
            <h1 className="mt-6 max-w-5xl font-display text-[2.5rem] font-medium leading-[1.05] tracking-editorial sm:text-[4rem] lg:text-[5rem] text-balance">
              Tailored business solutions for{' '}
              <span className="italic font-light text-musper-green">sustainable</span>{' '}
              growth.
            </h1>
          </Reveal>
          <Reveal delay={0.15}>
            <div className="mt-10 grid gap-8 lg:grid-cols-12 lg:items-end">
              <p className="lg:col-span-7 text-lg leading-relaxed text-musper-muted text-pretty">
                We support businesses, banks, and institutional partners with
                professional expertise, strategic insights, and tailored
                solutions designed to drive sustainable growth and measurable
                financial outcomes.
              </p>
              <div className="lg:col-span-5 lg:justify-self-end flex flex-wrap gap-3">
                <ChatCTA />
                <Button variant="outline" href="#services-list" icon={ArrowDown}>
                  Browse services
                </Button>
              </div>
            </div>
          </Reveal>
        </div>
      </section>

      {/* SERVICES LIST */}
      <section id="services-list" className="border-t border-musper-line py-12 lg:py-20">
        <div className="container">
          <div className="divide-y divide-musper-line">
            {services.map((service, i) => {
              const reversed = i % 2 === 1;
              return (
                <article key={service.id} className="py-14 lg:py-20">
                  <div className={[
                    'grid items-start gap-10 lg:grid-cols-12 lg:gap-12',
                  ].join(' ')}>
                    {/* Number + meta */}
                    <Reveal className={['lg:col-span-3', reversed ? 'lg:order-3' : ''].join(' ')}>
                      <p className="font-mono text-xs tracking-tight text-musper-muted">
                        Service {service.number}
                      </p>
                      <p className="mt-3 font-display text-7xl leading-none font-light italic text-musper-green/80">
                        {service.number}
                      </p>
                    </Reveal>

                    {/* Body */}
                    <div className="lg:col-span-6">
                      <Reveal delay={0.05}>
                        <h2 className="font-display text-3xl leading-[1.1] tracking-editorial sm:text-[2.5rem] text-balance">
                          {service.title}
                        </h2>
                        <p className="mt-6 text-lg leading-relaxed text-musper-muted text-pretty">
                          {service.summary}
                        </p>
                        <div className="mt-8 inline-flex items-start gap-3 rounded-2xl border border-musper-green/15 bg-musper-green-soft px-5 py-4">
                          <span className="mt-1 h-2 w-2 shrink-0 rounded-full bg-musper-orange" />
                          <div>
                            <p className="text-xs uppercase tracking-eyebrow text-musper-green">Outcome</p>
                            <p className="mt-1 text-sm text-musper-ink/85">{service.outcome}</p>
                          </div>
                        </div>
                      </Reveal>
                    </div>

                    {/* Points */}
                    <Reveal delay={0.1} className="lg:col-span-3">
                      <p className="text-xs uppercase tracking-eyebrow text-musper-muted">Includes</p>
                      <ul className="mt-4 space-y-3">
                        {service.points.map((p) => (
                          <li key={p} className="flex items-start gap-2.5 text-sm text-musper-ink/85">
                            <Check size={15} strokeWidth={2} className="mt-0.5 shrink-0 text-musper-orange" />
                            <span>{p}</span>
                          </li>
                        ))}
                      </ul>
                    </Reveal>
                  </div>
                </article>
              );
            })}
          </div>
        </div>
      </section>

      {/* MID-PAGE CTA */}
      <section className="relative overflow-hidden border-t border-musper-line surface-dark py-24 lg:py-28">
        <div className="pointer-events-none absolute inset-0 bg-grain opacity-30 mix-blend-overlay" />
        <div className="container relative grid gap-10 lg:grid-cols-12 lg:items-center">
          <div className="lg:col-span-7">
            <Reveal>
              <p className="eyebrow !text-musper-orange">Not sure where to start?</p>
              <h2 className="mt-6 font-display text-4xl leading-[1.05] tracking-editorial text-musper-cream sm:text-5xl text-balance">
                Chat with our assistant — it'll point you to the right service in under three minutes.
              </h2>
            </Reveal>
          </div>
          <div className="lg:col-span-5 lg:justify-self-end">
            <Reveal delay={0.1}>
              <div className="flex flex-col gap-3 sm:flex-row sm:flex-wrap lg:flex-col">
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
