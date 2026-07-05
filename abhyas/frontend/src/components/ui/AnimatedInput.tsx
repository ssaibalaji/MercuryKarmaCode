import {
  FormControl,
  FormErrorMessage,
  FormLabel,
  Input,
  type InputProps,
} from '@chakra-ui/react';
import { forwardRef } from 'react';

interface AnimatedInputProps extends InputProps {
  label?: string;
  error?: string;
}

export const AnimatedInput = forwardRef<HTMLInputElement, AnimatedInputProps>(
  ({ label, error, ...rest }, ref) => {
    return (
      <FormControl isInvalid={Boolean(error)}>
        {label && <FormLabel>{label}</FormLabel>}
        <Input
          ref={ref}
          borderRadius="xl"
          borderWidth="2px"
          transition="all 0.15s ease"
          _focus={{ borderColor: 'brand.500', boxShadow: 'none', transform: 'scale(1.01)' }}
          {...rest}
        />
        {error && <FormErrorMessage>{error}</FormErrorMessage>}
      </FormControl>
    );
  },
);

AnimatedInput.displayName = 'AnimatedInput';
