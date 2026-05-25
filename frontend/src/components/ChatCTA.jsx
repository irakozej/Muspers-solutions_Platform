import { Link } from 'react-router-dom';
import { MessageCircle, ArrowUpRight } from 'lucide-react';

// Distinctive recurring CTA — used inline on Home, Services, etc.
// A wider, editorial pill with a chat icon and a leading orange dot.
export default function ChatCTA({ to = '/diagnostic', label = 'Chat with our assistant', tone = 'light', className = '' }) {
  const dark = tone === 'dark';
  return (
    <Link
      to={to}
      className={[
        'group inline-flex items-center gap-3 rounded-full pl-2 pr-5 py-2 transition-all duration-500 ease-editorial',
        dark
          ? 'bg-musper-cream text-musper-green hover:bg-musper-orange hover:text-musper-cream'
          : 'bg-musper-green text-musper-cream hover:bg-musper-green-deep',
        'shadow-soft hover:-translate-y-0.5',
        className,
      ].join(' ')}
    >
      <span
        className={[
          'flex h-9 w-9 items-center justify-center rounded-full transition-colors duration-500 ease-editorial',
          dark
            ? 'bg-musper-green text-musper-cream group-hover:bg-musper-cream group-hover:text-musper-orange'
            : 'bg-musper-orange text-musper-cream',
        ].join(' ')}
      >
        <MessageCircle size={16} strokeWidth={1.75} />
      </span>
      <span className="flex items-center gap-2 text-[0.95rem] font-medium tracking-tight">
        {label}
        <ArrowUpRight
          size={15}
          className="opacity-70 transition-transform duration-500 ease-editorial group-hover:translate-x-0.5 group-hover:-translate-y-0.5 group-hover:opacity-100"
        />
      </span>
    </Link>
  );
}
