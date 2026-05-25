import Button from '../components/Button';

export default function NotFound() {
  return (
    <section className="flex min-h-[60vh] items-center py-32">
      <div className="container text-center">
        <p className="font-mono text-xs uppercase tracking-eyebrow text-musper-muted">Error 404</p>
        <h1 className="mt-6 font-display text-[3rem] leading-[1.05] tracking-editorial sm:text-[5rem]">
          The page you're looking for isn't here.
        </h1>
        <p className="mx-auto mt-8 max-w-xl text-lg text-musper-muted">
          It may have moved, or it may have never existed. Either way — here are some better places to land.
        </p>
        <div className="mt-10 flex flex-wrap justify-center gap-3">
          <Button to="/">Back to home</Button>
          <Button variant="outline" to="/services">Browse services</Button>
        </div>
      </div>
    </section>
  );
}
