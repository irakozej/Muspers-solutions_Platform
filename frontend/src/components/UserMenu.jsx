import { useEffect, useRef, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { ChevronDown, User as UserIcon, LogOut, ShieldCheck } from 'lucide-react';
import { useAuth } from '../context/AuthContext';

function initialsOf(user) {
  const source = user?.full_name || user?.email || '?';
  const parts = source.split(/\s+|@/).filter(Boolean);
  const first = parts[0]?.[0] || '?';
  const second = parts[1]?.[0] || '';
  return (first + second).toUpperCase();
}

export default function UserMenu() {
  const { user, logout } = useAuth();
  const [open, setOpen] = useState(false);
  const ref = useRef(null);
  const navigate = useNavigate();

  useEffect(() => {
    const onClick = (e) => {
      if (ref.current && !ref.current.contains(e.target)) setOpen(false);
    };
    document.addEventListener('mousedown', onClick);
    return () => document.removeEventListener('mousedown', onClick);
  }, []);

  if (!user) return null;
  const isAdvisor = user.role === 'advisor';

  return (
    <div ref={ref} className="relative">
      <button
        type="button"
        onClick={() => setOpen((o) => !o)}
        className="group flex items-center gap-2 rounded-full border border-musper-line bg-musper-cream-soft py-1.5 pl-1.5 pr-3 transition-colors duration-300 hover:border-musper-green/30"
      >
        <span className="flex h-8 w-8 items-center justify-center rounded-full bg-musper-green text-xs font-medium text-musper-cream">
          {initialsOf(user)}
        </span>
        <span className="hidden text-sm font-medium tracking-tight text-musper-ink sm:block">
          {user.full_name?.split(' ')[0] || 'Account'}
        </span>
        <ChevronDown
          size={14}
          className={`text-musper-muted transition-transform duration-300 ${open ? 'rotate-180' : ''}`}
        />
      </button>

      <AnimatePresence>
        {open && (
          <motion.div
            initial={{ opacity: 0, y: -8, scale: 0.97 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: -8, scale: 0.97 }}
            transition={{ duration: 0.25, ease: [0.22, 1, 0.36, 1] }}
            className="absolute right-0 mt-3 w-72 origin-top-right overflow-hidden rounded-2xl border border-musper-line bg-musper-cream-soft shadow-soft"
          >
            <div className="border-b border-musper-line px-5 py-4">
              <p className="text-xs uppercase tracking-eyebrow text-musper-muted">Signed in as</p>
              <p className="mt-2 font-display text-lg leading-tight tracking-editorial text-musper-ink">
                {user.full_name || 'Account'}
              </p>
              <p className="mt-0.5 truncate text-sm text-musper-muted">{user.email}</p>
              <span className="mt-3 inline-flex items-center gap-1.5 rounded-full bg-musper-green-soft px-2.5 py-1 text-[0.65rem] font-medium uppercase tracking-eyebrow text-musper-green">
                {isAdvisor ? <ShieldCheck size={11} /> : <UserIcon size={11} />}
                {user.role}
              </span>
            </div>
            <div className="p-2">
              <Link
                to="/profile"
                onClick={() => setOpen(false)}
                className="flex items-center gap-2 rounded-xl px-3 py-2 text-sm text-musper-ink transition-colors hover:bg-musper-green-soft"
              >
                <UserIcon size={15} /> Account & profile
              </Link>
              <button
                type="button"
                onClick={async () => {
                  setOpen(false);
                  await logout();
                  navigate('/');
                }}
                className="flex w-full items-center gap-2 rounded-xl px-3 py-2 text-sm text-musper-ink transition-colors hover:bg-musper-orange-soft"
              >
                <LogOut size={15} /> Sign out
              </button>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
