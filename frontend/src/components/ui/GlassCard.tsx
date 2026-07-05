import { Box, type BoxProps } from '@chakra-ui/react';
import { motion } from 'framer-motion';
import type { ReactNode } from 'react';

interface GlassCardProps extends BoxProps {
  children: ReactNode;
}

export function GlassCard({ children, ...rest }: GlassCardProps) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      whileHover={{ scale: 1.02, y: -5 }}
      transition={{ duration: 0.25 }}
    >
      <Box
        p={6}
        borderRadius="2xl"
        bg="whiteAlpha.700"
        backdropFilter="blur(16px)"
        border="1px solid"
        borderColor="whiteAlpha.400"
        boxShadow="xl"
        {...rest}
      >
        {children}
      </Box>
    </motion.div>
  );
}
