import { Box } from '@chakra-ui/react';
import type { ReactNode } from 'react';
import { NavBar } from './NavBar';

export function AppLayout({ children }: { children: ReactNode }) {
  return (
    <Box minH="100vh">
      <NavBar />
      {children}
    </Box>
  );
}
