import { Button, HStack, Text, type ButtonProps } from '@chakra-ui/react';
import { motion } from 'framer-motion';
import { FcGoogle } from 'react-icons/fc';
import { authService } from '../../services/authService';

export function GoogleLoginButton(props: ButtonProps) {
  const handleClick = (): void => {
    window.location.href = authService.googleLoginUrl();
  };

  return (
    <motion.div
      style={{ display: 'block', width: '100%' }}
      whileHover={{ scale: 1.02, y: -2 }}
      whileTap={{ scale: 0.98 }}
    >
      <Button
        onClick={handleClick}
        variant="outline"
        borderRadius="full"
        w="full"
        py={6}
        borderWidth="2px"
        {...props}
      >
        <HStack spacing={3} justify="center">
          <FcGoogle size={20} />
          <Text fontWeight="semibold">Continue with Google</Text>
        </HStack>
      </Button>
    </motion.div>
  );
}
