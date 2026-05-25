import { motion } from 'framer-motion';

const variants = {
  hidden: { opacity: 0, y: 22 },
  visible: (delay) => ({
    opacity: 1,
    y: 0,
    transition: { duration: 0.7, ease: [0.22, 1, 0.36, 1], delay },
  }),
};

export default function Reveal({
  children,
  delay = 0,
  as: Tag = 'div',
  className = '',
  once = true,
  amount = 0.25,
}) {
  const MotionTag = motion[Tag] || motion.div;
  return (
    <MotionTag
      className={className}
      variants={variants}
      initial="hidden"
      whileInView="visible"
      viewport={{ once, amount }}
      custom={delay}
    >
      {children}
    </MotionTag>
  );
}
