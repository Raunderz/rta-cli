import { h, render, Component } from 'preact';
import { useState, useEffect, useRef } from 'preact/hooks';
import Dashboard from './dashboard.jsx';
import { Router, Route, Link, useLocation, Switch } from 'wouter';
import { BlogPage } from './blog.jsx';
import { Analytics } from "@vercel/analytics/react";
import { marked } from 'marked';

const FlowerIcon = ({ size = 24, color = "currentColor", style = {} }) => {
  const rotations = [0, 45, 90, 135, 180, 225, 270, 315];
  const gold = "#D4A26A";
  const ember = "#E85D4A";
  const cream = "#F5F0EA";

  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 400 400"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      style={{ verticalAlign: 'middle', ...style }}
    >
      <defs>
        <filter id="warmglow" x="-20%" y="-20%" width="140%" height="140%">
          <feGaussianBlur stdDeviation="3" result="blur" />
          <feComposite in="SourceGraphic" in2="blur" operator="over" />
        </filter>

        <g id="petal-warm">
          <path
            d="M0,-20 C35,-90 85,-90 100,-10 C85,70 35,70 0,0 C-35,70 -85,70 -100,-10 C-85,-90 -35,-90 0,-20 Z"
            stroke={gold}
            strokeWidth="2"
            fill={gold}
            fillOpacity="0.04"
          />
          <g stroke={cream} strokeWidth="1.5" opacity="0.6">
            <path d="M0,-10 C0,-30 0,-55 0,-75" />
            <path d="M0,-20 C20,-35 40,-45 65,-55" />
            <path d="M0,-20 C-20,-35 -40,-45 -65,-55" />
            <path d="M0,0 C20,10 40,20 60,35" />
            <path d="M0,0 C-20,10 -40,20 -60,35" />
          </g>
        </g>
      </defs>

      <style>{`
        @keyframes warmBloom {
          0%, 100% { transform: scale(1); }
          50% { transform: scale(1.04); }
        }
        @keyframes slowSpin {
          from { transform: rotate(0deg); }
          to { transform: rotate(360deg); }
        }
        .wf-group {
          transform-origin: center;
          transform-box: fill-box;
          animation: warmBloom 5s ease-in-out infinite;
        }
        .wf-petals {
          transform-origin: center;
          transform-box: fill-box;
          animation: slowSpin 40s linear infinite;
        }
        .wf-dot {
          animation: warmTwinkle 2.5s ease-in-out infinite;
        }
        @keyframes warmTwinkle {
          0%, 100% { opacity: 0.3; transform: scale(0.8); }
          50% { opacity: 1; transform: scale(1.1); }
        }
      `}</style>

      <g transform="translate(200, 200)">
        <g fill={cream} opacity="0.15">
          {[
            { x: -120, y: -100, r: 1 }, { x: 140, y: -130, r: 1.5 },
            { x: -150, y: 120, r: 1 }, { x: 130, y: 150, r: 0.8 },
            { x: 50, y: -160, r: 1.2 }, { x: -80, y: 140, r: 1 },
            { x: 170, y: 0, r: 0.9 }, { x: -160, y: -40, r: 1.1 }
          ].map((s, i) => (
            <circle key={i} className="wf-dot" cx={s.x} cy={s.y} r={s.r} style={{ animationDelay: `${i * 0.4}s`, transformOrigin: `${s.x}px ${s.y}px` }} />
          ))}
        </g>

        <g className="wf-group">
          <g className="wf-petals">
            {rotations.map(deg => (
              <use key={deg} href="#petal-warm" transform={`rotate(${deg})`} />
            ))}
          </g>

          <g fill="none">
            <circle cx="0" cy="0" r="35" stroke={gold} strokeWidth="1" strokeDasharray="4 6" opacity="0.3"/>
            <circle cx="0" cy="0" r="28" stroke={ember} strokeWidth="2" filter="url(#warmglow)" opacity="0.8"/>
            <g fill={cream} stroke="none">
              <circle className="wf-dot" cx="-10" cy="-8" r="2" style={{ animationDelay: '0s', transformOrigin: '-10px -8px' }}/>
              <circle className="wf-dot" cx="12" cy="-6" r="2" style={{ animationDelay: '0.5s', transformOrigin: '12px -6px' }}/>
              <circle className="wf-dot" cx="-6" cy="10" r="2" style={{ animationDelay: '1s', transformOrigin: '-6px 10px' }}/>
              <circle className="wf-dot" cx="9" cy="12" r="2" style={{ animationDelay: '1.5s', transformOrigin: '9px 12px' }}/>
              <circle className="wf-dot" cx="0" cy="0" r="2.5" filter="url(#warmglow)" style={{ transformOrigin: '0 0' }}/>
            </g>
          </g>
        </g>
      </g>
    </svg>
  );
};

const API_BASE_URL = import.meta.env.VITE_BACKEND_URL || "http://localhost:8000";

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
          <FlowerIcon size={24} color="var(--accent)" style={{ marginRight: '6px' }} />
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
      line.appendChild(el('span', "color: var(--accent); font-weight: 500;", value));
      infoRef.current.appendChild(line);
    };

    const typeCmd = async (text, speed = 30) => {
      if (!isRunning || !terminalRef.current) return;
      const span = el('span', "color: var(--accent);");
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
      const loaderSpan = el('span', "color: var(--accent); font-size: 10px;");
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
      line.appendChild(el('span', "color: var(--accent); font-weight: bold;", "[+]"));
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
      const line = el('div', "color: var(--text-primary); margin-top: 0.4rem; padding: 0.5rem; background: rgba(255, 255, 255, 0.03); border-left: 2px solid var(--accent); font-size: 10px; line-height: 1.5;");
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

      await addInfoLine('Version', 'v0.4.0', 0);
      await addInfoLine('User', 'test@example.com', 100);
      await addInfoLine('Provider', 'rta', 100);
      await addInfoLine('Model', 'auto', 100);
      await addInfoLine('RAM', '42.5 MB', 100);

      await sleep(400);
      if (!isRunning || !terminalRef.current) return;

      const prompt = el('div', "color: var(--accent); margin-bottom: 0.3rem; font-size: 10px; margin-top: 0.6rem;", "rta >");
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
    <div class="container" style="width:100%;">
      <div class="hero-grid">
        <div class="hero-content">
          <h1>BUILD <br /> FASTER.</h1>
          <p>High-performance code editing and automation for modern engineering teams. Engineered for precision.</p>
          <div class="hero-actions">
            <Link href="/auth" class="btn btn-primary">Initialize Core</Link>
            <Link href="/releases" class="btn">View Logs</Link>
          </div>
        </div>
        <TerminalDemo />
      </div>
    </div>
  </section>
);

const FeaturesSection = () => {
  const features = [
    { id: "01", title: "Native Git", desc: "Pure mobile Git implementation. No proxies, just performance." },
    { id: "02", title: "AI Assisted", desc: "Context-aware code generation. Zero learning curve." },
    { id: "03", title: "Local First", desc: "Lightning fast with zero round-trips. Works entirely offline." }
  ];

  return (
    <section class="features container">
      <div class="section-header">
        <h2>Architecture</h2>
        <p class="mono">System Capabilities</p>
      </div>
      <div class="features-grid">
        {features.map(f => (
          <div class="feature-card" key={f.id}>
            <div class="feature-icon">
              <FlowerIcon size={44} color="var(--accent)" />
            </div>
            <h3>{f.title}</h3>
            <p>{f.desc}</p>
          </div>
        ))}
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
        <h2>Deployment</h2>
        <p class="mono">Allocate Resources</p>
      </div>
      <div style="display: flex; justify-content: center; gap: 1rem; margin-bottom: 3rem; flex-wrap: wrap;">
        <button class={`btn ${currency === 'USD' ? 'btn-primary' : ''}`} onClick={() => setCurrency('USD')}>USD</button>
        <button class={`btn ${currency === 'INR' ? 'btn-primary' : ''}`} onClick={() => setCurrency('INR')}>INR</button>
      </div>
      <div class="pricing-grid">
        {tiers.map(t => (
          <div class={`pricing-card ${t.featured ? 'featured' : ''}`} key={t.name}>
            <div class="pricing-tier">{t.name}</div>
            <div class="pricing-price">{t.price}<span>/mo</span></div>
            <ul class="pricing-features">
              {t.features.map(f => <li key={f}>{f}</li>)}
            </ul>
            <button class={t.featured ? 'btn btn-primary' : 'btn'}>Select Plan</button>
          </div>
        ))}
      </div>
    </div>
  );
};

const StatusPage = () => {
  const [status, setStatus] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch(`${API_BASE_URL}/v1/status`, { headers: { "ngrok-skip-browser-warning": "true" } })
      .then(res => res.json())
      .then(data => { setStatus(data); setLoading(false); })
      .catch(() => {
        setStatus({ status: "offline", services: { database: "offline", api: "offline", proxy: "offline" } });
        setLoading(false);
      });
  }, []);

  const getBadge = (val) => {
    const isOk = val === "operational" || val === "online";
    return <span class={`status-badge ${isOk ? 'operational' : ''}`}>{val?.toUpperCase() || "UNKNOWN"}</span>;
  };

  return (
    <div class="container" style="padding-top: clamp(100px, 15vh, 140px); padding-bottom: 80px;">
      <div class="section-header">
        <h2>Telemetry</h2>
        <p class="mono">System Integrity</p>
      </div>
      <div class="status-board">
        <div class="status-header">
          <span class="mono">Global Status</span>
          {loading ? <span class="mono">Checking...</span> : getBadge(status?.status)}
        </div>
        <div class="status-row">
          <span class="mono">API Endpoint</span>
          <span class="mono" style={{ color: status?.services?.api === 'operational' ? '#5BB881' : 'var(--red)' }}>
            {loading ? "..." : status?.services?.api?.toUpperCase()}
          </span>
        </div>
        <div class="status-row">
          <span class="mono">Database Cluster</span>
          <span class="mono" style={{ color: status?.services?.database === 'operational' ? '#5BB881' : 'var(--red)' }}>
            {loading ? "..." : status?.services?.database?.toUpperCase()}
          </span>
        </div>
        <div class="status-row">
          <span class="mono">Proxy Mesh</span>
          <span class="mono" style={{ color: status?.services?.proxy === 'operational' ? '#5BB881' : 'var(--red)' }}>
            {loading ? "..." : status?.services?.proxy?.toUpperCase()}
          </span>
        </div>
      </div>
      {!loading && status?.version && (
        <p class="mono" style="font-size: 10px; color: var(--text-muted); margin-top: 20px; text-align: center;">
          v{status.version} &middot; Last check: {new Date(status.timestamp * 1000).toLocaleTimeString()}
        </p>
      )}
    </div>
  );
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
        <h2 style="margin-bottom: 2rem; text-align: center; font-size: 1.8rem;">{isLogin ? "Authenticate" : "Register"}</h2>

        <div style="background: var(--accent-glow); border-left: 3px solid var(--accent); padding: 12px 16px; margin-bottom: 24px;">
          <p class="mono" style="font-size: 11px; color: var(--accent); margin: 0; line-height: 1.5; font-weight: bold;">
            [Protocol Suggestion]
          </p>
          <p class="mono" style="font-size: 11px; color: var(--text-secondary); margin: 4px 0 0 0; line-height: 1.5;">
            GitHub Authentication is recommended for optimal performance and CLI integration.
          </p>
        </div>

        {authError && <div style="color: var(--red); margin-bottom: 1rem; font-size: 14px; padding: 10px; border: 1px solid var(--red); font-family: var(--font-mono);">{authError}</div>}

        <button class="btn" style="width: 100%; margin-bottom: 1.5rem;" onClick={() => window.location.href = `${API_BASE_URL}/v1/auth/github`}>
          {isLogin ? "Continue with GitHub" : "Sign up with GitHub"}
        </button>

        {isLogin && (
          <>
            <div style="display: flex; align-items: center; gap: 1rem; margin-bottom: 1.5rem; opacity: 0.4;">
              <div style="flex: 1; height: 1px; background: var(--border);"></div>
              <span class="mono" style="font-size: 10px;">OR</span>
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
            {isLogin ? "No clearance? Register" : "Have clearance? Login"}
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
      <p style="margin-bottom: 2rem;">By accessing Rta, you agree to be bound by these terms. If you disagree with any part, you may not access our services.</p>
      <h3 style="color: var(--text-primary); margin-bottom: 1rem; margin-top: 2rem; font-family: var(--font-display);">1. Acceptance of Terms</h3>
      <p style="margin-bottom: 2rem;">Billing is processed via secure payment gateways. Subscriptions renew automatically unless cancelled. All fees are non-refundable except as required by law.</p>
    </div>
  </div>
);

const RoadmapPage = () => (
  <div class="container" style="padding-top: clamp(100px, 15vh, 140px); padding-bottom: 80px;">
    <div class="section-header">
      <h2>Roadmap</h2>
      <p class="mono">Upcoming Deployments</p>
    </div>
    <div class="features-grid">
      <div class="feature-card">
        <div class="feature-icon mono" style="font-size: 0.7rem; color: var(--accent);">Phase 01 [Active]</div>
        <h3>Core CLI v1.0</h3>
        <p>Auth, Telemetry, Project Indexing</p>
      </div>
      <div class="feature-card">
        <div class="feature-icon mono" style="font-size: 0.7rem;">Phase 02 [Soon]</div>
        <h3>Public Beta</h3>
        <p>Context Sync, AI Refactor Engine</p>
      </div>
      <div class="feature-card">
        <div class="feature-icon mono" style="font-size: 0.7rem; color: var(--text-primary);">Phase 03 [Beta]</div>
        <h3>Mobile App</h3>
        <p>Android Chat Interface, Account Sync</p>
      </div>
    </div>
  </div>
);

const ReleasesPage = () => {
  const [os, setOs] = useState('linux');

  return (
    <div class="container" style="padding-top: clamp(100px, 15vh, 140px); padding-bottom: 80px;">
      <div class="section-header">
        <h2>Releases</h2>
        <p class="mono">Download Binaries</p>
      </div>
      <div style="display: flex; justify-content: center; gap: 1rem; margin-bottom: 3rem; flex-wrap: wrap;">
        <button class={`btn ${os === 'linux' ? 'btn-primary' : ''}`} onClick={() => setOs('linux')}>Linux</button>
        <button class={`btn ${os === 'windows' ? 'btn-primary' : ''}`} onClick={() => setOs('windows')}>Windows</button>
        <button class={`btn ${os === 'android' ? 'btn-primary' : ''}`} onClick={() => setOs('android')}>Android</button>
      </div>
      <div class="status-board">
        {os === 'android' ? (
          <div style="padding: var(--space-m); text-align: center;">
            <h4 class="mono" style="margin-bottom: 2rem; color: var(--text-primary);">Mobile Protocol [Beta]</h4>
            <div style="background: #fff; padding: 1.5rem; display: inline-block; border-radius: 12px; margin-bottom: 2rem; box-shadow: 0 0 30px rgba(212, 162, 106, 0.15);">
              <img src="/assets/android_qr.png" alt="Android QR" style="width: 220px; height: 220px; max-width: 100%; display: block;" />
            </div>
            <div style="max-width: 500px; margin: 0 auto; padding: 1.5rem; background: rgba(255, 255, 255, 0.03); border: 1px solid var(--border);">
              <p class="mono" style="font-size: 11px; color: var(--accent); line-height: 1.6; margin: 0;">
                [Classified] Mobile deployment is restricted to Chat & Telemetry.
                Full Autonomous Agent capabilities (Code Execution/Refactoring) remain exclusive to CLI & Desktop nodes.
              </p>
            </div>
          </div>
        ) : (
          <>
            <div class="status-header">
              <span class="mono">v1.4.2 [Stable]</span>
              <a
                href={os === 'linux' ? "/rta" : "/rta.exe"}
                download={os === 'linux' ? "rta" : "rta.exe"}
                class="btn btn-primary"
                style="text-decoration: none;"
              >
                Download for {os === 'linux' ? 'Linux' : 'Windows'}
              </a>
            </div>
            <div style="padding: var(--space-m);">
              <h4 class="mono" style="margin-bottom: 1rem;">Quick Install</h4>
              <pre style="background: var(--bg-deep); padding: 1.5rem; border: 1px solid var(--border); color: var(--text-secondary); font-family: var(--font-mono); font-size: 14px; overflow-x: auto;">
                {os === 'linux' ? `chmod +x rta
sudo mv rta /usr/local/bin/
rta chat` : `rta.exe chat`}
              </pre>
            </div>
          </>
        )}
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
          <h4 class="mono" style="margin-bottom: 2rem; color: var(--text-muted);">Index</h4>
          <nav style="display: flex; flex-direction: column; gap: 1rem;">
            {sections.map(s => (
              <a href={`#${s.id}`} class="nav-link mono" style="font-size: 0.8rem;" key={s.id}>{s.title.toUpperCase()}</a>
            ))}
          </nav>
        </aside>

        <div style="flex: 1; max-width: 700px; width: 100%;">
          <div class="section-header" style="text-align: left; margin-bottom: 4rem;">
            <h2>Documentation</h2>
            <p class="mono">System Operation Manual v0.4.0</p>
          </div>

          {sections.map(s => (
            <div id={s.id} style="margin-bottom: 6rem;" key={s.id}>
              <h3 style="font-size: clamp(1.6rem, 4vw, 2rem); margin-bottom: 2rem; border-bottom: 1px solid var(--border); padding-bottom: 1rem; font-family: var(--font-display);">
                {s.title}
              </h3>
              <div class="markdown-body" style="font-size: 1rem; line-height: 1.8; color: var(--text-secondary);">
                <div dangerouslySetInnerHTML={{ __html: marked(s.content) }} />
              </div>
            </div>
          ))}
        </div>
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
            <FlowerIcon size={20} color="var(--accent)" style={{ marginRight: '6px' }} />
            Rta
          </Link>
          <p class="footer-logo-text">The high-performance developer toolkit for the next era of computing.</p>
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
          <a href="#">Waitlist</a>
          <Link href="/blog">Blog</Link>
        </div>
        <div class="footer-col">
          <h4>Legal</h4>
          <Link href="/legal">Terms</Link>
          <Link href="/legal">Privacy</Link>
        </div>
      </div>
      <div class="footer-bottom">
        <span>&copy; 2026 Rta Software. All rights reserved.</span>
        <div style="display: flex; gap: 2rem;">
          <a href="#">Twitter</a>
          <a href="#">GitHub</a>
        </div>
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
        <p class="mono">Resource Not Found</p>
      </div>
      <div style="margin-bottom: 3rem; opacity: 0.6; display: flex; justify-content: center;">
        <FlowerIcon size={100} color="var(--accent)" />
      </div>
      <div style="display: flex; gap: 1rem; justify-content: center; flex-wrap: wrap;">
        <Link href="/" class="btn btn-primary">Return to Base</Link>
        <Link href="/status" class="btn">Diagnostics</Link>
      </div>
    </div>
    <p class="mono" style="margin-top: 2rem; color: var(--text-muted); font-size: 0.7rem; letter-spacing: 0.2em;">
      Terminated Session: {Math.random().toString(16).slice(2, 10).toUpperCase()}
    </p>
  </div>
);

const App = () => (
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
          <Route path="/blog" component={BlogPage} />
          <Route path="/blog/:slug" component={BlogPage} />
          <Route path="/docs" component={DocsPage} />
          <Route path="/dashboard" component={Dashboard} />
          <Route component={NotFoundPage} />
        </Switch>
      </Router>
    </main>
    <AppFooter />
    <Analytics />
  </div>
);

render(<App />, document.body);
