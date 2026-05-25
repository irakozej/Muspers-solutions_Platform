import { Link } from 'react-router-dom';

export default function Navbar() {
  return (
    <header className="border-b border-black/5 bg-white/70 backdrop-blur">
      <nav className="mx-auto flex max-w-6xl items-center justify-between px-6 py-4">
        <Link to="/" className="flex items-center gap-2">
          <span className="inline-block h-3 w-3 rounded-full bg-musper-orange" />
          <span className="font-display text-lg font-semibold tracking-tightish text-musper-green">
            Musper Solutions
          </span>
        </Link>
        <ul className="hidden items-center gap-8 text-sm text-musper-muted md:flex">
          <li>Services</li>
          <li>About</li>
          <li>Contact</li>
        </ul>
      </nav>
    </header>
  );
}
