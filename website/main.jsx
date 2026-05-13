import { h, render, Component } from 'preact';
import { useState, useEffect, useRef } from 'preact/hooks';
import Dashboard from './dashboard.jsx';
import { Router, Route, Link, useLocation, Switch } from 'wouter';
import { BlogPage } from './blog.jsx';
import { Analytics } from "@vercel/analytics/react";


const FlowerIcon = ({ size = 24, color = "currentColor", style = {} }) => {
  const rotations = [0, 45, 90, 135, 180, 225, 270, 315];
  
  // Galaxy Palette
  const nebulaPink = "#ff71ce";
  const nebulaBlue = "#01cdfe";
  const nebulaPurple = "#b967ff";
  const starWhite = "#fffbfe";

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
        <filter id="glow" x="-20%" y="-20%" width="140%" height="140%">
          <feGaussianBlur stdDeviation="2" result="blur" />
          <feComposite in="SourceGraphic" in2="blur" operator="over" />
        </filter>
        
        <g id="petal-shape">
          <path 
            d="M0,-20 C35,-90 85,-90 100,-10 C85,70 35,70 0,0 C-35,70 -85,70 -100,-10 C-85,-90 -35,-90 0,-20 Z" 
            stroke={nebulaPurple}
            strokeWidth="2"
            fill={nebulaPurple}
            fillOpacity="0.03"
          />
          <g stroke={nebulaBlue} strokeWidth="2">
            <path d="M0,-10 C0,-30 0,-55 0,-75" />
            <path d="M0,-20 C20,-35 40,-45 65,-55" />
            <path d="M0,-20 C-20,-35 -40,-45 -65,-55" />
            <path d="M0,0 C20,10 40,20 60,35" />
            <path d="M0,0 C-20,10 -40,20 -60,35" />
          </g>
        </g>
      </defs>

      <style>
        {`
          @keyframes bloom {
            0%, 100% { transform: scale(1); }
            50% { transform: scale(1.06); }
          }
          @keyframes slowRotate {
            from { transform: rotate(0deg); }
            to { transform: rotate(360deg); }
          }
          .flower-anim-group { 
            transform-origin: center;
            transform-box: fill-box;
            animation: bloom 4s ease-in-out infinite; 
          }
          .petals-only { 
            transform-origin: center;
            transform-box: fill-box;
            animation: slowRotate 30s linear infinite; 
          }
          .star {
            animation: twinkle 2s ease-in-out infinite;
          }
          @keyframes twinkle {
            0%, 100% { opacity: 0.3; transform: scale(0.8); }
            50% { opacity: 1; transform: scale(1.1); }
          }
        `}
      </style>

      <g transform="translate(200, 200)">
        {/* Background Stars */}
        <g fill={starWhite} opacity="0.3">
          {[
            { x: -120, y: -100, r: 1 }, { x: 140, y: -130, r: 1.5 },
            { x: -150, y: 120, r: 1 }, { x: 130, y: 150, r: 0.8 },
            { x: 50, y: -160, r: 1.2 }, { x: -80, y: 140, r: 1 },
            { x: 170, y: 0, r: 0.9 }, { x: -160, y: -40, r: 1.1 }
          ].map((s, i) => (
            <circle key={i} className="star" cx={s.x} cy={s.y} r={s.r} style={{ animationDelay: `${i * 0.4}s`, transformOrigin: `${s.x}px ${s.y}px` }} />
          ))}
        </g>

        <g className="flower-anim-group">
          <g className="petals-only">
            {rotations.map(deg => (
              <use key={deg} href="#petal-shape" transform={`rotate(${deg})`} />
            ))}
          </g>

          <g fill="none">
            <circle cx="0" cy="0" r="35" stroke={nebulaBlue} strokeWidth="1" strokeDasharray="5 5" opacity="0.5"/>
            <circle cx="0" cy="0" r="28" stroke={nebulaPink} strokeWidth="2" filter="url(#glow)"/>
            <g fill={starWhite} stroke="none">
              <circle className="star" cx="-10" cy="-8" r="2" style={{ animationDelay: '0s', transformOrigin: '-10px -8px' }}/>
              <circle className="star" cx="12" cy="-6" r="2" style={{ animationDelay: '0.5s', transformOrigin: '12px -6px' }}/>
              <circle className="star" cx="-6" cy="10" r="2" style={{ animationDelay: '1s', transformOrigin: '-6px 10px' }}/>
              <circle className="star" cx="9" cy="12" r="2" style={{ animationDelay: '1.5s', transformOrigin: '9px 12px' }}/>
              <circle className="star" cx="0" cy="0" r="2.5" filter="url(#glow)" style={{ transformOrigin: '0 0' }}/>
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
  const isActive = (path) => location === path ? "active" : "";

  useEffect(() => {
    try {
      const saved = localStorage.getItem("rta_user");
      if (saved) setUser(JSON.parse(saved));
      else setUser(null);
    } catch (e) {
      setUser(null);
    }
  }, [location]);

  return (
    <nav class="navbar">
      <div class="container nav-content">
        <Link href="/" class="logo">
          <FlowerIcon size={28} color="var(--text-main)" style={{ marginRight: '8px' }} />
          RTA
        </Link>
        <div class="nav-links">
          <Link href="/pricing" class={`nav-link ${isActive('/pricing')}`}>Pricing</Link>
          <Link href="/roadmap" class={`nav-link ${isActive('/roadmap')}`}>Roadmap</Link>
          <Link href="/status" class={`nav-link ${isActive('/status')}`}>Status</Link>
          <Link href="/releases" class={`nav-link ${isActive('/releases')}`}>Releases</Link>
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

    const createElement = (tag, styleStr, content) => {
      const el = document.createElement(tag);
      if (styleStr) el.style.cssText = styleStr;
      if (content) {
        if (typeof content === 'string') el.textContent = content;
        else el.appendChild(content);
      }
      return el;
    };

    const addInfoLine = async (label, value, delay = 0) => {
      await sleep(delay);
      if (!isRunning || !infoRef.current) return;

      const line = createElement('div', "display: flex; justify-content: space-between; margin-bottom: 0.3rem; font-size: 10px; line-height: 1.4;");
      const labelSpan = createElement('span', "color: #a0a0a0;", label);
      const valSpan = createElement('span', "color: var(--neon-red);", value);
      line.appendChild(labelSpan);
      line.appendChild(valSpan);

      infoRef.current.appendChild(line);
    };

    const typeCommand = async (text, speed = 30) => {
      if (!isRunning || !terminalRef.current) return;
      const cmdSpan = createElement('span', "color: var(--neon-red);");
      terminalRef.current.lastChild.appendChild(cmdSpan);
      for (let char of text) {
        if (!isRunning) return;
        cmdSpan.textContent += char;
        scrollToBottom();
        await sleep(speed);
      }
    };

    const showLoader = async (duration = 1800) => {
      if (!isRunning || !terminalRef.current) return;
      const frames = ['-', '\\', '|', '/'];
      let frame = 0;
      const start = Date.now();
      const loaderSpan = createElement('span', "color: var(--neon-red); font-size: 10px;");
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

      const line = createElement('div', "color: #a0a0a0; margin-bottom: 0.4rem; font-size: 10px; display: flex; align-items: center; gap: 0.5rem;");
      const checkSpan = createElement('span', "color: var(--neon-red); font-weight: bold;", "[+]");
      const nameSpan = createElement('span', "", name);
      line.appendChild(checkSpan);
      line.appendChild(nameSpan);

      terminalRef.current.appendChild(line);
      scrollToBottom();

      await sleep(500);
      if (!isRunning || !terminalRef.current) return;
      const check = createElement('div', "color: var(--text-muted); margin-bottom: 0.4rem; font-size: 9px; margin-left: 1.5rem;", "[done]");
      terminalRef.current.appendChild(check);
      scrollToBottom();
    };

    const agentMsg = async (msg) => {
      await sleep(600);
      if (!isRunning || !terminalRef.current) return;
      const line = createElement('div', "color: var(--text-main); margin-top: 0.5rem; padding: 0.6rem; background: rgba(255, 255, 255, 0.05); border-left: 2px solid var(--text-main); font-size: 10px; line-height: 1.4;");
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

      await addInfoLine('Version', 'v0.2.0', 0);
      await addInfoLine('User', 'test@example.com', 100);
      await addInfoLine('Provider', 'rta', 100);
      await addInfoLine('Model', 'auto', 100);
      await addInfoLine('RAM', '42.5 MB', 100);

      await sleep(400);
      if (!isRunning || !terminalRef.current) return;

      const prompt = createElement('div', "color: var(--neon-red); margin-bottom: 0.4rem; font-size: 10px; margin-top: 0.8rem;", "rta > ");
      terminalRef.current.appendChild(prompt);

      await typeCommand(scenario.command, 40);
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
        <span style="font-size: 10px; color: var(--text-muted); margin-left: auto; font-family: var(--font-mono);">rta-terminal-demo</span>
      </div>
      <div style="display: flex; flex-direction: column; height: 100%; padding: 1.5rem; overflow: hidden; gap: 1rem;">
        <div style="display: flex; gap: 2rem; align-items: flex-start; border-bottom: 1px solid var(--border-color); padding-bottom: 1rem; flex-shrink: 0;">
          <pre style="font-family: monospace; font-size: 7px; line-height: 1.1; color: var(--neon-red); font-weight: bold; margin: 0;">
            {` _  .-')   .-') _      ('-.     
( \\( -O ) (  OO) )    ( OO ).-. 
 ,------.  /     '._   / . --. / 
|   /\`. '|'--...__)  | \\-.  \\  
|  /  | |'--.  .--'.-'-'  |  | 
|  |_.' |   |  |    \\| |_.'  | 
|  .  '.'   |  |     |  .-.  | 
|  |\\  \\    |  |     |  | |  | 
 \\'--' '--'   \\'--'     \\'--' \\'--'`}
          </pre>
          <div ref={infoRef} style="min-width: 140px; flex: 1;"></div>
        </div>
        <div ref={terminalRef} class="terminal-body" style="flex: 1; overflow-y: auto; padding: 0; padding-right: 5px; color: var(--text-main);">
        </div>
      </div>
    </div>
  );
};

const Hero = () => (
  <section class="hero container">
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
        <h2>ARCHITECTURE</h2>
        <p class="mono">SYSTEM CAPABILITIES</p>
      </div>
      <div class="features-grid">
        {features.map(f => (
          <div class="feature-card" key={f.id}>
            <div class="feature-icon">
              <FlowerIcon size={48} color="var(--text-main)" />
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
    <div class="container" style="padding-top: 120px; padding-bottom: 80px;">
      <div class="section-header">
        <h2>DEPLOYMENT</h2>
        <p class="mono">ALLOCATE RESOURCES</p>
      </div>
      <div style="display: flex; justify-content: center; gap: 1rem; margin-bottom: 4rem;">
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
      .then(data => {
        setStatus(data);
        setLoading(false);
      })
      .catch(() => {
        setStatus({ status: "offline", services: { database: "offline", api: "offline", proxy: "offline" } });
        setLoading(false);
      });
  }, []);

  const getBadge = (val) => {
    const isOk = val === "operational" || val === "online";
    return <span class={`status-badge ${isOk ? 'operational' : 'degraded'}`}>{val?.toUpperCase() || "UNKNOWN"}</span>;
  };

  return (
    <div class="container" style="padding-top: 120px; padding-bottom: 80px;">
      <div class="section-header">
        <h2>TELEMETRY</h2>
        <p class="mono">SYSTEM INTEGRITY</p>
      </div>
      <div class="status-board">
        <div class="status-header">
          <span class="mono">Global Status</span>
          {loading ? <span class="mono">CHECKING...</span> : getBadge(status?.status)}
        </div>
        <div class="status-row">
          <span class="mono">API Endpoint</span>
          <span class="mono" style={{ color: status?.services?.api === 'operational' ? '#33ff33' : '#ff3333' }}>
            {loading ? "..." : status?.services?.api?.toUpperCase()}
          </span>
        </div>
        <div class="status-row">
          <span class="mono">Database Cluster</span>
          <span class="mono" style={{ color: status?.services?.database === 'operational' ? '#33ff33' : '#ff3333' }}>
            {loading ? "..." : status?.services?.database?.toUpperCase()}
          </span>
        </div>
        <div class="status-row">
          <span class="mono">Proxy Mesh</span>
          <span class="mono" style={{ color: status?.services?.proxy === 'operational' ? '#33ff33' : '#ff3333' }}>
            {loading ? "..." : status?.services?.proxy?.toUpperCase()}
          </span>
        </div>
      </div>
      {!loading && status?.version && (
        <p class="mono" style="font-size: 10px; color: var(--text-muted); margin-top: 20px; text-align: center;">
          v{status.version} • LAST CHECK: {new Date(status.timestamp * 1000).toLocaleTimeString()}
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
    <div class="container" style="padding-top: 120px; padding-bottom: 80px;">
      <div class="auth-box">
        <h2 style="margin-bottom: 2rem; text-align: center;">{isLogin ? "AUTHENTICATE" : "REGISTER"}</h2>

        <div style="background: rgba(59, 130, 246, 0.05); border-left: 3px solid #3b82f6; padding: 12px 16px; margin-bottom: 24px;">
          <p class="mono" style="font-size: 11px; color: #3b82f6; margin: 0; line-height: 1.5; font-weight: bold;">
            [PROTOCOL_SUGGESTION]
          </p>
          <p class="mono" style="font-size: 11px; color: var(--text-muted); margin: 4px 0 0 0; line-height: 1.5;">
            GitHub Authentication is recommended for optimal performance and CLI integration.
          </p>
        </div>

        {authError && <div style="color: var(--neon-red); margin-bottom: 1rem; font-size: 14px; padding: 10px; border: 1px solid var(--neon-red);">{authError}</div>}

        <button class="btn" style="width: 100%; margin-bottom: 1.5rem;" onClick={() => window.location.href = `${API_BASE_URL}/v1/auth/github`}>
          {isLogin ? "Continue with GitHub" : "Sign up with GitHub"}
        </button>

        {isLogin && (
          <>
            <div style="display: flex; align-items: center; gap: 1rem; margin-bottom: 1.5rem; opacity: 0.5;">
              <div style="flex: 1; height: 1px; background: var(--border-color);"></div>
              <span class="mono" style="font-size: 10px;">OR</span>
              <div style="flex: 1; height: 1px; background: var(--border-color);"></div>
            </div>

            <form class="auth-form" onSubmit={handleAuth}>
              <input type="email" name="email" class="auth-input" placeholder="Email" required />
              <input type="password" name="password" class="auth-input" placeholder="Password" required />
              <div ref={captchaRef} class="h-captcha" data-sitekey="51b06ce2-0f58-4148-8fec-b2944c54e718" style="margin-bottom: 1rem;"></div>
              <button type="submit" class="btn btn-primary" style="width: 100%;" disabled={isLoading}>
                {isLoading ? "PROCESSING..." : "Login"}
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
  <div class="container" style="padding-top: 120px; padding-bottom: 80px; max-width: 800px;">
    <h2 style="margin-bottom: 2rem;">TERMS OF SERVICE</h2>
    <div style="color: var(--text-muted); font-size: 18px; line-height: 1.8;">
      <p style="margin-bottom: 2rem;">By accessing Rta, you agree to be bound by these terms. If you disagree with any part, you may not access our services.</p>
      <h3 style="color: var(--text-main); margin-bottom: 1rem; margin-top: 2rem;">1. Acceptance of Terms</h3>
      <p style="margin-bottom: 2rem;">Billing is processed via secure payment gateways. Subscriptions renew automatically unless cancelled. All fees are non-refundable except as required by law.</p>
    </div>
  </div>
);

const RoadmapPage = () => (
  <div class="container" style="padding-top: 120px; padding-bottom: 80px;">
    <div class="section-header">
      <h2>ROADMAP</h2>
      <p class="mono">UPCOMING DEPLOYMENTS</p>
    </div>
    <div class="features-grid">
      <div class="feature-card">
        <div class="feature-icon mono" style="font-size: 1rem; color: var(--text-main);">PHASE 01 [ACTIVE]</div>
        <h3>Core CLI v1.0</h3>
        <p>Auth, Telemetry, Project Indexing</p>
      </div>
      <div class="feature-card">
        <div class="feature-icon mono" style="font-size: 1rem;">PHASE 02 [SOON]</div>
        <h3>Public Beta</h3>
        <p>Context Sync, AI Refactor Engine</p>
      </div>
      <div class="feature-card">
        <div class="feature-icon mono" style="font-size: 1rem; color: var(--text-main);">PHASE 03 [BETA]</div>
        <h3>Mobile App</h3>
        <p>Android Chat Interface, Account Sync</p>
      </div>
    </div>
  </div>
);

const ReleasesPage = () => {
  const [os, setOs] = useState('linux');

  return (
    <div class="container" style="padding-top: 120px; padding-bottom: 80px;">
      <div class="section-header">
        <h2>RELEASES</h2>
        <p class="mono">DOWNLOAD BINARIES</p>
      </div>
      <div style="display: flex; justify-content: center; gap: 1rem; margin-bottom: 3rem;">
        <button class={`btn ${os === 'linux' ? 'btn-primary' : ''}`} onClick={() => setOs('linux')}>Linux</button>
        <button class={`btn ${os === 'windows' ? 'btn-primary' : ''}`} onClick={() => setOs('windows')}>Windows</button>
        <button class={`btn ${os === 'android' ? 'btn-primary' : ''}`} onClick={() => setOs('android')}>Android</button>
      </div>
      <div class="status-board">
        {os === 'android' ? (
          <div style="padding: 3rem; text-align: center;">
            <h4 class="mono" style="margin-bottom: 2rem; color: var(--text-main);">MOBILE PROTOCOL [BETA]</h4>
            <div style="background: #fff; padding: 1.5rem; display: inline-block; border-radius: 12px; margin-bottom: 2rem; box-shadow: 0 0 30px rgba(59, 130, 246, 0.2);">
              <img src="/assets/android_qr.png" alt="Android QR" style="width: 220px; height: 220px; display: block;" />
            </div>
            <div style="max-width: 500px; margin: 0 auto; padding: 1.5rem; background: rgba(255, 255, 255, 0.03); border: 1px solid var(--border-color);">
              <p class="mono" style="font-size: 11px; color: var(--neon-red); line-height: 1.6; margin: 0;">
                [CLASSIFIED] Mobile deployment is restricted to Chat & Telemetry. 
                Full Autonomous Agent capabilities (Code Execution/Refactoring) remain exclusive to CLI & Desktop nodes.
              </p>
            </div>
          </div>
        ) : (
          <>
            <div class="status-header">
              <span class="mono">v1.4.2 [STABLE]</span>
              <a
                href={os === 'linux' ? "/rta" : "/rta.exe"}
                download={os === 'linux' ? "rta" : "rta.exe"}
                class="btn btn-primary"
                style="text-decoration: none;"
              >
                Download for {os === 'linux' ? 'Linux' : 'Windows'}
              </a>
            </div>
            <div style="padding: 2rem;">
              <h4 class="mono" style="margin-bottom: 1rem;">QUICK INSTALL</h4>
              <pre style="background: var(--bg-dark); padding: 1.5rem; border: 1px solid var(--border-color); color: var(--text-muted); font-family: var(--font-mono); font-size: 14px;">
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

const AppFooter = () => (
  <footer class="footer">
    <div class="container">
      <div class="footer-grid">
        <div class="footer-col">
          <Link href="/" class="logo" style="margin-bottom: 1rem;">
            <FlowerIcon size={24} color="var(--text-main)" style={{ marginRight: '8px' }} />
            RTA
          </Link>
          <p style="color: var(--text-muted); font-size: 14px;">The high-performance developer toolkit for the next era of computing.</p>
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
          <a href="#">Documentation</a>
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
        <span>© 2026 Rta Software. All rights reserved.</span>
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
        <h2 style="font-size: 80px; margin-bottom: 0;">404</h2>
        <p class="mono">RESOURCE_NOT_FOUND</p>
      </div>
      <div style="margin-bottom: 3rem; opacity: 0.8; display: flex; justify-content: center;">
        <FlowerIcon size={120} color="var(--text-main)" />
      </div>
      <div style="display: flex; gap: 1rem; justify-content: center;">
        <Link href="/" class="btn btn-primary">Return to Base</Link>
        <Link href="/status" class="btn">Diagnostics</Link>
      </div>
    </div>
    <p class="mono" style="margin-top: 2rem; color: var(--text-muted); font-size: 12px; letter-spacing: 0.2em;">
      TERMINATED_SESSION_ID: {Math.random().toString(16).slice(2, 10).toUpperCase()}
    </p>
  </div>
);

const App = () => {
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
            <Route path="/blog" component={BlogPage} />
            <Route path="/blog/:slug" component={BlogPage} />
            <Route path="/dashboard" component={Dashboard} />
            <Route component={NotFoundPage} />
          </Switch>
        </Router>
      </main>
      <AppFooter />
      <Analytics />
    </div>

  );
};

render(<App />, document.body);

