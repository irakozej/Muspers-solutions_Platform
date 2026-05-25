export default function Footer() {
  return (
    <footer className="border-t border-black/5 bg-white/60">
      <div className="mx-auto flex max-w-6xl flex-col items-start justify-between gap-2 px-6 py-6 text-sm text-musper-muted md:flex-row md:items-center">
        <p>&copy; {new Date().getFullYear()} Musper Solutions Ltd. — Kigali, Rwanda.</p>
        <p className="text-xs">Phase 1 placeholder — platform under construction.</p>
      </div>
    </footer>
  );
}
