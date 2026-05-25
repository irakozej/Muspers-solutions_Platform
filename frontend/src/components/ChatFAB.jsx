import { useEffect, useState } from 'react';
import { useLocation, Link } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { MessageCircle } from 'lucide-react';

// Floating Action Button — site-wide bottom-right access to the (future) assistant.
// Hides itself on the /diagnostic page (where the chat itself will live).
export default function ChatFAB() {
  const location = useLocation();
  const [visible, setVisible] = useState(false);

  useEffect(() => {
    // Briefly delay first appearance so it doesn't pop in on top of the hero.
    const t = setTimeout(() => setVisible(true), 700);
    return () => clearTimeout(t);
  }, []);

  if (location.pathname.startsWith('/diagnostic')) return null;

  return (
    <AnimatePresence>
      {visible && (
        <motion.div
          initial={{ opacity: 0, y: 24, scale: 0.9 }}
          animate={{ opacity: 1, y: 0, scale: 1 }}
          exit={{ opacity: 0, y: 24, scale: 0.9 }}
          transition={{ duration: 0.45, ease: [0.22, 1, 0.36, 1] }}
          className="fixed bottom-6 right-6 z-40 sm:bottom-8 sm:right-8"
        >
          <Link
            to="/diagnostic"
            className="group relative flex items-center gap-3 rounded-full bg-musper-green pl-4 pr-5 py-3 text-musper-cream shadow-soft transition-all duration-500 ease-editorial hover:bg-musper-orange hover:-translate-y-0.5"
            aria-label="Chat with our assistant"
          >
            <span className="absolute -left-1 -top-1 h-3 w-3 rounded-full bg-musper-orange shadow-[0_0_0_4px_rgba(245,242,234,1)] transition-colors duration-500 group-hover:bg-musper-cream" />
            <MessageCircle size={18} strokeWidth={1.75} />
            <span className="hidden text-sm font-medium tracking-tight sm:inline">
              Chat with our assistant
            </span>
            <span className="text-sm font-medium tracking-tight sm:hidden">Chat</span>
          </Link>
        </motion.div>
      )}
    </AnimatePresence>
  );
}
