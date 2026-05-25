// Single reusable form field that matches the editorial aesthetic.
export default function FormField({
  label,
  name,
  value,
  onChange,
  type = 'text',
  required,
  textarea,
  placeholder,
  autoComplete,
  hint,
  inputMode,
}) {
  const cls =
    'w-full rounded-2xl border border-musper-line bg-white px-4 py-3 text-base text-musper-ink placeholder:text-musper-muted-soft transition-colors duration-300 focus:border-musper-green focus:outline-none focus:ring-2 focus:ring-musper-green/15 disabled:opacity-60';
  return (
    <label className="block">
      <span className="flex items-center justify-between text-xs font-medium uppercase tracking-eyebrow text-musper-muted">
        <span>{label}</span>
        {hint && <span className="normal-case tracking-tight text-musper-muted-soft">{hint}</span>}
      </span>
      {textarea ? (
        <textarea
          name={name}
          value={value}
          onChange={onChange}
          required={required}
          rows={5}
          placeholder={placeholder}
          className={`${cls} mt-2 resize-y`}
        />
      ) : (
        <input
          type={type}
          name={name}
          value={value}
          onChange={onChange}
          required={required}
          placeholder={placeholder}
          autoComplete={autoComplete}
          inputMode={inputMode}
          className={`${cls} mt-2`}
        />
      )}
    </label>
  );
}
