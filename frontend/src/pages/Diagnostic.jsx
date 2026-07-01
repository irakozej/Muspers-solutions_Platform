import { useEffect, useRef, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Sparkles, Send, MessageCircle, Loader2, Check, ArrowUpRight, AlertCircle,
} from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { diagnosticApi, STAGE_ORDER, STAGE_LABELS } from '../services/diagnostic';

export default function Diagnostic() {
  const { user, isAuthenticated, isInitializing } = useAuth();

  if (isInitializing) {
    return (
      <SplashShell>
        <p className="text-sm text-musper-muted">Checking your session...</p>
      </SplashShell>
    );
  }
  if (!isAuthenticated) return <SignedOutScreen />;
  if (user?.role === 'advisor') return <AdvisorScreen />;
  if (user?.role !== 'client') return <UnsupportedScreen />;
  return <DiagnosticInterview />;
}

// ───────────────────── auth / role gates ─────────────────────

function SignedOutScreen() {
  return (
    <SplashShell>
      <p className="eyebrow">Diagnostic</p>
      <h1 className="mt-6 font-display text-[2.25rem] leading-[1.05] tracking-editorial sm:text-[3rem] text-balance">
        Sign in to start your diagnostic.
      </h1>
      <p className="mt-6 max-w-xl text-base leading-relaxed text-musper-muted">
        The Musper diagnostic is a guided fifteen to twenty minute conversation.
        We ask a few structured questions and the report goes to Penny first.
      </p>
      <div className="mt-8 flex flex-wrap gap-3">
        <Link
          to="/login"
          state={{ from: '/diagnostic' }}
          className="inline-flex items-center gap-2 rounded-full bg-musper-green px-5 py-3 text-sm font-medium text-musper-cream shadow-soft hover:-translate-y-0.5 hover:bg-musper-green-deep transition-all duration-300"
        >
          Sign in
        </Link>
        <Link
          to="/signup"
          state={{ from: '/diagnostic' }}
          className="inline-flex items-center gap-2 rounded-full border border-musper-line bg-musper-cream-soft px-5 py-3 text-sm font-medium text-musper-ink/80 hover:border-musper-green/30 transition-all duration-300"
        >
          Create account
        </Link>
      </div>
    </SplashShell>
  );
}

function AdvisorScreen() {
  return (
    <SplashShell>
      <p className="eyebrow">Advisor view</p>
      <h1 className="mt-6 font-display text-[2.25rem] leading-[1.05] tracking-editorial sm:text-[3rem] text-balance">
        This is the client-side interview.
      </h1>
      <p className="mt-6 max-w-xl text-base leading-relaxed text-musper-muted">
        Clients run the diagnostic from this page. As an advisor, your view of
        sessions, reports, and clients lives in the workspace.
      </p>
      <div className="mt-8 flex flex-wrap gap-3">
        <Link
          to="/advisor"
          className="inline-flex items-center gap-2 rounded-full bg-musper-green px-5 py-3 text-sm font-medium text-musper-cream shadow-soft hover:-translate-y-0.5 hover:bg-musper-green-deep transition-all duration-300"
        >
          Open advisor dashboard <ArrowUpRight size={14} />
        </Link>
      </div>
    </SplashShell>
  );
}

function UnsupportedScreen() {
  return (
    <SplashShell>
      <h1 className="font-display text-3xl tracking-editorial">Your account can't access this page.</h1>
    </SplashShell>
  );
}

// ───────────────────── splash & interview ─────────────────────

function SplashShell({ children }) {
  return (
    <section className="container py-24 lg:py-32">
      <motion.div
        initial={{ opacity: 0, y: 12 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
        className="mx-auto max-w-3xl"
      >
        {children}
      </motion.div>
    </section>
  );
}

function DiagnosticInterview() {
  const [session, setSession] = useState(null);    // {id, progress, complete}
  const [messages, setMessages] = useState([]);    // [{id, role, content, created_at}]
  const [pending, setPending] = useState(false);
  const [starting, setStarting] = useState(false);
  const [draft, setDraft] = useState('');
  const [error, setError] = useState(null);
  const navigate = useNavigate();

  const start = async () => {
    setStarting(true);
    setError(null);
    try {
      const data = await diagnosticApi.start();
      setSession({
        id: data.session_id,
        progress: data.progress,
        complete: data.is_complete,
      });
      setMessages([data.message]);
    } catch (e) {
      setError(e?.message || 'Could not start the diagnostic.');
    } finally {
      setStarting(false);
    }
  };

  const send = async (e) => {
    e?.preventDefault?.();
    const content = draft.trim();
    if (!content || pending || !session) return;
    const placeholder = {
      id: `local-${Date.now()}`,
      role: 'user',
      content,
      created_at: new Date().toISOString(),
    };
    setMessages((m) => [...m, placeholder]);
    setDraft('');
    setPending(true);
    setError(null);
    try {
      const data = await diagnosticApi.sendMessage(session.id, content);
      setSession((s) => ({ ...s, progress: data.progress, complete: data.is_complete }));
      setMessages((m) => [...m, data.message]);
    } catch (e) {
      setMessages((m) => m.filter((mm) => mm.id !== placeholder.id));
      setDraft(content);
      setError(e?.message || 'The message did not go through.');
    } finally {
      setPending(false);
    }
  };

  // No session yet -> splash
  if (!session) {
    return (
      <SplashShell>
        <p className="eyebrow">Diagnostic</p>
        <h1 className="mt-6 font-display text-[2.25rem] leading-[1.05] tracking-editorial sm:text-[3.5rem] text-balance">
          A guided fifteen to twenty minute conversation about your business.
        </h1>
        <p className="mt-6 max-w-2xl text-base leading-relaxed text-musper-muted">
          We'll ask short, plain questions about how the business is really doing.
          Nothing fancy. The report goes to Penny first, who decides what to share back with you.
          Find a quiet moment, this works best in one sitting.
        </p>
        {error && <ErrorBox message={error} />}
        <div className="mt-10 flex flex-wrap gap-3">
          <button
            type="button"
            onClick={start}
            disabled={starting}
            className="inline-flex items-center gap-2 rounded-full bg-musper-orange px-6 py-3 text-sm font-medium text-musper-cream shadow-cta hover:-translate-y-0.5 hover:bg-musper-orange-dark transition-all duration-300 disabled:cursor-not-allowed disabled:opacity-60"
          >
            {starting ? <Loader2 size={15} className="animate-spin" /> : <Sparkles size={15} />}
            {starting ? 'Starting...' : 'Begin diagnostic'}
          </button>
          <Link
            to="/dashboard"
            className="inline-flex items-center gap-2 rounded-full border border-musper-line bg-musper-cream-soft px-6 py-3 text-sm font-medium text-musper-ink/80 hover:border-musper-green/30 transition-all duration-300"
          >
            Not now
          </Link>
        </div>
      </SplashShell>
    );
  }

  // Completed -> thank you
  if (session.complete) {
    return (
      <SplashShell>
        <motion.div
          initial={{ scale: 0.85, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          transition={{ type: 'spring', stiffness: 200, damping: 18 }}
          className="flex h-14 w-14 items-center justify-center rounded-full bg-musper-green text-musper-cream"
        >
          <Check size={22} />
        </motion.div>
        <h1 className="mt-8 font-display text-[2.25rem] leading-[1.05] tracking-editorial sm:text-[3rem] text-balance">
          Thank you, your diagnostic is complete.
        </h1>
        <p className="mt-6 max-w-xl text-base leading-relaxed text-musper-muted">
          Penny will personally review your responses and put together a report.
          You'll see it on your dashboard once she's shared it with you.
        </p>
        <div className="mt-10 flex flex-wrap gap-3">
          <button
            type="button"
            onClick={() => navigate('/dashboard')}
            className="inline-flex items-center gap-2 rounded-full bg-musper-green px-6 py-3 text-sm font-medium text-musper-cream shadow-soft hover:-translate-y-0.5 hover:bg-musper-green-deep transition-all duration-300"
          >
            Back to dashboard <ArrowUpRight size={14} />
          </button>
        </div>
      </SplashShell>
    );
  }

  // Active interview
  return (
    <section className="bg-musper-cream-soft/40 min-h-[calc(100vh-5rem)]">
      <div className="container mx-auto max-w-3xl px-4 py-8 sm:px-6 sm:py-12">
        <ProgressBar progress={session.progress} />
        <Transcript messages={messages} pending={pending} />
        {error && <ErrorBox message={error} />}
        <Composer
          draft={draft}
          setDraft={setDraft}
          onSend={send}
          disabled={pending || session.complete}
        />
      </div>
    </section>
  );
}

// ───────────────────── progress, transcript, composer ─────────────────────

function ProgressBar({ progress }) {
  const currentIdx = STAGE_ORDER.indexOf(progress?.stage || 'snapshot');
  return (
    <div className="mb-6 flex items-center gap-2 text-xs">
      {STAGE_ORDER.slice(0, 4).map((stage, i) => {
        const active = i === currentIdx;
        const done = i < currentIdx;
        return (
          <div key={stage} className="flex flex-1 items-center gap-2">
            <span
              className={[
                'flex h-2 w-2 shrink-0 rounded-full transition-colors duration-500',
                done ? 'bg-musper-green' : active ? 'bg-musper-orange' : 'bg-musper-line',
              ].join(' ')}
            />
            <span
              className={[
                'truncate font-medium uppercase tracking-eyebrow',
                active ? 'text-musper-orange' : done ? 'text-musper-green' : 'text-musper-muted-soft',
              ].join(' ')}
            >
              {STAGE_LABELS[stage]}
            </span>
            {i < STAGE_ORDER.length - 2 && (
              <span className="hidden flex-1 border-t border-dashed border-musper-line sm:block" />
            )}
          </div>
        );
      })}
    </div>
  );
}

function Transcript({ messages, pending }) {
  const endRef = useRef(null);
  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: 'smooth', block: 'end' });
  }, [messages.length, pending]);

  return (
    <div className="rounded-3xl border border-musper-line bg-white p-5 shadow-soft sm:p-7">
      <div className="space-y-5">
        <AnimatePresence initial={false}>
          {messages.map((m) => (
            <MessageBubble key={m.id} message={m} />
          ))}
          {pending && (
            <motion.div
              key="typing"
              initial={{ opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -4 }}
              className="flex items-start gap-3"
            >
              <Avatar role="assistant" />
              <div className="flex h-9 items-center gap-1 rounded-2xl bg-musper-green-soft px-4 py-2 text-musper-green">
                <Dot delay={0} />
                <Dot delay={0.15} />
                <Dot delay={0.30} />
              </div>
            </motion.div>
          )}
        </AnimatePresence>
        <div ref={endRef} />
      </div>
    </div>
  );
}

function MessageBubble({ message }) {
  const isAssistant = message.role === 'assistant';
  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.45, ease: [0.22, 1, 0.36, 1] }}
      className={['flex items-start gap-3', isAssistant ? '' : 'flex-row-reverse'].join(' ')}
    >
      <Avatar role={message.role} />
      <div
        className={[
          'max-w-[78%] whitespace-pre-wrap rounded-2xl px-4 py-3 text-[0.95rem] leading-relaxed',
          isAssistant
            ? 'rounded-tl-sm bg-musper-green-soft text-musper-ink'
            : 'rounded-tr-sm bg-musper-orange text-musper-cream',
        ].join(' ')}
      >
        {message.content}
      </div>
    </motion.div>
  );
}

function Avatar({ role }) {
  if (role === 'assistant') {
    return (
      <span className="relative flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-musper-green text-musper-cream font-display text-sm font-semibold">
        M
        <span className="absolute -top-0.5 -right-0.5 h-2 w-2 rounded-full bg-musper-orange" />
      </span>
    );
  }
  return (
    <span className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-musper-orange-soft text-musper-orange-dark">
      <MessageCircle size={15} />
    </span>
  );
}

function Dot({ delay }) {
  return (
    <motion.span
      className="h-1.5 w-1.5 rounded-full bg-current"
      animate={{ y: [0, -4, 0], opacity: [0.4, 1, 0.4] }}
      transition={{ duration: 0.9, repeat: Infinity, delay, ease: 'easeInOut' }}
    />
  );
}

function Composer({ draft, setDraft, onSend, disabled }) {
  const onKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      onSend();
    }
  };
  return (
    <form onSubmit={onSend} className="mt-6">
      <div className="flex items-end gap-3 rounded-3xl border border-musper-line bg-white p-3 shadow-soft focus-within:border-musper-green/40">
        <textarea
          value={draft}
          onChange={(e) => setDraft(e.target.value)}
          onKeyDown={onKeyDown}
          rows={1}
          placeholder={disabled ? 'Listening...' : 'Type your answer here'}
          className="flex-1 resize-none bg-transparent px-3 py-2 text-[0.95rem] text-musper-ink placeholder:text-musper-muted-soft focus:outline-none"
          style={{ minHeight: '2.5rem', maxHeight: '10rem' }}
        />
        <button
          type="submit"
          disabled={disabled || !draft.trim()}
          className="inline-flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-musper-green text-musper-cream transition-all duration-300 hover:-translate-y-0.5 hover:bg-musper-green-deep disabled:cursor-not-allowed disabled:opacity-50"
          aria-label="Send"
        >
          <Send size={15} />
        </button>
      </div>
      <p className="mt-2 px-2 text-[0.7rem] uppercase tracking-eyebrow text-musper-muted-soft">
        Enter to send · Shift+Enter for a new line
      </p>
    </form>
  );
}

function ErrorBox({ message }) {
  return (
    <div className="mt-6 flex items-start gap-3 rounded-2xl border border-musper-orange/30 bg-musper-orange-soft px-4 py-3 text-sm text-musper-orange-dark">
      <AlertCircle size={16} className="mt-0.5 shrink-0" />
      <span>{message}</span>
    </div>
  );
}
