import { motion } from 'framer-motion';
import type { CSSProperties, ReactNode } from 'react';

interface PageWrapperProps {
  children: ReactNode;
  style?: CSSProperties;
  className?: string;
}

export function PageWrapper({ children, style, className }: PageWrapperProps) {
  return (
    <motion.div
      initial={{ opacity: 0, x: -20 }}
      animate={{ opacity: 1, x: 0 }}
      exit={{ opacity: 0, x: 20 }}
      transition={{ duration: 0.3 }}
      className={className}
      style={{ minHeight: '100vh', ...style }}
    >
      {children}
    </motion.div>
  );
}
