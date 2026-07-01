import { useEffect, useRef } from 'react';
import {
  motion,
  useMotionValue,
  useTransform,
  animate,
  useInView,
  useReducedMotion,
} from 'framer-motion';

// Animated number counter.
// Accepts values like "2000+", "15+", "45+", "10" - parses the digits, counts
// up from 0 on viewport-enter, and re-attaches any non-digit suffix ("+", "%").
// Respects prefers-reduced-motion: when set, the final value is shown instantly.
export default function CountUp({
  value,
  duration = 1.8,
  className = '',
  startOnView = true,
}) {
  const raw = String(value ?? '');
  const match = raw.match(/^(\d+(?:\.\d+)?)(.*)$/);
  const target = match ? Number(match[1]) : 0;
  const suffix = match ? match[2] : raw;
  const isFloat = !!match && match[1].includes('.');

  const ref = useRef(null);
  const inView = useInView(ref, { once: true, margin: '-80px' });
  const reduce = useReducedMotion();

  const mv = useMotionValue(reduce ? target : 0);
  const display = useTransform(mv, (v) => (isFloat ? v.toFixed(1) : Math.round(v).toString()));

  useEffect(() => {
    if (reduce) return;
    if (startOnView && !inView) return;
    const controls = animate(mv, target, {
      duration,
      ease: [0.22, 1, 0.36, 1],
    });
    return () => controls.stop();
  }, [inView, startOnView, target, duration, mv, reduce]);

  return (
    <span ref={ref} className={`tabular-nums ${className}`}>
      <motion.span>{display}</motion.span>
      {suffix}
    </span>
  );
}
