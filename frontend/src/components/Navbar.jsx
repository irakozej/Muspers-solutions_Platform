import { useEffect, useState } from 'react';
import { Link, NavLink, useLocation } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { Menu, X } from 'lucide-react';
import { navLinks } from '../data/site';
import ChatCTA from './ChatCTA';
import UserMenu from './UserMenu';
import { useAuth } from '../context/AuthContext';

export default function Navbar() {
  const [scrolled, setScrolled] = useState(false);
  const [open, setOpen] = useState(false);
  const location = useLocation();
  const { isAuthenticated, isInitializing } = useAuth();

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 16);
    onScroll();
    window.addEventListener('scroll', onScroll, { passive: true });
    return () => window.removeEventListener('scroll', onScroll);
  }, []);

  useEffect(() => { setOpen(false); }, [location.pathname]);

  return (
    <motion.header
      initial={{ y: -24, opacity: 0 }}
      animate={{ y: 0, opacity: 1 }}
      transition={{ duration: 0.6, ease: [0.22, 1, 0.36, 1] }}
      className={[
        'sticky top-0 z-50 transition-all duration-500 ease-editorial',
        scrolled
          ? 'bg-musper-cream/85 backdrop-blur-md border-b border-musper-line'
          : 'bg-transparent border-b border-transparent',
      ].join(' ')}
    >
      <div className="container flex items-center justify-between py-4 lg:py-5">
        <Link to="/" className="group flex items-center gap-3">
          <span className="relative flex h-9 w-9 items-center justify-center rounded-full bg-musper-green text-musper-cream font-display text-lg font-semibold">
            M
            <span className="absolute -top-0.5 -right-0.5 h-2 w-2 rounded-full bg-musper-orange" />
          </span>
          <span className="font-display text-lg font-semibold tracking-editorial text-musper-ink">
            Musper <span className="text-musper-muted-soft">Solutions</span>
          </span>
        </Link>

        <nav className="hidden items-center gap-1 lg:flex">
          {navLinks.map((link) => (
            <NavLink
              key={link.to}
              to={link.to}
              end={link.to === '/'}
              className={({ isActive }) =>
                [
                  'relative rounded-full px-3.5 py-2 text-sm tracking-tight transition-colors duration-300',
                  isActive ? 'text-musper-green' : 'text-musper-ink/70 hover:text-musper-green',
                ].join(' ')
              }
            >
              {({ isActive }) => (
                <span className="flex items-center gap-1.5">
                  {link.label}
                  {isActive && (
                    <motion.span
                      layoutId="nav-dot"
                      className="h-1.5 w-1.5 rounded-full bg-musper-orange"
                      transition={{ type: 'spring', stiffness: 400, damping: 30 }}
                    />
                  )}
                </span>
              )}
            </NavLink>
          ))}
        </nav>

        <div className="hidden items-center gap-3 lg:flex">
          {isInitializing ? (
            <div className="h-9 w-32 rounded-full bg-musper-cream-soft" />
          ) : isAuthenticated ? (
            <>
              <ChatCTA />
              <UserMenu />
            </>
          ) : (
            <>
              <Link
                to="/login"
                className="text-sm font-medium text-musper-ink/80 transition-colors hover:text-musper-green"
              >
                Sign in
              </Link>
              <Link
                to="/signup"
                className="inline-flex items-center gap-2 rounded-full bg-musper-green px-5 py-2.5 text-sm font-medium text-musper-cream shadow-soft transition-all duration-300 hover:-translate-y-0.5 hover:bg-musper-green-deep"
              >
                Create account
              </Link>
            </>
          )}
        </div>

        <button
          type="button"
          onClick={() => setOpen((o) => !o)}
          className="flex h-10 w-10 items-center justify-center rounded-full border border-musper-line text-musper-ink lg:hidden"
          aria-label="Toggle menu"
        >
          {open ? <X size={18} /> : <Menu size={18} />}
        </button>
      </div>

      <AnimatePresence>
        {open && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.35, ease: [0.22, 1, 0.36, 1] }}
            className="overflow-hidden border-t border-musper-line bg-musper-cream/95 backdrop-blur-md lg:hidden"
          >
            <div className="container flex flex-col gap-1 py-4">
              {navLinks.map((link) => (
                <NavLink
                  key={link.to}
                  to={link.to}
                  end={link.to === '/'}
                  className={({ isActive }) =>
                    [
                      'flex items-center justify-between rounded-xl px-4 py-3 text-base transition-colors',
                      isActive ? 'bg-musper-green text-musper-cream' : 'text-musper-ink hover:bg-musper-green-soft',
                    ].join(' ')
                  }
                >
                  {link.label}
                </NavLink>
              ))}
              <div className="my-2 h-px bg-musper-line" />
              {isAuthenticated ? (
                <>
                  <NavLink
                    to="/profile"
                    className={({ isActive }) =>
                      [
                        'flex items-center justify-between rounded-xl px-4 py-3 text-base transition-colors',
                        isActive ? 'bg-musper-green text-musper-cream' : 'text-musper-ink hover:bg-musper-green-soft',
                      ].join(' ')
                    }
                  >
                    Account
                  </NavLink>
                  <div className="mt-2">
                    <ChatCTA />
                  </div>
                </>
              ) : (
                <>
                  <Link
                    to="/login"
                    className="flex items-center justify-between rounded-xl px-4 py-3 text-base text-musper-ink hover:bg-musper-green-soft"
                  >
                    Sign in
                  </Link>
                  <Link
                    to="/signup"
                    className="mt-2 inline-flex items-center justify-center gap-2 rounded-full bg-musper-green px-5 py-3 text-sm font-medium text-musper-cream"
                  >
                    Create account
                  </Link>
                </>
              )}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.header>
  );
}
