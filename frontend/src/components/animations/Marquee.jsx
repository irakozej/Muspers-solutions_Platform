import { Children } from 'react';
import { motion, useReducedMotion } from 'framer-motion';

// Slow horizontal marquee. Children render twice back-to-back so the loop
// looks seamless. Pauses on hover. Edges fade to background via mask.
export default function Marquee({
  children,
  duration = 38,
  reverse = false,
  pauseOnHover = true,
  className = '',
  itemGap = '2.5rem',
}) {
  const reduce = useReducedMotion();
  const items = Children.toArray(children);

  if (reduce) {
    return (
      <div className={`flex items-center overflow-hidden ${className}`} style={{ gap: itemGap }}>
        {items}
      </div>
    );
  }

  return (
    <div
      className={`group relative overflow-hidden ${className}`}
      style={{
        maskImage:
          'linear-gradient(to right, transparent 0, #000 7%, #000 93%, transparent 100%)',
        WebkitMaskImage:
          'linear-gradient(to right, transparent 0, #000 7%, #000 93%, transparent 100%)',
      }}
    >
      <motion.div
        className="flex items-center w-max"
        style={{ gap: itemGap }}
        initial={{ x: reverse ? '-50%' : 0 }}
        animate={{ x: reverse ? '0%' : '-50%' }}
        transition={{
          duration,
          ease: 'linear',
          repeat: Infinity,
          repeatType: 'loop',
        }}
        {...(pauseOnHover ? { whileHover: { animationPlayState: 'paused' } } : {})}
      >
        {items.map((c, i) => (
          <div key={`a-${i}`} className="shrink-0" style={{ paddingRight: itemGap }}>
            {c}
          </div>
        ))}
        {items.map((c, i) => (
          <div key={`b-${i}`} aria-hidden className="shrink-0" style={{ paddingRight: itemGap }}>
            {c}
          </div>
        ))}
      </motion.div>
    </div>
  );
}
