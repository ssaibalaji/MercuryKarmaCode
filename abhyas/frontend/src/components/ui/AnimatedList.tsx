import { motion } from 'framer-motion';
import type { CSSProperties, ReactNode } from 'react';

const containerVariants = {
  hidden: {},
  visible: {
    transition: { staggerChildren: 0.08 },
  },
};

const itemVariants = {
  hidden: { opacity: 0, y: 20 },
  visible: { opacity: 1, y: 0 },
};

interface AnimatedListProps {
  children: ReactNode[];
  style?: CSSProperties;
  className?: string;
}

export function AnimatedList({ children, style, className }: AnimatedListProps) {
  return (
    <motion.div
      initial="hidden"
      animate="visible"
      variants={containerVariants}
      className={className}
      style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem', ...style }}
    >
      {children.map((child, index) => (
        <motion.div key={index} variants={itemVariants}>
          {child}
        </motion.div>
      ))}
    </motion.div>
  );
}
