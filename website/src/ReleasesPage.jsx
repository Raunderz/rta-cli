import { useState } from 'preact/hooks';
import { Link } from 'wouter';
import { useHead } from './useHead';

const DownloadsSection = ({ os }) => {
  if (os === 'android') {
    return (
      <div style="padding: var(--space-m); text-align: center;">
        <h4 style="margin-bottom: 2rem; color: var(--text-primary); font-weight: 700;">Mobile App (Beta)</h4>
        <div style="background: #fff; padding: 1.5rem; display: inline-block; border-radius: var(--radius-lg); margin-bottom: 2rem; box-shadow: var(--shadow-md);">
          <img src="/assets/android_qr.png" alt="Android QR" style="width: 220px; height: 220px; max-width: 100%; display: block;" />
        </div>
        <div style="max-width: 500px; margin: 0 auto; padding: 1.25rem; background: var(--primary-light); border: 1px solid var(--primary); border-radius: var(--radius-md);">
          <p style="font-size: 0.85rem; color: var(--primary); line-height: 1.6; margin: 0; font-weight: 500;">
            Mobile deployment is currently limited to Chat and Telemetry. Full autonomous agent capabilities remain exclusive to CLI and Desktop.
          </p>
        </div>
      </div>
    );
  }

  if (os === 'desktop') {
    return (
      <div style="padding: var(--space-m);">
        <div class="status-header">
          <span class="mono">RTA Desktop IDE (Linux)</span>
          <a
            href="/rta-desktop-linux.tar.gz"
            download="rta-desktop-linux.tar.gz"
            class="btn btn-primary"
            style="text-decoration: none;"
          >
            Download (623 KB)
          </a>
        </div>
        <div style="padding: 1rem 0;">
          <div style="background: var(--primary-light); border: 1px solid var(--primary); border-radius: var(--radius-md); padding: 1rem; margin-bottom: 1.5rem;">
            <p style="font-size: 0.85rem; color: var(--primary); line-height: 1.6; margin: 0; font-weight: 500;">
              This is a standalone code editor based on Lite XL. AI agent features are not yet integrated — they are exclusive to the CLI.
            </p>
          </div>
          <h4 style="margin-bottom: 1rem;">Quick Install</h4>
          <pre style="background: var(--bg-deep); padding: 1.5rem; border: 1px solid var(--border); border-radius: var(--radius-md); color: var(--text-secondary); font-family: var(--font-mono); font-size: 14px; overflow-x: auto;">tar xzf rta-desktop-linux.tar.gz
sudo mv rta-desktop data /usr/local/bin/
rta-desktop</pre>
        </div>
      </div>
    );
  }

  return (
    <>
      <div class="status-header">
        <span class="mono">v1.4.2 (Stable)</span>
        <a
          href={os === 'linux' ? "/rta" : "/rta.exe"}
          download={os === 'linux' ? "rta" : "rta.exe"}
          class="btn btn-primary"
          style="text-decoration: none;"
        >
          Download for {os === 'linux' ? 'Linux' : 'Windows'} ({os === 'linux' ? '31 MB' : '22 MB'})
        </a>
      </div>
      <div style="padding: var(--space-m);">
        <h4 style="margin-bottom: 1rem;">Quick Install</h4>
        <pre style="background: var(--bg-deep); padding: 1.5rem; border: 1px solid var(--border); border-radius: var(--radius-md); color: var(--text-secondary); font-family: var(--font-mono); font-size: 14px; overflow-x: auto;">
          {os === 'linux' ? `chmod +x rta
sudo mv rta /usr/local/bin/
rta chat` : `rta.exe chat`}
        </pre>
      </div>
    </>
  );
};

export const ReleasesPage = () => {
  useHead({ title: "Releases", description: "Download Rta CLI, Desktop IDE, and Mobile App." });
  const [os, setOs] = useState('linux');

  return (
    <div class="container" style="padding-top: clamp(100px, 15vh, 140px); padding-bottom: 80px;">
      <div class="section-header">
        <h2>Releases</h2>
        <p>Download the tools.</p>
      </div>
      <div style="display: flex; justify-content: center; gap: 0.75rem; margin-bottom: 3rem; flex-wrap: wrap;">
        <button class={`btn ${os === 'linux' ? 'btn-primary' : ''}`} onClick={() => setOs('linux')}>CLI · Linux</button>
        <button class={`btn ${os === 'windows' ? 'btn-primary' : ''}`} onClick={() => setOs('windows')}>CLI · Windows</button>
        <button class={`btn ${os === 'desktop' ? 'btn-primary' : ''}`} onClick={() => setOs('desktop')}>Desktop IDE</button>
        <button class={`btn ${os === 'android' ? 'btn-primary' : ''}`} onClick={() => setOs('android')}>Android</button>
      </div>
      <div class="status-board">
        <DownloadsSection os={os} />
      </div>
    </div>
  );
};
