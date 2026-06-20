import { chakra, ButtonProps } from '@chakra-ui/react';
import { motion } from 'framer-motion';
import { ReactNode } from 'react';

const MotionButton = chakra(motion.button);

interface GradientButtonProps extends Omit<ButtonProps, 'children'> {
  children: ReactNode;
}

export function GradientButton({ children, ...props }: GradientButtonProps) {
  return (
    <MotionButton
      whileHover={{ scale: 1.02, y: -2 }}
      whileTap={{ scale: 0.98 }}
      px={6}
      py={3}
      rounded="full"
      fontWeight="semibold"
      color="white"
      bgGradient="linear(to-r, purple.500, pink.500)"
      _hover={{ boxShadow: 'lg' }}
      {...props}
    >
      {children}
    </MotionButton>
  );
}
