import { Link } from 'react-router-dom';
import { ArrowUpRight } from 'lucide-react';

const base =
  'group inline-flex items-center gap-2 rounded-full px-5 py-3 text-[0.92rem] font-medium tracking-tight transition-all duration-300 ease-editorial';

const variantClasses = {
  primary:
    `${base} bg-musper-green text-musper-cream shadow-soft hover:bg-musper-green-deep hover:-translate-y-0.5`,
  orange:
    `${base} bg-musper-orange text-musper-cream shadow-cta hover:bg-musper-orange-dark hover:-translate-y-0.5`,
  outline:
    `${base} border border-musper-green/25 text-musper-green hover:bg-musper-green hover:text-musper-cream`,
  outlineLight:
    `${base} border border-musper-cream/30 text-musper-cream hover:bg-musper-cream hover:text-musper-green`,
  ghost:
    `${base} text-musper-ink hover:text-musper-green`,
};

export default function Button({
  variant = 'primary',
  to,
  href,
  children,
  icon: Icon = ArrowUpRight,
  showIcon = true,
  className = '',
  ...props
}) {
  const cls = `${variantClasses[variant] || variantClasses.primary} ${className}`;
  const inner = (
    <>
      <span>{children}</span>
      {showIcon && (
        <Icon
          size={16}
          className="transition-transform duration-300 ease-editorial group-hover:translate-x-0.5 group-hover:-translate-y-0.5"
        />
      )}
    </>
  );
  if (to) return <Link to={to} className={cls} {...props}>{inner}</Link>;
  if (href) return <a href={href} className={cls} {...props}>{inner}</a>;
  return <button className={cls} {...props}>{inner}</button>;
}
