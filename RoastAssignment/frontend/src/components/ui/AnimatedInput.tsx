import { chakra, Box, InputProps, Text } from '@chakra-ui/react';
import { motion } from 'framer-motion';
import { forwardRef } from 'react';

const MotionInput = chakra(motion.input);

interface AnimatedInputProps extends InputProps {
  label?: string;
  error?: string;
}

export const AnimatedInput = forwardRef<HTMLInputElement, AnimatedInputProps>(
  ({ label, error, ...props }, ref) => (
    <Box>
      {label && (
        <Text as="label" display="block" fontSize="sm" fontWeight="medium" mb={1}>
          {label}
        </Text>
      )}
      <MotionInput
        ref={ref}
        whileFocus={{ scale: 1.01 }}
        w="full"
        px={4}
        py={3}
        rounded="xl"
        border="2px solid"
        borderColor={error ? 'red.500' : 'gray.200'}
        _focus={{ borderColor: 'purple.500', outline: 'none' }}
        {...props}
      />
      {error && (
        <Text color="red.500" fontSize="sm" mt={1}>
          {error}
        </Text>
      )}
    </Box>
  )
);

AnimatedInput.displayName = 'AnimatedInput';
