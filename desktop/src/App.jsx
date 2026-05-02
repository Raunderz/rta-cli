import { useState, useEffect } from 'preact/hooks';
import { MainLayout } from './components/MainLayout.jsx';
import { LandingPage } from './pages/LandingPage.jsx';

export function App() {
  const [isLoggedIn, setIsLoggedIn] = useState(() => !!localStorage.getItem("rta_api_key"));

  useEffect(() => {
    const handleStorage = () => {
      setIsLoggedIn(!!localStorage.getItem("rta_api_key"));
    };
    window.addEventListener('storage', handleStorage);
    // Poll for changes since 'storage' only triggers from other tabs
    const interval = setInterval(handleStorage, 1000);
    return () => {
      window.removeEventListener('storage', handleStorage);
      clearInterval(interval);
    };
  }, []);

  return isLoggedIn ? <MainLayout /> : <LandingPage />;
}