import { useState, useEffect, useRef, useCallback } from 'react';

function formatAbbreviated(n, decimals) {
  const sign = n < 0 ? -1 : 1;
  const v = Math.abs(n);
  let divisor = 1;
  let letter = '';
  if (v >= 1e15) {
    divisor = 1e15;
    letter = 'Q';
  } else if (v >= 1e12) {
    divisor = 1e12;
    letter = 'T';
  } else if (v >= 1e9) {
    divisor = 1e9;
    letter = 'B';
  } else if (v >= 1e6) {
    divisor = 1e6;
    letter = 'M';
  } else if (v >= 1e3) {
    divisor = 1e3;
    letter = 'K';
  }
  const scaled = sign * (v / divisor);
  const fixed = scaled.toFixed(decimals);
  return `${fixed}${letter}`;
}

export default function AnimatedCounter({
  value,
  prefix = '',
  suffix = '',
  duration = 2000,
  decimals = 0,
  className = '',
}) {
  const [display, setDisplay] = useState(0);
  const elRef = useRef(null);
  const rafRef = useRef(null);
  const visibleRef = useRef(false);
  const targetRef = useRef(value);

  const cancelRaf = useCallback(() => {
    if (rafRef.current != null) {
      cancelAnimationFrame(rafRef.current);
      rafRef.current = null;
    }
  }, []);

  const runAnimation = useCallback(
    (from, to) => {
      cancelRaf();
      const start = performance.now();

      const tick = (now) => {
        const elapsed = now - start;
        const progress = Math.min(elapsed / duration, 1);
        const eased = 1 - Math.pow(1 - progress, 3);
        const current = from + (to - from) * eased;
        setDisplay(current);
        if (progress < 1) {
          rafRef.current = requestAnimationFrame(tick);
        } else {
          rafRef.current = null;
          setDisplay(to);
        }
      };

      rafRef.current = requestAnimationFrame(tick);
    },
    [duration, cancelRaf]
  );

  useEffect(() => {
    const el = elRef.current;
    if (!el) return undefined;

    const observer = new IntersectionObserver(
      (entries) => {
        const entry = entries[0];
        visibleRef.current = Boolean(entry?.isIntersecting);
        if (entry?.isIntersecting) {
          targetRef.current = value;
          runAnimation(0, value);
        } else {
          cancelRaf();
          setDisplay(0);
        }
      },
      { threshold: 0.15, rootMargin: '0px' }
    );

    observer.observe(el);
    return () => {
      observer.disconnect();
      cancelRaf();
    };
  }, [value, runAnimation, cancelRaf]);

  useEffect(() => {
    if (!visibleRef.current) return undefined;
    if (value === targetRef.current) return undefined;
    targetRef.current = value;
    const from = display;
    runAnimation(from, value);
    return () => cancelRaf();
    // eslint-disable-next-line react-hooks/exhaustive-deps -- animate from last display when target changes while visible
  }, [value, runAnimation, cancelRaf]);

  const text = `${prefix}${formatAbbreviated(display, decimals)}${suffix}`;

  return (
    <span ref={elRef} className={className}>
      {text}
    </span>
  );
}
