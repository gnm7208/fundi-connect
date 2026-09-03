import { Route, Routes } from 'react-router-dom'

import { AppShell } from '@/components/layout/AppShell'
import { GuestOnly, Protected } from '@/components/RouteGuards'
import { AdminPage } from '@/features/admin/AdminPage'
import { LoginPage } from '@/features/auth/LoginPage'
import { RegisterPage } from '@/features/auth/RegisterPage'
import { BookingDetailPage } from '@/features/bookings/BookingDetailPage'
import { BookingsPage } from '@/features/bookings/BookingsPage'
import { DashboardPage } from '@/features/dashboard/DashboardPage'
import { FundiDetailPage } from '@/features/fundis/FundiDetailPage'
import { FundiSearchPage } from '@/features/fundis/FundiSearchPage'
import { FundiJobsPage } from '@/features/jobs/FundiJobsPage'
import { LandingPage } from '@/features/landing/LandingPage'
import { ConversationsPage } from '@/features/messages/ConversationsPage'
import { NotFoundPage } from '@/features/misc/NotFoundPage'
import { ProfilePage } from '@/features/profile/ProfilePage'
import { SettingsPage } from '@/features/profile/SettingsPage'
import { NewRequestPage } from '@/features/requests/NewRequestPage'
import { RequestDetailPage } from '@/features/requests/RequestDetailPage'
import { RequestsPage } from '@/features/requests/RequestsPage'
import { WalletPage } from '@/features/wallet/WalletPage'

export default function App() {
  return (
    <Routes>
      <Route element={<AppShell />}>
        <Route
          index
          element={
            <GuestOnly>
              <LandingPage />
            </GuestOnly>
          }
        />
        <Route
          path="login"
          element={
            <GuestOnly>
              <LoginPage />
            </GuestOnly>
          }
        />
        <Route
          path="register"
          element={
            <GuestOnly>
              <RegisterPage />
            </GuestOnly>
          }
        />

        <Route
          path="dashboard"
          element={
            <Protected>
              <DashboardPage />
            </Protected>
          }
        />

        <Route
          path="find"
          element={
            <Protected roles={['customer', 'admin']}>
              <FundiSearchPage />
            </Protected>
          }
        />
        <Route
          path="fundis/:fundiId"
          element={
            <Protected>
              <FundiDetailPage />
            </Protected>
          }
        />

        <Route
          path="bookings"
          element={
            <Protected>
              <BookingsPage />
            </Protected>
          }
        />
        <Route
          path="bookings/:bookingId"
          element={
            <Protected>
              <BookingDetailPage />
            </Protected>
          }
        />

        <Route
          path="jobs"
          element={
            <Protected roles={['fundi', 'admin']}>
              <FundiJobsPage />
            </Protected>
          }
        />

        <Route
          path="requests"
          element={
            <Protected>
              <RequestsPage />
            </Protected>
          }
        />
        <Route
          path="requests/new"
          element={
            <Protected roles={['customer', 'admin']}>
              <NewRequestPage />
            </Protected>
          }
        />
        <Route
          path="requests/:requestId"
          element={
            <Protected>
              <RequestDetailPage />
            </Protected>
          }
        />

        <Route
          path="wallet"
          element={
            <Protected roles={['fundi', 'admin']}>
              <WalletPage />
            </Protected>
          }
        />
        <Route
          path="messages"
          element={
            <Protected>
              <ConversationsPage />
            </Protected>
          }
        />

        <Route
          path="profile"
          element={
            <Protected>
              <ProfilePage />
            </Protected>
          }
        />
        <Route
          path="settings"
          element={
            <Protected>
              <SettingsPage />
            </Protected>
          }
        />

        <Route
          path="admin"
          element={
            <Protected roles={['admin']}>
              <AdminPage />
            </Protected>
          }
        />

        <Route path="*" element={<NotFoundPage />} />
      </Route>
    </Routes>
  )
}
