// Password field with a show/hide toggle. Looks exactly like FormField.
// Each instance keeps its own visibility, so two of them on one form
// (password + confirm) toggle independently.
import { useId, useLayoutEffect, useRef, useState } from 'react';
import { Eye, EyeOff } from 'lucide-react';

export default function PasswordInput({
  label,
  name,
  value,
  onChange,
  autoComplete,
  required,
  hint,
  error,
}) {
  const [visible, setVisible] = useState(false);
  const inputRef = useRef(null);
  const caret = useRef(null); // selection to restore after the type switch
  const errorId = useId();

  // Switching type can reset the caret in some browsers; put it back.
  useLayoutEffect(() => {
    const el = inputRef.current;
    if (el && caret.current && document.activeElement === el) {
      el.setSelectionRange(caret.current.start, caret.current.end);
    }
    caret.current = null;
  }, [visible]);

  const toggle = () => {
    const el = inputRef.current;
    if (el && document.activeElement === el) {
      caret.current = { start: el.selectionStart, end: el.selectionEnd };
    }
    setVisible((v) => !v);
  };

  const cls =
    'w-full rounded-2xl border bg-white py-3 pl-4 pr-12 text-base text-musper-ink placeholder:text-musper-muted-soft transition-colors duration-300 focus:outline-none focus:ring-2 disabled:opacity-60';
  const tone = error
    ? 'border-musper-orange focus:border-musper-orange focus:ring-musper-orange/20'
    : 'border-musper-line focus:border-musper-green focus:ring-musper-green/15';

  return (
    <div>
      <label className="block">
        <span className="flex items-center justify-between text-xs font-medium uppercase tracking-eyebrow text-musper-muted">
          <span>{label}</span>
          {hint && <span className="normal-case tracking-tight text-musper-muted-soft">{hint}</span>}
        </span>
        <span className="relative mt-2 block">
          <input
            ref={inputRef}
            type={visible ? 'text' : 'password'}
            name={name}
            value={value}
            onChange={onChange}
            required={required}
            autoComplete={autoComplete}
            autoCapitalize="none"
            autoCorrect="off"
            spellCheck={false}
            aria-invalid={error ? true : undefined}
            aria-describedby={error ? errorId : undefined}
            className={`${cls} ${tone}`}
          />
          <button
            type="button"
            onClick={toggle}
            // Keep focus (and the caret) in the field when tapped with a mouse.
            onMouseDown={(e) => e.preventDefault()}
            aria-label={visible ? 'Hide password' : 'Show password'}
            aria-pressed={visible}
            className="absolute right-1 top-1/2 flex h-11 w-11 -translate-y-1/2 items-center justify-center rounded-full text-musper-muted transition-colors hover:text-musper-green focus-visible:outline focus-visible:outline-2 focus-visible:outline-musper-green"
          >
            {visible ? <EyeOff size={18} aria-hidden="true" /> : <Eye size={18} aria-hidden="true" />}
          </button>
        </span>
      </label>
      {error && (
        <p id={errorId} role="alert" className="mt-2 text-sm text-musper-orange-dark">
          {error}
        </p>
      )}
    </div>
  );
}
