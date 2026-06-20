import { motion, Transition } from 'framer-motion';
import { ReactNode } from 'react';

// `chakra()` overlays Chakra's CSS `transition` style prop on top of
// framer-motion's animation-config `transition` prop, so the combined
// component's `transition` type collapses to Chakra's CSS string type. We
// only need the motion props here, so a plain `motion.div` (styled with
// Chakra's `minH` via `style`) avoids the prop name clash entirely.
const MotionDiv = motion.div;

interface PageWrapperProps {
  children: ReactNode;
}

const pageTransition: Transition = { duration: 0.3 };

export function PageWrapper({ children }: PageWrapperProps) {
  return (
    <MotionDiv
      initial={{ opacity: 0, x: -20 }}
      animate={{ opacity: 1, x: 0 }}
      exit={{ opacity: 0, x: 20 }}
      transition={pageTransition}
      style={{ minHeight: '100vh' }}
    >
      {children}
    </MotionDiv>
  );
}
