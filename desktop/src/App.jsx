import { useState, useEffect } from 'preact/hooks';
import { LandingPage } from './pages/LandingPage.jsx';
import iconImage from './assets/icon.png';

export function App() {
  const [showSplash, setShowSplash] = useState(true);

  useEffect(() => {
    const timer = setTimeout(() => setShowSplash(false), 1500);
    return () => clearTimeout(timer);
  }, []);

  if (showSplash) {
    return (
      <div className="splash-screen">
        <div className="splash-logo">
          <img src={iconImage} alt="RTA" className="w-20 h-20" />
        </div>
        <h1 className="splash-title">RTA</h1>
        <div className="splash-loader"></div>
      </div>
    );
  }

  return <LandingPage />;
}
