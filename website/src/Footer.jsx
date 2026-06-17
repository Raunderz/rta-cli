import { useState, useEffect } from 'preact/hooks';
import { Link } from 'wouter';

export const AppFooter = () => (
  <footer class="footer">
    <div class="container">
      <div class="footer-grid">
        <div class="footer-col">
          <Link href="/" class="logo" style="margin-bottom: 0.5rem;">
            <span class="logo-dot"></span>
            Rta
          </Link>
          <p class="footer-logo-text">Your AI coding workspace in your pocket. Build anywhere, on any device.</p>
        </div>
        <div class="footer-col">
          <h4>Platform</h4>
          <Link href="/pricing">Pricing</Link>
          <Link href="/roadmap">Roadmap</Link>
          <Link href="/status">Status</Link>
          <Link href="/releases">Releases</Link>
        </div>
        <div class="footer-col">
          <h4>Resources</h4>
          <Link href="/docs">Documentation</Link>
          <Link href="/api">API</Link>
          <Link href="/blog">Blog</Link>
          <a href="https://raunderz.github.io/rta.html" target="_blank" rel="noopener noreferrer">GitHub</a>
          <a href="https://discord.gg/ZpxUv9VyGP" target="_blank" rel="noopener noreferrer">Discord</a>
        </div>
        <div class="footer-col">
          <h4>Legal</h4>
          <Link href="/legal">Terms</Link>
          <Link href="/privacy">Privacy</Link>
        </div>
      </div>
      <div class="footer-bottom">
        <a href="https://raunderz.github.io/rta.html" target="_blank" rel="noopener noreferrer" style="color: var(--text-secondary); text-decoration: none;">Rta — By Rounders (raunderz)</a>
      </div>
    </div>
  </footer>
);

export const NotFoundPage = () => (
  <div class="container" style="padding-top: 120px; padding-bottom: 80px; min-height: 70vh; display: flex; flex-direction: column; align-items: center; justify-content: center;">
    <div class="status-board" style="max-width: 600px; width: 100%; text-align: center; padding: 4rem 2rem;">
      <div class="section-header" style="margin-bottom: 2rem;">
        <h2 style="font-size: clamp(5rem, 12vw, 7rem); margin-bottom: 0;">404</h2>
        <p>Page not found</p>
      </div>
      <div style="margin-bottom: 3rem; opacity: 0.6; display: flex; justify-content: center;">
        <svg width="80" height="80" viewBox="0 0 24 24" fill="none" stroke="var(--primary)" stroke-width="1" stroke-linecap="round" stroke-linejoin="round">
          <path d="M11 20A7 7 0 0 1 9.8 6.9C15.5 4.9 17 3.5 19 2c1 2 2 4.5 2 8 0 5.5-4.78 10-10 10Z" />
          <path d="M2 21c0-3 1.85-5.36 5.08-6C9.5 14.52 12 13 13 12" />
        </svg>
      </div>
      <div style="display: flex; gap: 1rem; justify-content: center; flex-wrap: wrap;">
        <Link href="/" class="btn btn-primary">Go home</Link>
        <Link href="/status" class="btn">Check status</Link>
      </div>
    </div>
  </div>
);

export const ServiceNotice = () => (
  <div style="position: fixed; bottom: 2rem; left: 50%; transform: translateX(-50%); width: calc(100% - 2rem); max-width: 520px; background: var(--bg-card); border: 1px solid var(--border); padding: 1.5rem; border-radius: var(--radius-lg); box-shadow: var(--shadow-lg); z-index: 9999; display: flex; flex-direction: column; gap: 0.75rem;">
    <div style="display: flex; align-items: center; gap: 0.5rem;">
      <span style="width: 8px; height: 8px; border-radius: 50%; background: var(--primary); display: inline-block;"></span>
      <span style="font-weight: 600; font-size: 0.85rem; color: var(--text-primary);">Pre-release notice</span>
    </div>
    <p style="font-size: 0.85rem; line-height: 1.6; margin: 0; color: var(--text-secondary);">
      Rta is in active development and not yet available for public use.
      Full launch coming in v1.0.0. In the meantime, feel free to explore the docs and API.
    </p>
  </div>
);

export const CookieBanner = () => {
  const [visible, setVisible] = useState(false);

  useEffect(() => {
    const consent = localStorage.getItem('rta_cookie_consent');
    if (!consent) setVisible(true);
  }, []);

  const accept = () => {
    localStorage.setItem('rta_cookie_consent', 'true');
    setVisible(false);
  };

  if (!visible) return null;

  return (
    <div style="position: fixed; bottom: 2rem; left: 50%; transform: translateX(-50%); width: calc(100% - 2rem); max-width: 500px; background: var(--bg-surface); border: 1px solid var(--border); padding: 1.5rem; border-radius: var(--radius-lg); box-shadow: var(--shadow-lg); z-index: 9999; display: flex; flex-direction: column; gap: 1rem;">
      <p style="font-size: 0.85rem; line-height: 1.6; margin: 0; color: var(--text-secondary);">
        We use essential cookies and anonymous telemetry to improve the experience.
        Read our <Link href="/privacy" style="color: var(--primary); text-decoration: underline;">Privacy Policy</Link>.
      </p>
      <button onClick={accept} class="btn btn-primary" style="width: 100%;">Got it</button>
    </div>
  );
};
