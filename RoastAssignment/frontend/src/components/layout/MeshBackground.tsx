import { Box } from '@chakra-ui/react';

export function MeshBackground() {
  return (
    <Box position="fixed" inset={0} zIndex={-1} overflow="hidden">
      <Box position="absolute" inset={0} bgGradient="linear(to-br, purple.50, white, pink.50)" />
      <Box
        position="absolute"
        top={0}
        left="25%"
        w="96"
        h="96"
        bg="purple.200"
        rounded="full"
        filter="blur(64px)"
        opacity={0.3}
        animation="pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite"
      />
      <Box
        position="absolute"
        bottom={0}
        right="25%"
        w="96"
        h="96"
        bg="pink.200"
        rounded="full"
        filter="blur(64px)"
        opacity={0.3}
        animation="pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite"
      />
    </Box>
  );
}
