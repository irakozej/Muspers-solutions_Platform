import { Navigate, useLocation } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

export default function RoleProtectedRoute({ children, role }) {
  const { user, isAuthenticated, isInitializing } = useAuth();
  const location = useLocation();

  if (isInitializing) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <p className="text-sm text-musper-muted">Checking your session...</p>
      </div>
    );
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace state={{ from: location.pathname + location.search }} />;
  }

  if (role && user?.role !== role) {
    // Wrong role, bounce to whichever dashboard matches their role, or home.
    const target = user?.role === 'advisor' ? '/advisor' : user?.role === 'client' ? '/dashboard' : '/';
    return <Navigate to={target} replace />;
  }

  return children;
}
