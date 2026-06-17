import { useState, useEffect } from 'preact/hooks';
import { Link, useLocation } from 'wouter';

export default function Navbar() {
  const [location] = useLocation();
  const [user, setUser] = useState(null);
  const [isMenuOpen, setIsMenuOpen] = useState(false);
  const isActive = (path) => location === path ? "active" : "";

  useEffect(() => {
    try {
      const saved = localStorage.getItem("rta_user");
      setUser(saved ? JSON.parse(saved) : null);
    } catch (e) {
      setUser(null);
    }
    setIsMenuOpen(false);
  }, [location]);

  return (
    <nav class="navbar">
      <div class="container nav-content">
        <Link href="/" class="logo">
          <span class="logo-dot"></span>
          Rta
        </Link>

        <button
          class={`menu-toggle ${isMenuOpen ? 'open' : ''}`}
          onClick={() => setIsMenuOpen(!isMenuOpen)}
          aria-label="Toggle menu"
        >
          <span class="hamburger"></span>
        </button>

        <div class={`nav-links ${isMenuOpen ? 'open' : ''}`}>
          <Link href="/pricing" class={`nav-link ${isActive('/pricing')}`}>Pricing</Link>
          <Link href="/roadmap" class={`nav-link ${isActive('/roadmap')}`}>Roadmap</Link>
          <Link href="/status" class={`nav-link ${isActive('/status')}`}>Status</Link>
          <Link href="/releases" class={`nav-link ${isActive('/releases')}`}>Releases</Link>
          <Link href="/docs" class={`nav-link ${isActive('/docs')}`}>Docs</Link>
          <Link href="/api" class={`nav-link ${isActive('/api')}`}>API</Link>
          <Link href={user ? "/dashboard" : "/auth"} class={`nav-link ${isActive(user ? '/dashboard' : '/auth')}`}>
            {user ? "Dashboard" : "Account"}
          </Link>
        </div>
      </div>
    </nav>
  );
}
