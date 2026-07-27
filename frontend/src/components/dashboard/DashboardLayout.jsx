import { useEffect, useState } from 'react';
import { Link, NavLink, Outlet, useLocation, useNavigate } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import {
  LayoutDashboard,
  Users,
  BarChart3,
  Settings,
  FileText,
  History,
  User as UserIcon,
  LogOut,
  Menu,
  X,
  Sparkles,
  ChevronRight,
} from 'lucide-react';
import { useAuth } from '../../context/AuthContext';

const ADVISOR_NAV = [
  { to: '/advisor', end: true, label: 'Overview', icon: LayoutDashboard },
  { to: '/advisor/clients', label: 'Clients', icon: Users },
  { to: '/advisor/analytics', label: 'Analytics', icon: BarChart3 },
  { to: '/advisor/settings', label: 'Settings', icon: Settings },
];

const CLIENT_NAV = [
  { to: '/dashboard', end: true, label: 'Overview', icon: LayoutDashboard },
  { to: '/dashboard/reports', label: 'My Reports', icon: FileText },
  { to: '/dashboard/history', label: 'Session History', icon: History },
  { to: '/dashboard/profile', label: 'Profile', icon: UserIcon },
];

export default function DashboardLayout({ role }) {
  const { user, logout } = useAuth();
  const location = useLocation();
  const navigate = useNavigate();
  const [mobileOpen, setMobileOpen] = useState(false);

  // Scroll-reset on route change
  useEffect(() => {
    window.scrollTo({ top: 0, behavior: 'instant' });
    setMobileOpen(false);
  }, [location.pathname]);

  const nav = role === 'advisor' ? ADVISOR_NAV : CLIENT_NAV;
  const homePath = role === 'advisor' ? '/advisor' : '/dashboard';

  return (
    <div className="min-h-screen bg-musper-cream">
      {/* Top bar (mobile) */}
      <div className="sticky top-0 z-30 flex items-center justify-between border-b border-musper-line bg-musper-cream/90 px-5 py-3 backdrop-blur lg:hidden">
        <Link to={homePath} className="flex items-center gap-2">
          <span className="relative flex h-8 w-8 items-center justify-center rounded-full bg-musper-green text-musper-cream font-display text-sm font-semibold">
            M
            <span className="absolute -top-0.5 -right-0.5 h-2 w-2 rounded-full bg-musper-orange" />
          </span>
          <span className="font-display text-base font-semibold tracking-editorial">
            MusperSolutions {role === 'advisor' ? 'Advisor' : 'Client'}
          </span>
        </Link>
        <button
          onClick={() => setMobileOpen((o) => !o)}
          className="flex h-9 w-9 items-center justify-center rounded-full border border-musper-line"
          aria-label="Toggle navigation"
        >
          {mobileOpen ? <X size={16} /> : <Menu size={16} />}
        </button>
      </div>

      <div className="flex">
        {/* Sidebar */}
        <aside className="sticky top-0 hidden h-screen w-72 shrink-0 flex-col border-r border-musper-line bg-musper-cream-soft/80 px-6 py-7 lg:flex">
          <Link to="/" className="flex items-center gap-2.5">
            <span className="relative flex h-10 w-10 items-center justify-center rounded-full bg-musper-green text-musper-cream font-display text-lg font-semibold">
              M
              <span className="absolute -top-0.5 -right-0.5 h-2.5 w-2.5 rounded-full bg-musper-orange" />
            </span>
            <div className="leading-tight">
              <p className="font-display text-base font-semibold tracking-editorial text-musper-ink">
                MusperSolutions
              </p>
              <p className="text-[0.65rem] uppercase tracking-eyebrow text-musper-muted">
                {role === 'advisor' ? 'Advisor workspace' : 'Client dashboard'}
              </p>
            </div>
          </Link>

          <nav className="mt-10 flex-1 space-y-1">
            {nav.map(({ to, end, label, icon: Icon }) => (
              <NavLink
                key={to}
                to={to}
                end={end}
                className={({ isActive }) =>
                  [
                    'group flex items-center justify-between rounded-2xl px-3 py-2.5 text-sm transition-colors duration-200',
                    isActive
                      ? 'bg-musper-green text-musper-cream'
                      : 'text-musper-ink/75 hover:bg-musper-green-soft hover:text-musper-green',
                  ].join(' ')
                }
              >
                {({ isActive }) => (
                  <>
                    <span className="flex items-center gap-3">
                      <Icon size={16} strokeWidth={1.75} />
                      {label}
                    </span>
                    <ChevronRight
                      size={14}
                      className={[
                        'transition-all duration-200',
                        isActive ? 'opacity-100' : 'opacity-0 -translate-x-1 group-hover:translate-x-0 group-hover:opacity-60',
                      ].join(' ')}
                    />
                  </>
                )}
              </NavLink>
            ))}
          </nav>

          {role === 'client' && (
            <Link
              to="/diagnostic"
              className="mb-6 flex items-center gap-2 rounded-2xl border border-musper-orange/30 bg-musper-orange-soft px-4 py-3 text-sm text-musper-orange-dark transition hover:bg-musper-orange hover:text-musper-cream"
            >
              <Sparkles size={15} />
              Start a new diagnostic
            </Link>
          )}

          {/* User card */}
          <div className="rounded-2xl border border-musper-line bg-white px-4 py-4">
            <div className="flex items-center gap-3">
              <span className="flex h-9 w-9 items-center justify-center rounded-full bg-musper-green text-xs font-medium text-musper-cream">
                {(user?.full_name || user?.email || '?')
                  .split(/\s|@/)
                  .filter(Boolean)
                  .slice(0, 2)
                  .map((p) => p[0])
                  .join('')
                  .toUpperCase()}
              </span>
              <div className="min-w-0 flex-1">
                <p className="truncate text-sm font-medium">{user?.full_name || 'Account'}</p>
                <p className="truncate text-xs text-musper-muted">{user?.email}</p>
              </div>
            </div>
            <div className="mt-3 flex gap-2">
              <Link
                to="/"
                className="flex-1 rounded-full border border-musper-line bg-musper-cream-soft px-3 py-1.5 text-center text-xs font-medium text-musper-ink/80 transition hover:border-musper-green/30"
              >
                Site
              </Link>
              <button
                type="button"
                onClick={async () => { await logout(); navigate('/'); }}
                className="flex flex-1 items-center justify-center gap-1 rounded-full border border-musper-line bg-musper-cream-soft px-3 py-1.5 text-xs font-medium text-musper-ink/80 transition hover:border-musper-orange/40 hover:text-musper-orange-dark"
              >
                <LogOut size={11} /> Sign out
              </button>
            </div>
          </div>
        </aside>

        {/* Mobile drawer */}
        <AnimatePresence>
          {mobileOpen && (
            <motion.div
              initial={{ height: 0, opacity: 0 }}
              animate={{ height: 'auto', opacity: 1 }}
              exit={{ height: 0, opacity: 0 }}
              transition={{ duration: 0.25, ease: [0.22, 1, 0.36, 1] }}
              className="absolute left-0 right-0 top-[57px] z-20 overflow-hidden border-b border-musper-line bg-musper-cream-soft lg:hidden"
            >
              <div className="space-y-1 px-5 py-4">
                {nav.map(({ to, end, label, icon: Icon }) => (
                  <NavLink
                    key={to}
                    to={to}
                    end={end}
                    className={({ isActive }) =>
                      [
                        'flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm',
                        isActive
                          ? 'bg-musper-green text-musper-cream'
                          : 'text-musper-ink/75 hover:bg-musper-green-soft',
                      ].join(' ')
                    }
                  >
                    <Icon size={15} />
                    {label}
                  </NavLink>
                ))}
                <button
                  type="button"
                  onClick={async () => { await logout(); navigate('/'); }}
                  className="mt-2 flex w-full items-center gap-3 rounded-xl px-3 py-2.5 text-sm text-musper-ink/75 hover:bg-musper-orange-soft"
                >
                  <LogOut size={15} /> Sign out
                </button>
              </div>
            </motion.div>
          )}
        </AnimatePresence>

        {/* Main content */}
        <main className="min-w-0 flex-1">
          <div className="mx-auto max-w-6xl px-5 py-8 sm:px-8 sm:py-12 lg:px-12 lg:py-14">
            <Outlet />
          </div>
        </main>
      </div>
    </div>
  );
}
