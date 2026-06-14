import { h, render, Component } from 'preact';
import { useState, useEffect, useRef } from 'preact/hooks';
import Dashboard from './dashboard.jsx';
import ChatInterface from './chat_interface.jsx';
import { Router, Route, Link, useLocation, useRoute, Switch } from 'wouter';
import { BlogPage } from './blog.jsx';
import { Analytics } from "@vercel/analytics/react";
import { marked } from 'marked';
import DOMPurify from 'dompurify';

const LandscapeHero = () => (
  <div class="landscape-hero">
    <svg viewBox="0 0 1440 900" preserveAspectRatio="xMidYMid slice" fill="none" xmlns="http://www.w3.org/2000/svg">
      {/* Floating particles */}
      {[180, 400, 600, 900, 1100, 1300].map((x, i) => (
        <circle key={i} cx={x} cy={250 + i * 40} r={2.5} fill="#FBBF24" opacity="0.3">
          <animate attributeName="cy" values={`${250 + i * 40};${240 + i * 40};${250 + i * 40}`} dur={`${3 + i}s`} repeatCount="indefinite" />
          <animate attributeName="opacity" values="0.2;0.5;0.2" dur={`${4 + i}s`} repeatCount="indefinite" />
        </circle>
      ))}
    </svg>
  </div>
);

const LeafIcon = ({ size = 24 }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
    <path d="M11 20A7 7 0 0 1 9.8 6.9C15.5 4.9 17 3.5 19 2c1 2 2 4.5 2 8 0 5.5-4.78 10-10 10Z" />
    <path d="M2 21c0-3 1.85-5.36 5.08-6C9.5 14.52 12 13 13 12" />
  </svg>
);

const ZapIcon = ({ size = 24 }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
    <polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2" />
  </svg>
);

const CloudIcon = ({ size = 24 }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
    <path d="M17.5 19H9a7 7 0 1 1 6.71-9h1.79a4.5 4.5 0 1 1 0 9Z" />
  </svg>
);

const API_BASE_URL = import.meta.env.VITE_BACKEND_URL || "https://rta-tb0k.onrender.com";

const Navbar = () => {
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
};

const TerminalDemo = () => {
  const terminalRef = useRef(null);
  const infoRef = useRef(null);

  useEffect(() => {
    let isRunning = true;
    let timeoutIds = [];

    const sleep = (ms) => new Promise((r) => {
      const id = setTimeout(r, ms);
      timeoutIds.push(id);
    });

    const scrollToBottom = () => {
      if (terminalRef.current) {
        terminalRef.current.scrollTop = terminalRef.current.scrollHeight;
      }
    };

    const el = (tag, styleStr, content) => {
      const e = document.createElement(tag);
      if (styleStr) e.style.cssText = styleStr;
      if (content) {
        if (typeof content === 'string') e.textContent = content;
        else e.appendChild(content);
      }
      return e;
    };

    const addInfoLine = async (label, value, delay = 0) => {
      await sleep(delay);
      if (!isRunning || !infoRef.current) return;
      const line = el('div', "display: flex; justify-content: space-between; margin-bottom: 0.2rem; font-size: 9px; line-height: 1.5;");
      line.appendChild(el('span', "color: var(--text-muted);", label));
      line.appendChild(el('span', "color: var(--primary); font-weight: 500;", value));
      infoRef.current.appendChild(line);
    };

    const typeCmd = async (text, speed = 30) => {
      if (!isRunning || !terminalRef.current) return;
      const span = el('span', "color: var(--primary);");
      terminalRef.current.lastChild.appendChild(span);
      for (let char of text) {
        if (!isRunning) return;
        span.textContent += char;
        scrollToBottom();
        await sleep(speed);
      }
    };

    const showLoader = async (duration = 1800) => {
      if (!isRunning || !terminalRef.current) return;
      const frames = ['-', '\\', '|', '/'];
      let frame = 0;
      const start = Date.now();
      const loaderSpan = el('span', "color: var(--primary); font-size: 10px;");
      terminalRef.current.appendChild(loaderSpan);
      return new Promise((r) => {
        const iv = setInterval(() => {
          if (!isRunning) { clearInterval(iv); r(); return; }
          loaderSpan.textContent = frames[frame % frames.length] + ' Processing...';
          frame++;
          scrollToBottom();
          if (Date.now() - start > duration) {
            clearInterval(iv);
            loaderSpan.remove();
            r();
          }
        }, 80);
        timeoutIds.push(iv);
      });
    };

    const addTool = async (name) => {
      await sleep(400);
      if (!isRunning || !terminalRef.current) return;
      const line = el('div', "color: var(--text-secondary); margin-bottom: 0.3rem; font-size: 10px; display: flex; align-items: center; gap: 0.5rem;");
      line.appendChild(el('span', "color: var(--primary); font-weight: bold;", "[+]"));
      line.appendChild(el('span', "", name));
      terminalRef.current.appendChild(line);
      scrollToBottom();
      await sleep(500);
      if (!isRunning || !terminalRef.current) return;
      terminalRef.current.appendChild(el('div', "color: var(--text-muted); margin-bottom: 0.3rem; font-size: 9px; margin-left: 1.5rem;", "[done]"));
      scrollToBottom();
    };

    const agentMsg = async (msg) => {
      await sleep(600);
      if (!isRunning || !terminalRef.current) return;
      const line = el('div', "color: var(--text-primary); margin-top: 0.4rem; padding: 0.5rem; background: var(--accent-glow); border-left: 2px solid var(--primary); font-size: 10px; line-height: 1.5;");
      terminalRef.current.appendChild(line);
      for (let char of msg) {
        if (!isRunning) return;
        line.textContent += char;
        scrollToBottom();
        await sleep(15);
      }
    };

    const runDemo = async () => {
      if (!isRunning || !infoRef.current || !terminalRef.current) return;
      infoRef.current.innerHTML = '';
      terminalRef.current.innerHTML = '';

      const scenarios = [
        {
          command: 'create a todo app with nextjs and stripe',
          tools: ['read_directory', 'create_file', 'install_package', 'configure_env', 'run_build'],
          message: 'Done! Created a Next.js todo app with Stripe integration and auth setup.'
        },
        {
          command: 'train a simple neural network in c++ for mnist',
          tools: ['create_file', 'configure_compiler', 'optimize_weights', 'run_simulation'],
          message: 'Training complete. Accuracy: 98.4%. Weights saved to model.bin.'
        },
        {
          command: 'generate the rta landing page with vanjs',
          tools: ['analyze_branding', 'scaffold_project', 'generate_components', 'apply_styling'],
          message: 'Website generated! High-performance landing page with terminal animations ready.'
        }
      ];

      const scenario = scenarios[Math.floor(Math.random() * scenarios.length)];

      await addInfoLine('Version', 'v0.6.0', 0);
      await addInfoLine('User', 'test@example.com', 100);
      await addInfoLine('Provider', 'rta', 100);
      await addInfoLine('Model', 'auto', 100);
      await addInfoLine('RAM', '42.5 MB', 100);

      await sleep(400);
      if (!isRunning || !terminalRef.current) return;

      const prompt = el('div', "color: var(--primary); margin-bottom: 0.3rem; font-size: 10px; margin-top: 0.6rem;", "rta >");
      terminalRef.current.appendChild(prompt);
      await typeCmd(scenario.command, 40);
      await showLoader(2000);

      for (const tool of scenario.tools) {
        await addTool(tool);
      }

      await agentMsg(scenario.message);
      await sleep(4000);
      if (isRunning) runDemo();
    };

    runDemo();

    return () => {
      isRunning = false;
      timeoutIds.forEach(id => clearTimeout(id));
    };
  }, []);

  return (
    <div class="hero-visual">
      <div class="terminal-header">
        <div class="terminal-dot"></div>
        <div class="terminal-dot"></div>
        <div class="terminal-dot"></div>
        <span style="font-size: 9px; color: var(--text-muted); margin-left: auto; font-family: var(--font-mono);">rta-terminal-demo</span>
      </div>
      <div style="display: flex; flex-direction: column; height: 100%; padding: var(--space-s); overflow: hidden; gap: 0.8rem;">
        <div class="terminal-info-grid">
          <pre class="terminal-ascii">{` _  .-')   .-') _      ('-.     
( \\( -O ) (  OO) )    ( OO ).-. 
 ,------.  /     '._   / . --. / 
|   /\\'. |'--...__)  | \\-.  \\  
|  /  | |'--.  .--'.-'-'  |  | 
|  |_.' |   |  |    \\| |_.'  | 
|  .  '.'   |  |     |  .-.  | 
|  |\\  \\    |  |     |  | |  | 
 \\'--' '--'   \\'--'     \\'--' \\'--'`}</pre>
          <div ref={infoRef} class="terminal-info-lines"></div>
        </div>
        <div ref={terminalRef} class="terminal-scroll"></div>
      </div>
    </div>
  );
};

const Hero = () => (
  <section class="hero">
    <LandscapeHero />
    <div class="container" style="width:100%;">
      <div class="hero-grid">
        <div class="hero-content">
          <h1>Code <span class="highlight">anywhere</span>.</h1>
          <p>Your AI coding workspace in your pocket. Build, preview, and iterate on any device — no powerful machine required.</p>
          <div class="hero-actions">
            <Link href="/chat" class="btn btn-primary">Try AI Chat</Link>
            <Link href="/auth" class="btn btn-secondary">Start building</Link>
            <Link href="/releases" class="btn btn-ghost">Download app</Link>
          </div>
        </div>
        <TerminalDemo />
      </div>
    </div>
  </section>
);

const FeaturesSection = () => {
  const features = [
    { icon: CloudIcon, title: "Freedom to roam", desc: "Code from a hillside or a cafe. Your entire dev environment lives in the cloud, ready when you are." },
    { icon: ZapIcon, title: "Your AI partner", desc: "Describe your idea in plain language and watch it become real code in minutes. No boilerplate, just results." },
    { icon: LeafIcon, title: "Seamless transition", desc: "Start on your phone, finish on your laptop. Perfect sync across all your devices, zero friction." }
  ];

  return (
    <section class="features container">
      <div class="section-header">
        <h2>Mobility</h2>
        <p>Unbound creativity for modern makers.</p>
      </div>
      <div class="features-grid">
        {features.map((f, i) => {
          const Icon = f.icon;
          return (
            <div class="feature-card" key={i}>
              <div class="feature-icon">
                <Icon size={22} />
              </div>
              <h3>{f.title}</h3>
              <p>{f.desc}</p>
            </div>
          );
        })}
      </div>
    </section>
  );
};

const PricingPage = () => {
  const [currency, setCurrency] = useState('USD');
  const priceMap = {
    INR: { starter: "₹0", basic: "₹75", pro: "₹299" },
    USD: { starter: "$0", basic: "$1.49", pro: "$4.49" }
  };

  const tiers = [
    { name: "Starter", price: priceMap[currency].starter, features: ["10 Daily AI Calls", "Standard Support"] },
    { name: "Basic", price: priceMap[currency].basic, featured: true, features: ["50 Daily AI Calls", "Advanced CLI Tools", "Mobile App Access"] },
    { name: "Pro", price: priceMap[currency].pro, features: ["100 Daily AI Calls", "24/7 Priority Support"] }
  ];

  return (
    <div class="container" style="padding-top: clamp(100px, 15vh, 140px); padding-bottom: 80px;">
      <div class="section-header">
        <h2>Pricing</h2>
        <p>Simple, transparent pricing for every maker.</p>
      </div>
      <div style="display: flex; justify-content: center; gap: 0.75rem; margin-bottom: 3rem; flex-wrap: wrap;">
        <button class={`btn ${currency === 'USD' ? 'btn-primary' : ''}`} onClick={() => setCurrency('USD')}>USD</button>
        <button class={`btn ${currency === 'INR' ? 'btn-primary' : ''}`} onClick={() => setCurrency('INR')}>INR</button>
      </div>

      <div style="max-width: 600px; margin: 0 auto 4rem auto; padding: 1.25rem; background: var(--secondary-soft); border: 1.5px solid var(--secondary); border-radius: var(--radius-md); text-align: center;">
        <p style="font-size: 0.85rem; color: var(--text-primary); margin: 0; line-height: 1.6; font-weight: 500;">
          Payment systems are in sandbox mode. Select a plan to join the priority queue.
        </p>
      </div>

      <div class="pricing-grid">
        {tiers.map(t => (
          <div class={`pricing-card ${t.featured ? 'featured' : ''}`} key={t.name}>
            {t.featured && <span class="pricing-badge">Recommended</span>}
            <div class="pricing-tier">{t.name}</div>
            <div class="pricing-price">{t.price}<span> /month</span></div>
            <ul class="pricing-features">
              {t.features.map(f => <li key={f}>{f}</li>)}
            </ul>
            <button class={t.featured ? 'btn btn-primary' : 'btn'} style={t.featured ? '' : 'border-color: var(--primary); color: var(--primary);'}>
              {t.price === "$0" || t.price === "₹0" ? "Get started" : "Select plan"}
            </button>
          </div>
        ))}
      </div>
    </div>
  );
};

const StatusPage = () => {
  useEffect(() => {
    window.location.href = "https://stats.uptimerobot.com/S5Qwww7Jtp";
  }, []);
  return null;
};

const AuthPage = () => {
  const [isLogin, setIsLogin] = useState(true);
  const [isLoading, setIsLoading] = useState(false);
  const [authError, setAuthError] = useState("");
  const captchaRef = useRef(null);

  useEffect(() => {
    if (captchaRef.current && window.hcaptcha) {
      try { window.hcaptcha.render(captchaRef.current); } catch (e) { }
    }
  }, [isLogin]);

  const handleAuth = async (e) => {
    e.preventDefault();
    setAuthError("");
    setIsLoading(true);
    const formData = new FormData(e.target);
    const data = Object.fromEntries(formData.entries());
    const captchaToken = window.hcaptcha ? window.hcaptcha.getResponse() : "test_token";
    if (!captchaToken && import.meta.env.PROD) {
      setAuthError("Please complete the captcha.");
      setIsLoading(false);
      return;
    }
    data.captcha_token = captchaToken;
    try {
      const endpoint = isLogin ? "/v1/auth/login" : "/v1/auth/signup";
      const res = await fetch(`${API_BASE_URL}${endpoint}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(data)
      });
      const result = await res.json();
      if (!res.ok) throw new Error(result.detail || "Authentication failed");
      if (!isLogin) {
        setIsLogin(true);
        setAuthError("Signup successful! Please log in.");
      } else {
        localStorage.setItem("rta_user", JSON.stringify(result));
        window.location.href = "/dashboard";
      }
    } catch (err) {
      setAuthError(err.message);
    } finally {
      setIsLoading(false);
      if (window.hcaptcha) window.hcaptcha.reset();
    }
  };

  return (
    <div class="container" style="padding-top: clamp(100px, 15vh, 140px); padding-bottom: 80px;">
      <div class="auth-box">
        <h2 style="margin-bottom: 2rem; text-align: center; font-size: 1.5rem;">{isLogin ? "Welcome back" : "Create account"}</h2>

        <div style="background: var(--primary-light); border: 1px solid var(--primary); border-radius: var(--radius-sm); padding: 12px 16px; margin-bottom: 24px;">
          <p style="font-size: 0.85rem; color: var(--primary); margin: 0; line-height: 1.5; font-weight: 500;">
            GitHub authentication is recommended for CLI integration.
          </p>
        </div>

        {authError && <div style="color: var(--red); margin-bottom: 1rem; font-size: 14px; padding: 10px; border: 1px solid var(--red); border-radius: var(--radius-sm); background: var(--red-soft);">{authError}</div>}

        <button class="btn" style="width: 100%; margin-bottom: 1.5rem;" onClick={() => window.location.href = `${API_BASE_URL}/v1/auth/github`}>
          {isLogin ? "Continue with GitHub" : "Sign up with GitHub"}
        </button>

        {isLogin && (
          <>
            <div style="display: flex; align-items: center; gap: 1rem; margin-bottom: 1.5rem; opacity: 0.4;">
              <div style="flex: 1; height: 1px; background: var(--border);"></div>
              <span style="font-size: 0.75rem; color: var(--text-muted);">or</span>
              <div style="flex: 1; height: 1px; background: var(--border);"></div>
            </div>

            <form class="auth-form" onSubmit={handleAuth}>
              <input type="email" name="email" class="auth-input" placeholder="Email" required />
              <input type="password" name="password" class="auth-input" placeholder="Password" required />
              <div ref={captchaRef} class="h-captcha" data-sitekey="51b06ce2-0f58-4148-8fec-b2944c54e718" style="margin-bottom: 1rem;"></div>
              <button type="submit" class="btn btn-primary" style="width: 100%;" disabled={isLoading}>
                {isLoading ? "Processing..." : "Login"}
              </button>
            </form>
          </>
        )}

        <div style="margin-top: 2rem; text-align: center;">
          <a href="#" class="nav-link" onClick={e => { e.preventDefault(); setIsLogin(!isLogin); setAuthError(""); }}>
            {isLogin ? "No account? Sign up" : "Have an account? Login"}
          </a>
        </div>
      </div>
    </div>
  );
};

const LegalPage = () => (
  <div class="container" style="padding-top: clamp(100px, 15vh, 140px); padding-bottom: 80px; max-width: 800px;">
    <h2 style="margin-bottom: 2rem;">Terms of Service</h2>
    <div style="color: var(--text-secondary); font-size: 1.05rem; line-height: 1.8;">
      <p style="margin-bottom: 2rem;">By accessing Rta, you agree to these terms. Read carefully.</p>
      
      <h3 style="color: var(--text-primary); margin-bottom: 1rem; margin-top: 2rem;">1. Account Usage</h3>
      <p style="margin-bottom: 1rem;">Users must provide accurate info. One person per account. Sharing credentials is prohibited. We reserve right to terminate access for any violation.</p>

      <h3 style="color: var(--text-primary); margin-bottom: 1rem; margin-top: 2rem;">2. AI & Code Generation</h3>
      <p style="margin-bottom: 1rem;">Rta provides AI-assisted code. We do not guarantee accuracy or safety of generated code. Review all output before execution. User assumes all risk for code deployed via Rta.</p>

      <h3 style="color: var(--text-primary); margin-bottom: 1rem; margin-top: 2rem;">3. Prohibited Conduct</h3>
      <p style="margin-bottom: 1rem;">Do not use Rta for: malware creation, illegal hacking, harassment, or bypassing system limits. Do not attempt to reverse engineer the CLI or backend infrastructure.</p>

      <h3 style="color: var(--text-primary); margin-bottom: 1rem; margin-top: 2rem;">4. Intellectual Property</h3>
      <p style="margin-bottom: 1rem;">You own code you write. We own the Rta platform, branding, and proprietary algorithms. License to use Rta is non-exclusive and revocable.</p>

      <h3 style="color: var(--text-primary); margin-bottom: 1rem; margin-top: 2rem;">5. Limitation of Liability</h3>
      <p style="margin-bottom: 1rem;">Rta is provided "as is". We are not liable for data loss, system failure, or financial damages resulting from use of our tools.</p>
    </div>
  </div>
);

const PrivacyPage = () => {
  const [content, setContent] = useState("");

  useEffect(() => {
    fetch('/privacy.md')
      .then(res => res.text())
      .then(text => setContent(marked.parse(text)))
      .catch(() => setContent("Error loading privacy policy."));
  }, []);

  return (
    <div class="container" style="padding-top: clamp(100px, 15vh, 140px); padding-bottom: 80px; max-width: 800px;">
      <div class="markdown-body" dangerouslySetInnerHTML={{ __html: DOMPurify.sanitize(content) }} />
    </div>
  );
};

const RoadmapPage = () => (
  <div class="container" style="padding-top: clamp(100px, 15vh, 140px); padding-bottom: 80px;">
    <div class="section-header">
      <h2>Roadmap</h2>
      <p>What's coming next.</p>
    </div>
    <div class="features-grid">
      <div class="feature-card">
        <div class="feature-icon" style="font-size: 0.7rem; background: var(--accent-glow); color: var(--primary);">Phase 01</div>
        <h3>Core CLI v1.0</h3>
        <p>Auth, Telemetry, Project Indexing</p>
      </div>
      <div class="feature-card">
        <div class="feature-icon" style="font-size: 0.7rem; background: var(--secondary-soft); color: #B45309;">Phase 02</div>
        <h3>Public Beta</h3>
        <p>Context Sync, AI Refactor Engine</p>
      </div>
      <div class="feature-card">
        <div class="feature-icon" style="font-size: 0.7rem; background: var(--primary-light); color: var(--primary);">Phase 03</div>
        <h3>Mobile App</h3>
        <p>Android Chat Interface, Account Sync</p>
      </div>
    </div>
  </div>
);

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

const ReleasesPage = () => {
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

const DocsPage = () => {
  const sections = [
    {
      id: "installation",
      title: "Installation",
      content: `
### Get the Binary
Rta is distributed as a standalone binary. No Python or dependencies required to run the core.

- **Linux/macOS**: [Download Binary](/rta)
- **Windows**: [Download Binary](/rta.exe)

### Linux/macOS Setup
Once downloaded, move the binary to your path and make it executable:
\`\`\`bash
chmod +x rta
sudo mv rta /usr/local/bin/
\`\`\`

### Windows Setup
1. Download \`rta.exe\`.
2. Move it to a folder (e.g., \`C:\\bin\`).
3. Add that folder to your **System PATH** environment variable.
4. Open a new Terminal (PowerShell or CMD).

### Authenticate
Run the login command to link your account and get your API key:
\`\`\`bash
rta login
\`\`\`
`
    },
    {
      id: "usage",
      title: "Basic Usage",
      content: `
### Start a Chat
Navigate to your project directory and initialize a session:
\`\`\`bash
rta chat
\`\`\`

### Key Commands
- \`/review\`: Toggle **Review Mode** (read-only safety).
- \`/skill list\`: View available prompt-based skills.
- \`/exit\`: End the session.

### Semantic Search
Rta uses a lean BM25 index to "know" your codebase. It indexes your files locally (no heavy ML models) to provide architectural awareness.
`
    },
    {
      id: "mcp",
      title: "The Constellation (MCP)",
      content: `
### What is MCP?
The Model Context Protocol (MCP) allows Rta to connect to external tools like GitHub, Google Search, or local databases.

### Configuration
Edit your configuration at \`~/.rta/mcp_config.json\`. Rta generates a template on first run.

### GitHub Integration
Add your Personal Access Token to the config to enable repository management, issue tracking, and PR reviews.

\`\`\`json
{
  "mcpServers": {
    "github": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-github"],
      "env": { "GITHUB_PERSONAL_ACCESS_TOKEN": "..." }
    }
  }
}
\`\`\`
`
    }
  ];

  return (
    <div class="container" style="padding-top: clamp(100px, 15vh, 140px); padding-bottom: 80px;">
      <div class="docs-layout">
        <aside class="docs-sidebar">
          <h4 style="margin-bottom: 2rem; color: var(--text-muted); font-size: 0.8rem; text-transform: uppercase; letter-spacing: 0.05em;">Index</h4>
          <nav style="display: flex; flex-direction: column; gap: 1rem;">
            {sections.map(s => (
              <a href={`#${s.id}`} class="nav-link" style="font-size: 0.85rem;" key={s.id}>{s.title}</a>
            ))}
          </nav>
        </aside>

        <div style="flex: 1; max-width: 700px; width: 100%;">
          <div class="section-header" style="text-align: left; margin-bottom: 4rem;">
            <h2>Documentation</h2>
            <p>System Operation Manual v0.6.0</p>
          </div>

          {sections.map(s => (
            <div id={s.id} style="margin-bottom: 6rem;" key={s.id}>
              <h3 style="font-size: clamp(1.4rem, 4vw, 1.8rem); margin-bottom: 2rem; border-bottom: 1px solid var(--border); padding-bottom: 1rem;">
                {s.title}
              </h3>
              <div class="markdown-body" style="font-size: 1rem; line-height: 1.8; color: var(--text-secondary);">
                <div dangerouslySetInnerHTML={{ __html: DOMPurify.sanitize(marked.parse(s.content)) }} />
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

const API_BASE = import.meta.env.VITE_BACKEND_URL || "https://rta-tb0k.onrender.com";

const ApiPage = () => {
  const [copied, setCopied] = useState(null);

  const copy = (text, id) => {
    navigator.clipboard.writeText(text);
    setCopied(id);
    setTimeout(() => setCopied(null), 2000);
  };

  const CodeBlock = ({ code, id }) => (
    <div style={{ position: 'relative', marginBottom: '1.5rem' }}>
      <button
        onClick={() => copy(code, id)}
        style={{
          position: 'absolute', top: '8px', right: '8px',
          background: 'var(--primary)', color: '#fff', border: 'none',
          padding: '4px 10px', borderRadius: 'var(--radius-sm)', cursor: 'pointer',
          fontSize: '11px', fontFamily: 'var(--font-mono)', zIndex: 1,
        }}
      >
        {copied === id ? 'Copied' : 'Copy'}
      </button>
      <pre style={{
        background: 'var(--bg-deep)', padding: '1.25rem',
        border: '1px solid var(--border)', borderRadius: 'var(--radius-md)',
        overflow: 'auto', fontSize: '13px', lineHeight: 1.6,
        fontFamily: 'var(--font-mono)', color: 'var(--text-secondary)',
      }}>
        <code>{code}</code>
      </pre>
    </div>
  );

  const Endpoint = ({ method, path, desc, children }) => (
    <div style={{ marginBottom: '4rem' }} id={path.replace(/[\/\s]/g, '-').slice(1)}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '0.5rem' }}>
        <span style={{
          background: method === 'GET' ? 'rgba(16, 185, 129, 0.15)' : 'var(--primary-light)',
          color: method === 'GET' ? '#10B981' : 'var(--primary)',
          padding: '3px 10px', borderRadius: 'var(--radius-sm)', fontSize: '11px',
          fontFamily: 'var(--font-mono)', fontWeight: 'bold', letterSpacing: '0.05em',
        }}>
          {method}
        </span>
        <code style={{ fontFamily: 'var(--font-mono)', fontSize: '15px', color: 'var(--text-primary)', fontWeight: 600 }}>
          {path}
        </code>
      </div>
      <p style={{ color: 'var(--text-secondary)', marginBottom: '1.5rem', fontSize: '15px' }}>{desc}</p>
      {children}
    </div>
  );

  return (
    <div class="container" style={{ paddingTop: 'clamp(100px, 15vh, 140px)', paddingBottom: '80px', maxWidth: '900px' }}>
      <div class="section-header" style={{ marginBottom: '3rem' }}>
        <h2>API</h2>
        <p>Build with Rta.</p>
      </div>

      <div style={{ marginBottom: '4rem' }}>
        <div style={{
          background: 'var(--primary-light)', border: '1px solid var(--primary)',
          borderRadius: 'var(--radius-md)', padding: '1.25rem', marginBottom: '2rem',
        }}>
          <p style={{ fontSize: '0.85rem', color: 'var(--primary)', margin: 0, fontWeight: '600', marginBottom: '0.5rem' }}>
            Base URL
          </p>
          <code style={{ fontFamily: 'var(--font-mono)', fontSize: '15px', color: 'var(--text-primary)' }}>
            {API_BASE}
          </code>
        </div>

        <h3 style={{ fontSize: '1.3rem', marginBottom: '1rem' }}>Authentication</h3>
        <p style={{ color: 'var(--text-secondary)', marginBottom: '1rem', lineHeight: 1.7 }}>
          All requests require an API key passed via the <code style={{ fontFamily: 'var(--font-mono)', background: 'var(--bg-elevated)', padding: '2px 6px', borderRadius: 'var(--radius-sm)' }}>X-API-KEY</code> header.
          Generate your key from the <Link href="/dashboard" style={{ color: 'var(--primary)', textDecoration: 'underline' }}>Dashboard</Link>.
        </p>
        <CodeBlock id="auth-header" code={`curl -H "X-API-KEY: your_api_key_here" ${API_BASE}/v1/chat`} />
      </div>

      <Endpoint method="POST" path="/v1/chat" desc="Send a chat message. Supports streaming (SSE) and non-streaming responses. OpenAI-compatible format available.">
        <h4 style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginBottom: '0.75rem', letterSpacing: '0.05em', textTransform: 'uppercase' }}>Request Body</h4>
        <CodeBlock id="chat-request" code={`{
  "model": "rta-auto",
  "messages": [
    { "role": "user", "content": "Write a hello world in Python" }
  ],
  "stream": false,
  "format": "openai",
  "max_tokens": 2000
}`} />

        <h4 style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginBottom: '0.75rem', letterSpacing: '0.05em', textTransform: 'uppercase' }}>Parameters</h4>
        <div style={{ overflowX: 'auto', marginBottom: '1.5rem' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '14px' }}>
            <thead>
              <tr style={{ borderBottom: '1px solid var(--border)' }}>
                <th style={{ textAlign: 'left', padding: '8px 12px', color: 'var(--text-muted)', fontWeight: 500 }}>Parameter</th>
                <th style={{ textAlign: 'left', padding: '8px 12px', color: 'var(--text-muted)', fontWeight: 500 }}>Type</th>
                <th style={{ textAlign: 'left', padding: '8px 12px', color: 'var(--text-muted)', fontWeight: 500 }}>Description</th>
              </tr>
            </thead>
            <tbody style={{ color: 'var(--text-secondary)' }}>
              <tr style={{ borderBottom: '1px solid var(--border-light)' }}>
                <td style={{ padding: '8px 12px' }}><code>model</code></td>
                <td style={{ padding: '8px 12px' }}>string</td>
                <td style={{ padding: '8px 12px' }}><code>rta-auto</code> for auto-routing, or specific model name</td>
              </tr>
              <tr style={{ borderBottom: '1px solid var(--border-light)' }}>
                <td style={{ padding: '8px 12px' }}><code>messages</code></td>
                <td style={{ padding: '8px 12px' }}>array</td>
                <td style={{ padding: '8px 12px' }}>Array of <code>&#123;role, content&#125;</code> objects</td>
              </tr>
              <tr style={{ borderBottom: '1px solid var(--border-light)' }}>
                <td style={{ padding: '8px 12px' }}><code>stream</code></td>
                <td style={{ padding: '8px 12px' }}>boolean</td>
                <td style={{ padding: '8px 12px' }}>Enable SSE streaming. Default: <code>false</code></td>
              </tr>
              <tr style={{ borderBottom: '1px solid var(--border-light)' }}>
                <td style={{ padding: '8px 12px' }}><code>format</code></td>
                <td style={{ padding: '8px 12px' }}>string</td>
                <td style={{ padding: '8px 12px' }}><code>"rta"</code> (default) or <code>"openai"</code> for OpenAI-compatible responses</td>
              </tr>
              <tr style={{ borderBottom: '1px solid var(--border-light)' }}>
                <td style={{ padding: '8px 12px' }}><code>max_tokens</code></td>
                <td style={{ padding: '8px 12px' }}>integer</td>
                <td style={{ padding: '8px 12px' }}>Max response tokens. Default: 2000</td>
              </tr>
              <tr>
                <td style={{ padding: '8px 12px' }}><code>tools</code></td>
                <td style={{ padding: '8px 12px' }}>array</td>
                <td style={{ padding: '8px 12px' }}>Optional tool definitions for function calling</td>
              </tr>
            </tbody>
          </table>
        </div>

        <h4 style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginBottom: '0.75rem', letterSpacing: '0.05em', textTransform: 'uppercase' }}>Example — Non-streaming (OpenAI format)</h4>
        <CodeBlock id="chat-curl" code={`curl -X POST ${API_BASE}/v1/chat \\
  -H "Content-Type: application/json" \\
  -H "X-API-KEY: your_api_key_here" \\
  -d '{
    "model": "rta-auto",
    "messages": [{"role": "user", "content": "Hello"}],
    "format": "openai"
  }'`} />

        <h4 style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginBottom: '0.75rem', letterSpacing: '0.05em', textTransform: 'uppercase' }}>Response (OpenAI format)</h4>
        <CodeBlock id="chat-response" code={`{
  "object": "chat.completion",
  "choices": [
    {
      "message": {
        "role": "assistant",
        "content": "Hello! How can I help you today?"
      },
      "finish_reason": "stop"
    }
  ],
  "usage": {
    "prompt_tokens": 12,
    "completion_tokens": 8,
    "total_tokens": 20
  },
  "model": "openai/gpt-oss-120b"
}`} />

        <h4 style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginBottom: '0.75rem', letterSpacing: '0.05em', textTransform: 'uppercase' }}>Example — Streaming</h4>
        <CodeBlock id="chat-stream-curl" code={`curl -X POST ${API_BASE}/v1/chat \\
  -H "Content-Type: application/json" \\
  -H "X-API-KEY: your_api_key_here" \\
  -d '{
    "model": "rta-auto",
    "messages": [{"role": "user", "content": "Hello"}],
    "stream": true,
    "format": "openai"
  }'`} />

        <h4 style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginBottom: '0.75rem', letterSpacing: '0.05em', textTransform: 'uppercase' }}>Stream Events (OpenAI format)</h4>
        <CodeBlock id="chat-stream-events" code={`data: {"choices":[{"delta":{"role":"assistant"},"index":0}]}

data: {"choices":[{"delta":{"content":"Hello"},"index":0}]}

data: {"choices":[{"delta":{"content":"!"},"index":0}]}

data: {"choices":[{"delta":{},"finish_reason":"stop"}],"usage":{"prompt_tokens":12,"completion_tokens":2,"total_tokens":14}}

data: [DONE]`} />

        <h4 style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginBottom: '0.75rem', letterSpacing: '0.05em', textTransform: 'uppercase' }}>JavaScript Example</h4>
        <CodeBlock id="chat-js" code={`const response = await fetch("${API_BASE}/v1/chat", {
  method: "POST",
  headers: {
    "Content-Type": "application/json",
    "X-API-KEY": "your_api_key_here"
  },
  body: JSON.stringify({
    model: "rta-auto",
    messages: [{ role: "user", content: "Hello" }],
    stream: true,
    format: "openai"
  })
});

const reader = response.body.getReader();
const decoder = new TextDecoder();

while (true) {
  const { done, value } = await reader.read();
  if (done) break;
  const chunk = decoder.decode(value);
  const lines = chunk.split("\\n").filter(l => l.startsWith("data: "));
  for (const line of lines) {
    const data = line.slice(6);
    if (data === "[DONE]") break;
    const parsed = JSON.parse(data);
    const content = parsed.choices?.[0]?.delta?.content;
    if (content) process.stdout.write(content);
  }
}`} />
      </Endpoint>

      <Endpoint method="GET" path="/v1/usage" desc="Check your current token and call usage for today and this month.">
        <h4 style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginBottom: '0.75rem', letterSpacing: '0.05em', textTransform: 'uppercase' }}>Example</h4>
        <CodeBlock id="usage-curl" code={`curl ${API_BASE}/v1/usage \\
  -H "X-API-KEY: your_api_key_here"`} />

        <h4 style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginBottom: '0.75rem', letterSpacing: '0.05em', textTransform: 'uppercase' }}>Response</h4>
        <CodeBlock id="usage-response" code={`{
  "tier": "free",
  "calls_today": 3,
  "calls_limit": 10,
  "tokens_today": 1250,
  "tokens_month": 15420,
  "tokens_limit_day": 50000
}`} />
      </Endpoint>

      <Endpoint method="GET" path="/v1/status" desc="Public service status. No authentication required.">
        <h4 style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginBottom: '0.75rem', letterSpacing: '0.05em', textTransform: 'uppercase' }}>Example</h4>
        <CodeBlock id="status-curl" code={`curl ${API_BASE}/v1/status`} />

        <h4 style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginBottom: '0.75rem', letterSpacing: '0.05em', textTransform: 'uppercase' }}>Response</h4>
        <CodeBlock id="status-response" code={`{
  "status": "operational",
  "version": "0.1.0",
  "services": {
    "database": "operational",
    "api": "operational",
    "proxy": "operational"
  }
}`} />
      </Endpoint>

      <Endpoint method="GET" path="/health" desc="Simple health check. No authentication required.">
        <CodeBlock id="health-response" code={`{
  "status": "healthy"
}`} />
      </Endpoint>

      <div style={{
        background: 'var(--primary-light)', border: '1px solid var(--primary)',
        borderRadius: 'var(--radius-md)', padding: '1.25rem', marginTop: '2rem',
      }}>
        <p style={{ fontSize: '0.85rem', color: 'var(--primary)', margin: 0, fontWeight: '600', marginBottom: '0.5rem' }}>
          Rate Limits
        </p>
        <p style={{ fontSize: '14px', color: 'var(--text-secondary)', margin: 0, lineHeight: 1.6 }}>
          Free tier: 10 calls/day. Upgrade via <Link href="/pricing" style={{ color: 'var(--primary)', textDecoration: 'underline' }}>Pricing</Link>.
          Rate limits are enforced per API key.
        </p>
      </div>
    </div>
  );
};

const AppFooter = () => (
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
          <a href="https://github.com/Raunderz/Rta" target="_blank" rel="noopener noreferrer">GitHub</a>
          <a href="https://discord.gg/ZpxUv9VyGP" target="_blank" rel="noopener noreferrer">Discord</a>
        </div>
        <div class="footer-col">
          <h4>Legal</h4>
          <Link href="/legal">Terms</Link>
          <Link href="/privacy">Privacy</Link>
        </div>
        </div>
        <div class="footer-bottom">
        <span>&copy; 2026 Rta Software. All rights reserved.</span>
        </div>
        </div>
        </footer>
        );

const Home = () => (
  <div>
    <Hero />
    <FeaturesSection />
  </div>
);

const NotFoundPage = () => (
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

const ServiceNotice = () => (
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

const CookieBanner = () => {
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

const App = () => {
  const [match] = useRoute("/chat");
  if (match) return <ChatInterface />;

  return (
    <div class="app-container">
      <Navbar />
      <main class="main-content">
        <Router>
          <Switch>
            <Route path="/" component={Home} />
            <Route path="/pricing" component={PricingPage} />
            <Route path="/roadmap" component={RoadmapPage} />
            <Route path="/status" component={StatusPage} />
            <Route path="/releases" component={ReleasesPage} />
            <Route path="/auth" component={AuthPage} />
            <Route path="/legal" component={LegalPage} />
            <Route path="/privacy" component={PrivacyPage} />
            <Route path="/blog" component={BlogPage} />
            <Route path="/blog/:slug" component={BlogPage} />
            <Route path="/docs" component={DocsPage} />
            <Route path="/api" component={ApiPage} />
            <Route path="/dashboard" component={Dashboard} />
            <Route component={NotFoundPage} />
          </Switch>
        </Router>
      </main>
      <ServiceNotice />
      <CookieBanner />
      <AppFooter />
      <Analytics />
    </div>
  );
};

render(<App />, document.body);
