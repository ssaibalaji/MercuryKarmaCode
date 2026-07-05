import { useEffect, useState } from 'react';
import {
  Box,
  Center,
  Heading,
  Select,
  Spinner,
  Switch,
  Table,
  Tbody,
  Td,
  Text,
  Th,
  Thead,
  Tr,
} from '@chakra-ui/react';
import { GlassCard } from '../components/ui/GlassCard';
import { adminService } from '../services/adminService';
import type { AdminUser, UserRole } from '../types';

const ROLE_OPTIONS: UserRole[] = ['teacher', 'parent', 'admin'];

export function AdminUserListPage() {
  const [users, setUsers] = useState<AdminUser[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [pendingId, setPendingId] = useState<number | null>(null);

  const loadUsers = (): void => {
    setIsLoading(true);
    adminService
      .listUsers()
      .then(setUsers)
      .catch(() => setError('Unable to load users right now.'))
      .finally(() => setIsLoading(false));
  };

  useEffect(() => {
    loadUsers();
  }, []);

  const handleToggleActive = async (user: AdminUser): Promise<void> => {
    setPendingId(user.id);
    try {
      const updated = await adminService.updateUser(user.id, { is_active: !user.is_active });
      setUsers((prev) => prev.map((item) => (item.id === updated.id ? updated : item)));
    } catch {
      setError('Failed to update user status.');
    } finally {
      setPendingId(null);
    }
  };

  const handleRoleChange = async (user: AdminUser, role: UserRole): Promise<void> => {
    setPendingId(user.id);
    try {
      const updated = await adminService.updateUser(user.id, { role });
      setUsers((prev) => prev.map((item) => (item.id === updated.id ? updated : item)));
    } catch {
      setError('Failed to update user role.');
    } finally {
      setPendingId(null);
    }
  };

  return (
    <Box maxW="6xl" mx="auto" px={6} py={10}>
      <Heading size="xl" mb={8}>
        Users
      </Heading>
      {isLoading ? (
        <Center minH="40vh">
          <Spinner size="xl" color="brand.500" />
        </Center>
      ) : (
        <GlassCard overflowX="auto">
          {error && (
            <Text color="red.600" mb={4}>
              {error}
            </Text>
          )}
          <Table variant="simple">
            <Thead>
              <Tr>
                <Th>Name</Th>
                <Th>Email</Th>
                <Th>Role</Th>
                <Th>Active</Th>
              </Tr>
            </Thead>
            <Tbody>
              {users.map((user) => (
                <Tr key={user.id}>
                  <Td>{user.full_name}</Td>
                  <Td>{user.email}</Td>
                  <Td>
                    <Select
                      value={user.role}
                      size="sm"
                      width="auto"
                      isDisabled={pendingId === user.id}
                      onChange={(event) => handleRoleChange(user, event.target.value as UserRole)}
                    >
                      {ROLE_OPTIONS.map((role) => (
                        <option key={role} value={role}>
                          {role}
                        </option>
                      ))}
                    </Select>
                  </Td>
                  <Td>
                    <Switch
                      isChecked={user.is_active}
                      isDisabled={pendingId === user.id}
                      onChange={() => handleToggleActive(user)}
                      colorScheme="purple"
                    />
                  </Td>
                </Tr>
              ))}
            </Tbody>
          </Table>
        </GlassCard>
      )}
    </Box>
  );
}
