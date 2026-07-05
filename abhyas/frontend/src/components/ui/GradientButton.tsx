import { Button, type ButtonProps } from '@chakra-ui/react';
import { motion } from 'framer-motion';
import type { ReactNode } from 'react';

interface GradientButtonProps extends ButtonProps {
  children: ReactNode;
}

export function GradientButton({ children, ...rest }: GradientButtonProps) {
  return (
    <motion.div
      style={{ display: 'inline-block' }}
      whileHover={{ scale: 1.02, y: -2 }}
      whileTap={{ scale: 0.98 }}
    >
      <Button
        bgGradient="linear(to-r, brand.500, accent.500)"
        color="white"
        borderRadius="full"
        px={6}
        py={3}
        fontWeight="semibold"
        _hover={{ boxShadow: 'lg' }}
        {...rest}
      >
        {children}
      </Button>
    </motion.div>
  );
}
