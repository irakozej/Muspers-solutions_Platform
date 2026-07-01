import { motion, useScroll, useSpring, useReducedMotion } from 'framer-motion';

// Thin orange progress bar pinned to the top of the viewport.
// Spring-smoothed so it feels "weighted" rather than tracking scroll exactly.
export default function ScrollProgress() {
  const { scrollYProgress } = useScroll();
  const scaleX = useSpring(scrollYProgress, { stiffness: 220, damping: 32, mass: 0.6 });
  const reduce = useReducedMotion();
  if (reduce) return null;
  return (
    <motion.div
      aria-hidden
      className="fixed inset-x-0 top-0 z-[60] h-[2px] origin-left bg-musper-orange/90"
      style={{ scaleX }}
    />
  );
}
