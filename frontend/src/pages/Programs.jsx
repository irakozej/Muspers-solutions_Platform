import { ArrowUpRight, Sparkles } from 'lucide-react';
import Button from '../components/Button';
import ChatCTA from '../components/ChatCTA';
import Reveal from '../components/Reveal';
import { programs, images } from '../data/site';

const programImages = {
  siyb: images.workshop,
  'growth-clinics': images.growth,
  'women-digital': images.women,
};

export default function Programs() {
  return (
    <div className="overflow-x-hidden">
      {/* HERO */}
      <section className="pt-24 pb-20 lg:pt-32 lg:pb-24">
        <div className="container">
          <Reveal>
            <p className="eyebrow">Programs</p>
          </Reveal>
          <Reveal delay={0.05}>
            <h1 className="mt-6 max-w-5xl font-display text-[2.5rem] font-medium leading-[1.05] tracking-editorial sm:text-[4rem] lg:text-[5.5rem] text-balance">
              Flagship initiatives that{' '}
              <span className="italic font-light text-musper-green">multiply</span>{' '}
              what works.
            </h1>
          </Reveal>
          <Reveal delay={0.15}>
            <p className="mt-10 max-w-2xl text-lg leading-relaxed text-musper-muted text-pretty">
              Our flagship programs strengthen entrepreneurship, empower
              businesses, and expand economic opportunity across Rwanda. Each one
              is built on proven methodologies, adapted for the realities on the
              ground.
            </p>
          </Reveal>
        </div>
      </section>

      {/* PROGRAMS */}
      <section className="border-t border-musper-line">
        {programs.map((program, i) => {
          const reversed = i % 2 === 1;
          return (
            <article
              key={program.id}
              className={[
                'border-b border-musper-line py-20 lg:py-28',
                reversed ? 'bg-musper-cream-soft/70' : '',
              ].join(' ')}
            >
              <div className="container">
                <div className="grid items-center gap-12 lg:grid-cols-12 lg:gap-16">
                  {/* Image */}
                  <Reveal className={['lg:col-span-5', reversed ? 'lg:order-2' : ''].join(' ')}>
                    <div className="relative">
                      <div className="relative aspect-[4/5] overflow-hidden rounded-[2rem] bg-musper-green">
                        <img
                          src={programImages[program.id]}
                          alt={program.name}
                          className="h-full w-full object-cover"
                        />
                        <div className="pointer-events-none absolute inset-0 bg-gradient-to-t from-musper-green/50 via-transparent to-transparent" />
                      </div>
                      <div className="absolute -bottom-5 -left-4 rounded-2xl border border-musper-line bg-musper-cream-soft px-4 py-3 shadow-soft lg:-bottom-7 lg:-left-7">
                        <p className="font-mono text-[0.7rem] uppercase tracking-eyebrow text-musper-green">
                          0{i + 1} / 0{programs.length}
                        </p>
                      </div>
                    </div>
                  </Reveal>

                  {/* Content */}
                  <div className={['lg:col-span-7', reversed ? 'lg:order-1' : ''].join(' ')}>
                    <Reveal delay={0.05}>
                      <p className="text-eyebrow uppercase tracking-eyebrow text-musper-orange">
                        {program.eyebrow}
                      </p>
                      <h2 className="mt-6 font-display text-4xl leading-[1.05] tracking-editorial sm:text-[3rem] text-balance">
                        {program.name}
                      </h2>
                      <p className="mt-6 text-lg leading-relaxed text-musper-muted text-pretty">
                        {program.summary}
                      </p>
                    </Reveal>

                    <Reveal delay={0.12}>
                      <div className="mt-8 grid gap-6 sm:grid-cols-2">
                        <div className="rounded-2xl border border-musper-line bg-musper-cream-soft/80 p-5">
                          <p className="text-xs uppercase tracking-eyebrow text-musper-green">Who it's for</p>
                          <p className="mt-3 text-sm leading-relaxed text-musper-ink/85">{program.audience}</p>
                        </div>
                        <div className="rounded-2xl border border-musper-line bg-musper-cream-soft/80 p-5">
                          <p className="text-xs uppercase tracking-eyebrow text-musper-green">By the end</p>
                          <ul className="mt-3 space-y-2 text-sm text-musper-ink/85">
                            {program.outcomes.map((o) => (
                              <li key={o} className="flex items-start gap-2">
                                <Sparkles size={13} className="mt-1 shrink-0 text-musper-orange" />
                                <span>{o}</span>
                              </li>
                            ))}
                          </ul>
                        </div>
                      </div>
                    </Reveal>

                    <Reveal delay={0.18}>
                      <div className="mt-8 flex flex-wrap gap-3">
                        <Button to="/contact" icon={ArrowUpRight}>Apply or enquire</Button>
                        <ChatCTA />
                      </div>
                    </Reveal>
                  </div>
                </div>
              </div>
            </article>
          );
        })}
      </section>

      {/* OUTRO */}
      <section className="py-28 lg:py-36">
        <div className="container text-center">
          <Reveal>
            <p className="eyebrow justify-center">Designing the next program</p>
            <h2 className="mx-auto mt-6 max-w-3xl font-display text-3xl leading-[1.1] tracking-editorial sm:text-[2.5rem] text-balance">
              We co-design programs with banks, MFIs, and development partners. Let's build the next one together.
            </h2>
            <div className="mt-10 flex justify-center gap-3">
              <Button to="/contact">Start a conversation</Button>
              <Button variant="outline" to="/services">See our services</Button>
            </div>
          </Reveal>
        </div>
      </section>
    </div>
  );
}
