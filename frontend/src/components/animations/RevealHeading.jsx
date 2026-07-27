import { Children, cloneElement, isValidElement, useRef } from 'react';
import { motion, useReducedMotion } from 'framer-motion';

// Word-by-word reveal for headings that may contain styled spans.
//
// Walks the React tree recursively: string children get split into words and
// each word is wrapped in a `motion.span` that fades + slides + un-blurs on
// mount. Non-string children (spans, breaks, italic accents) keep their
// styling, their inner text is what gets word-split.
//
// Stagger ~55ms per word feels alive without dragging. Words use a single
// spring-like easing so the line settles together.
export default function RevealHeading({
  children,
  as = 'h1',
  className = '',
  delay = 0,
  stagger = 0.055,
  blurStart = 8,
  inView = false,        // when true, trigger on viewport-enter instead of mount
}) {
  const reduce = useReducedMotion();
  const counter = useRef(0);
  counter.current = 0;

  const buildSpan = (word, key) => {
    const i = counter.current++;
    if (reduce) {
      return (
        <span key={key} style={{ display: 'inline-block' }}>
          {word}
        </span>
      );
    }
    return (
      <motion.span
        key={key}
        initial={{ opacity: 0, y: 18, filter: `blur(${blurStart}px)` }}
        {...(inView
          ? {
              whileInView: { opacity: 1, y: 0, filter: 'blur(0px)' },
              viewport: { once: true, margin: '-60px' },
            }
          : { animate: { opacity: 1, y: 0, filter: 'blur(0px)' } })}
        transition={{
          duration: 0.7,
          delay: delay + i * stagger,
          ease: [0.22, 1, 0.36, 1],
        }}
        style={{ display: 'inline-block', willChange: 'transform, opacity, filter' }}
      >
        {word}
      </motion.span>
    );
  };

  const processNode = (node, keyPrefix) => {
    if (node == null || typeof node === 'boolean') return node;

    if (typeof node === 'string' || typeof node === 'number') {
      const str = String(node);
      // Preserve original whitespace (single spaces, multi-spaces, etc.).
      const tokens = str.split(/(\s+)/);
      return tokens.map((tok, i) => {
        if (tok === '') return null;
        if (/^\s+$/.test(tok)) return tok; // whitespace as-is
        return buildSpan(tok, `${keyPrefix}-${i}`);
      });
    }

    if (Array.isArray(node)) {
      return node.map((n, i) => processNode(n, `${keyPrefix}-${i}`));
    }

    if (isValidElement(node)) {
      // <br/> and similar void elements - leave alone.
      if (typeof node.type === 'string' && node.type === 'br') {
        return node;
      }
      const childArray = Children.toArray(node.props?.children ?? []);
      const newChildren = childArray.map((c, i) => processNode(c, `${keyPrefix}-${i}`));
      return cloneElement(node, { ...node.props }, newChildren);
    }

    return node;
  };

  const Tag = as;
  return <Tag className={className}>{processNode(children, 'rh')}</Tag>;
}
