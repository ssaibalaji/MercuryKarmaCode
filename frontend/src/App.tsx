import { ChakraProvider } from '@chakra-ui/react';
import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom';
import { AuthProvider } from './context/AuthContext';
import { ProtectedRoute } from './components/auth/ProtectedRoute';
import { PlaceholderPage } from './pages/PlaceholderPage';
import { LoginPage } from './pages/LoginPage';
import { RegisterPage } from './pages/RegisterPage';
import { ForgotPasswordPage } from './pages/ForgotPasswordPage';
import { ProfilePage } from './pages/ProfilePage';
import { AuthCallbackPage } from './pages/AuthCallbackPage';
import { DashboardPage } from './pages/DashboardPage';
import { SettingsPage } from './pages/SettingsPage';
import { AdminDashboardPage } from './pages/AdminDashboardPage';
import { AdminUserListPage } from './pages/AdminUserListPage';
import { AttendanceCalendarPage } from './pages/AttendanceCalendarPage';
import { AttendanceMarkingPage } from './pages/AttendanceMarkingPage';
import { AttendanceHistoryPage } from './pages/AttendanceHistoryPage';
import { FeeOverviewPage } from './pages/FeeOverviewPage';
import { FeeDetailPage } from './pages/FeeDetailPage';
import { PaymentPage } from './pages/PaymentPage';
import { StudentListPage } from './pages/StudentListPage';
import { StudentCreatePage } from './pages/StudentCreatePage';
import { StudentDetailPage } from './pages/StudentDetailPage';
import { StudentEditPage } from './pages/StudentEditPage';
import theme from './lib/theme';

export default function App() {
  return (
    <ChakraProvider theme={theme}>
      <AuthProvider>
        <BrowserRouter>
          <Routes>
            <Route path="/" element={<Navigate to="/dashboard" replace />} />

            {/* Auth module routes (Module 1) */}
            <Route path="/login" element={<LoginPage />} />
            <Route path="/register" element={<RegisterPage />} />
            <Route path="/forgot-password" element={<ForgotPasswordPage />} />
            <Route path="/auth/callback" element={<AuthCallbackPage />} />
            <Route
              path="/profile"
              element={
                <ProtectedRoute>
                  <ProfilePage />
                </ProtectedRoute>
              }
            />

            {/* Dashboard module routes (Module 5) */}
            <Route
              path="/dashboard"
              element={
                <ProtectedRoute>
                  <DashboardPage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/settings"
              element={
                <ProtectedRoute>
                  <SettingsPage />
                </ProtectedRoute>
              }
            />

            {/* Students module routes (Module 2) */}
            <Route
              path="/students"
              element={
                <ProtectedRoute allowedRoles={['teacher', 'parent']}>
                  <StudentListPage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/students/new"
              element={
                <ProtectedRoute allowedRoles={['teacher']}>
                  <StudentCreatePage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/students/:id"
              element={
                <ProtectedRoute allowedRoles={['teacher', 'parent']}>
                  <StudentDetailPage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/students/:id/edit"
              element={
                <ProtectedRoute allowedRoles={['teacher']}>
                  <StudentEditPage />
                </ProtectedRoute>
              }
            />

            {/* Attendance module routes (Module 3) */}
            <Route
              path="/attendance"
              element={
                <ProtectedRoute allowedRoles={['teacher']}>
                  <AttendanceCalendarPage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/attendance/history"
              element={
                <ProtectedRoute>
                  <AttendanceHistoryPage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/attendance/:date"
              element={
                <ProtectedRoute allowedRoles={['teacher']}>
                  <AttendanceMarkingPage />
                </ProtectedRoute>
              }
            />

            {/* Fees module routes (Module 4) */}
            <Route
              path="/fees"
              element={
                <ProtectedRoute allowedRoles={['teacher']}>
                  <FeeOverviewPage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/fees/:studentId"
              element={
                <ProtectedRoute allowedRoles={['teacher', 'parent']}>
                  <FeeDetailPage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/fees/:studentId/pay"
              element={
                <ProtectedRoute allowedRoles={['parent']}>
                  <PaymentPage />
                </ProtectedRoute>
              }
            />

            {/* Admin module routes (Module 6) */}
            <Route
              path="/admin"
              element={
                <ProtectedRoute allowedRoles={['admin']}>
                  <AdminDashboardPage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/admin/users"
              element={
                <ProtectedRoute allowedRoles={['admin']}>
                  <AdminUserListPage />
                </ProtectedRoute>
              }
            />

            <Route path="*" element={<PlaceholderPage title="Not Found" />} />
          </Routes>
        </BrowserRouter>
      </AuthProvider>
    </ChakraProvider>
  );
}
