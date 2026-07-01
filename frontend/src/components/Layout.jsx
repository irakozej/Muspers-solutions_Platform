import { Outlet, useLocation } from 'react-router-dom';
import { useEffect } from 'react';
import Navbar from './Navbar';
import Footer from './Footer';
import ChatFAB from './ChatFAB';
import ScrollProgress from './animations/ScrollProgress';

export default function Layout() {
  const { pathname } = useLocation();

  // Reset scroll on route change.
  useEffect(() => {
    window.scrollTo({ top: 0, behavior: 'instant' });
  }, [pathname]);

  return (
    <div className="flex min-h-screen flex-col text-musper-ink">
      <ScrollProgress />
      <Navbar />
      <main className="flex-1">
        <Outlet />
      </main>
      <Footer />
      <ChatFAB />
    </div>
  );
}
