import { Routes, Route } from 'react-router-dom';
import { AuthProvider } from './context/AuthContext';
import Layout from './components/Layout';
import ProtectedRoute from './components/ProtectedRoute';
import RoleProtectedRoute from './components/RoleProtectedRoute';
import DashboardLayout from './components/dashboard/DashboardLayout';

import Home from './pages/Home';
import About from './pages/About';
import Services from './pages/Services';
import Programs from './pages/Programs';
import Testimonials from './pages/Testimonials';
import Contact from './pages/Contact';
import Diagnostic from './pages/Diagnostic';
import NotFound from './pages/NotFound';

import Login from './pages/auth/Login';
import Signup from './pages/auth/Signup';
import ForgotPassword from './pages/auth/ForgotPassword';
import ResetPassword from './pages/auth/ResetPassword';
import VerifyEmail from './pages/auth/VerifyEmail';
import Profile from './pages/auth/Profile';

import AdvisorOverview from './pages/advisor/Overview';
import ClientList from './pages/advisor/ClientList';
import ClientDetail from './pages/advisor/ClientDetail';
import Analytics from './pages/advisor/Analytics';
import AdvisorSettings from './pages/advisor/Settings';

import ClientOverview from './pages/client/Overview';
import ClientReports from './pages/client/Reports';
import ClientReportDetail from './pages/client/ReportDetail';
import SessionHistory from './pages/client/SessionHistory';
import SessionTranscript from './pages/client/SessionTranscript';
import ClientProfile from './pages/client/Profile';

function App() {
  return (
    <AuthProvider>
      <Routes>
        {/* Public site + auth */}
        <Route element={<Layout />}>
          <Route index element={<Home />} />
          <Route path="about" element={<About />} />
          <Route path="services" element={<Services />} />
          <Route path="programs" element={<Programs />} />
          <Route path="testimonials" element={<Testimonials />} />
          <Route path="contact" element={<Contact />} />
          <Route path="diagnostic" element={<Diagnostic />} />

          <Route path="login" element={<Login />} />
          <Route path="signup" element={<Signup />} />
          <Route path="forgot-password" element={<ForgotPassword />} />
          <Route path="reset-password" element={<ResetPassword />} />
          <Route path="verify-email" element={<VerifyEmail />} />

          <Route
            path="profile"
            element={
              <ProtectedRoute>
                <Profile />
              </ProtectedRoute>
            }
          />

          <Route path="*" element={<NotFound />} />
        </Route>

        {/* Advisor dashboard */}
        <Route
          path="advisor"
          element={
            <RoleProtectedRoute role="advisor">
              <DashboardLayout role="advisor" />
            </RoleProtectedRoute>
          }
        >
          <Route index element={<AdvisorOverview />} />
          <Route path="clients" element={<ClientList />} />
          <Route path="clients/:id" element={<ClientDetail />} />
          <Route path="analytics" element={<Analytics />} />
          <Route path="settings" element={<AdvisorSettings />} />
        </Route>

        {/* Client dashboard */}
        <Route
          path="dashboard"
          element={
            <RoleProtectedRoute role="client">
              <DashboardLayout role="client" />
            </RoleProtectedRoute>
          }
        >
          <Route index element={<ClientOverview />} />
          <Route path="reports" element={<ClientReports />} />
          <Route path="reports/:id" element={<ClientReportDetail />} />
          <Route path="history" element={<SessionHistory />} />
          <Route path="history/:id" element={<SessionTranscript />} />
          <Route path="profile" element={<ClientProfile />} />
        </Route>
      </Routes>
    </AuthProvider>
  );
}

export default App;
