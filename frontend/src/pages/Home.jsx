export default function Home() {
  return (
    <section className="mx-auto max-w-6xl px-6 py-24">
      <p className="mb-4 inline-flex items-center gap-2 rounded-full bg-musper-green/10 px-3 py-1 text-xs font-medium uppercase tracking-wider text-musper-green">
        <span className="h-1.5 w-1.5 rounded-full bg-musper-orange" />
        Kigali · Rwanda
      </p>
      <h1 className="font-display text-5xl font-bold leading-tight tracking-tightish text-musper-green md:text-7xl">
        Musper Solutions
      </h1>
      <p className="mt-6 max-w-2xl text-lg text-musper-muted">
        Strategic, financial, and operational consulting for African SMEs.
        The platform is being rebuilt — a new experience is on the way.
      </p>
      <div className="mt-10 flex flex-wrap gap-3">
        <button
          type="button"
          className="rounded-md bg-musper-orange px-5 py-3 text-sm font-semibold text-white shadow-sm transition hover:bg-musper-orange-dark"
        >
          Get in touch
        </button>
        <button
          type="button"
          className="rounded-md border border-musper-green/20 bg-white px-5 py-3 text-sm font-semibold text-musper-green transition hover:bg-musper-green/5"
        >
          Learn more
        </button>
      </div>
    </section>
  );
}
