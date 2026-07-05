import { Box } from '@chakra-ui/react';

export function MeshBackground() {
  return (
    <Box position="fixed" inset={0} zIndex={-1} overflow="hidden">
      <Box
        position="absolute"
        inset={0}
        bgGradient="linear(to-br, purple.50, white, pink.50)"
      />
      <Box
        position="absolute"
        top={0}
        left="25%"
        w="24rem"
        h="24rem"
        bg="purple.200"
        borderRadius="full"
        filter="blur(96px)"
        opacity={0.3}
      />
      <Box
        position="absolute"
        bottom={0}
        right="25%"
        w="24rem"
        h="24rem"
        bg="pink.200"
        borderRadius="full"
        filter="blur(96px)"
        opacity={0.3}
      />
    </Box>
  );
}
