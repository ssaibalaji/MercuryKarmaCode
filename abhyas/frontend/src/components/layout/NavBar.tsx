import {
  Box,
  Button,
  Drawer,
  DrawerBody,
  DrawerCloseButton,
  DrawerContent,
  DrawerHeader,
  DrawerOverlay,
  Flex,
  HStack,
  IconButton,
  Stack,
  Text,
  useDisclosure,
} from '@chakra-ui/react';
import { NavLink as RouterNavLink, useNavigate } from 'react-router-dom';
import type { ReactNode } from 'react';
import {
  FiCheckSquare,
  FiHome,
  FiLogOut,
  FiMenu,
  FiSettings,
  FiShield,
  FiUser,
  FiUsers,
} from 'react-icons/fi';
import { FaIndianRupeeSign } from 'react-icons/fa6';
import { useAuth } from '../../context/AuthContext';
import type { UserRole } from '../../types';

interface NavItem {
  label: string;
  to: string;
  icon: ReactNode;
}

const NAV_ITEMS_BY_ROLE: Record<UserRole, NavItem[]> = {
  teacher: [
    { label: 'Dashboard', to: '/dashboard', icon: <FiHome /> },
    { label: 'Students', to: '/students', icon: <FiUsers /> },
    { label: 'Attendance', to: '/attendance', icon: <FiCheckSquare /> },
    { label: 'Fees', to: '/fees', icon: <FaIndianRupeeSign /> },
  ],
  parent: [
    { label: 'Dashboard', to: '/dashboard', icon: <FiHome /> },
    { label: 'My Children', to: '/students', icon: <FiUsers /> },
    { label: 'Attendance', to: '/attendance/history', icon: <FiCheckSquare /> },
  ],
  admin: [
    { label: 'Admin Dashboard', to: '/admin', icon: <FiHome /> },
    { label: 'Users', to: '/admin/users', icon: <FiShield /> },
  ],
};

function NavLinkItem({ item, onClick }: { item: NavItem; onClick?: () => void }) {
  return (
    <RouterNavLink to={item.to} onClick={onClick} style={{ width: '100%' }}>
      {({ isActive }) => (
        <HStack
          spacing={3}
          px={4}
          py={2}
          borderRadius="full"
          bg={isActive ? 'whiteAlpha.700' : 'transparent'}
          color={isActive ? 'brand.600' : 'gray.600'}
          fontWeight={isActive ? 'semibold' : 'medium'}
          _hover={{ bg: 'whiteAlpha.500', color: 'brand.600' }}
          transition="all 0.15s"
        >
          <Box fontSize="lg">{item.icon}</Box>
          <Text>{item.label}</Text>
        </HStack>
      )}
    </RouterNavLink>
  );
}

export function NavBar() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const { isOpen, onOpen, onClose } = useDisclosure();

  if (!user) return null;

  const navItems = NAV_ITEMS_BY_ROLE[user.role];

  const handleLogout = async (): Promise<void> => {
    onClose();
    await logout();
    navigate('/login');
  };

  return (
    <Box
      as="nav"
      position="sticky"
      top={0}
      zIndex="sticky"
      bg="whiteAlpha.800"
      backdropFilter="blur(16px)"
      borderBottom="1px solid"
      borderColor="whiteAlpha.400"
      boxShadow="sm"
    >
      <Flex maxW="7xl" mx="auto" px={6} py={3} align="center" justify="space-between">
        <Text
          fontWeight="bold"
          fontSize="xl"
          bgGradient="linear(to-r, brand.500, accent.500)"
          bgClip="text"
          cursor="pointer"
          onClick={() => navigate('/dashboard')}
        >
          Abhyas
        </Text>

        <HStack spacing={2} display={{ base: 'none', md: 'flex' }}>
          {navItems.map((item) => (
            <NavLinkItem key={item.to} item={item} />
          ))}
        </HStack>

        <HStack spacing={2} display={{ base: 'none', md: 'flex' }}>
          <NavLinkItem item={{ label: 'Settings', to: '/settings', icon: <FiSettings /> }} />
          <NavLinkItem item={{ label: 'Profile', to: '/profile', icon: <FiUser /> }} />
          <Button
            leftIcon={<FiLogOut />}
            variant="ghost"
            colorScheme="red"
            borderRadius="full"
            onClick={handleLogout}
          >
            Logout
          </Button>
        </HStack>

        <IconButton
          aria-label="Open menu"
          icon={<FiMenu />}
          variant="ghost"
          display={{ base: 'inline-flex', md: 'none' }}
          onClick={onOpen}
        />
      </Flex>

      <Drawer isOpen={isOpen} placement="right" onClose={onClose}>
        <DrawerOverlay />
        <DrawerContent>
          <DrawerCloseButton />
          <DrawerHeader
            bgGradient="linear(to-r, brand.500, accent.500)"
            bgClip="text"
            fontWeight="bold"
          >
            Abhyas
          </DrawerHeader>
          <DrawerBody>
            <Stack spacing={1}>
              {navItems.map((item) => (
                <NavLinkItem key={item.to} item={item} onClick={onClose} />
              ))}
              <NavLinkItem
                item={{ label: 'Settings', to: '/settings', icon: <FiSettings /> }}
                onClick={onClose}
              />
              <NavLinkItem
                item={{ label: 'Profile', to: '/profile', icon: <FiUser /> }}
                onClick={onClose}
              />
              <Button
                leftIcon={<FiLogOut />}
                variant="ghost"
                colorScheme="red"
                justifyContent="flex-start"
                onClick={handleLogout}
              >
                Logout
              </Button>
            </Stack>
          </DrawerBody>
        </DrawerContent>
      </Drawer>
    </Box>
  );
}
