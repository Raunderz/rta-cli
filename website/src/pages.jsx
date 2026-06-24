import { useState, useEffect } from 'preact/hooks';
import { marked } from 'marked';
import DOMPurify from 'dompurify';
import { useHead } from './useHead';

export const PricingPage = () => {
  useHead({ title: "Pricing", description: "Simple, transparent pricing for every maker." });
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

export const StatusPage = () => {
  useHead({ title: "Status", description: "Check Rta service status." });
  useEffect(() => {
    window.location.href = "https://stats.uptimerobot.com/S5Qwww7Jtp";
  }, []);
  return null;
};

export const LegalPage = () => {
  useHead({ title: "Terms of Service", description: "Rta terms of service." });
  const [content, setContent] = useState("");

  useEffect(() => {
    fetch('/terms.md')
      .then(res => res.text())
      .then(text => setContent(marked.parse(text)))
      .catch(() => setContent("Error loading terms of service."));
  }, []);

  return (
    <div class="container" style="padding-top: clamp(100px, 15vh, 140px); padding-bottom: 80px; max-width: 800px;">
      <div class="markdown-body" dangerouslySetInnerHTML={{ __html: DOMPurify.sanitize(content) }} />
    </div>
  );
};

export const PrivacyPage = () => {
  useHead({ title: "Privacy Policy", description: "Rta privacy policy." });
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

export const RoadmapPage = () => {
  useHead({ title: "Roadmap", description: "Where we've been and where we're going." });
  const phases = [
    {
      status: "done",
      title: "CLI Agent Core",
      date: "May 2026",
      link: "https://github.com/Raunderz/rta-cli",
      items: [
        "Async event-driven architecture with streaming",
        "22+ tools: bash, file ops, grep, git, web search, memory, LSP",
        "Multi-provider routing with automatic fallback",
        "MCP plugin system for external tool integration",
        "Session persistence and management",
        "90+ test files covering tools, providers, UI, security",
      ],
    },
    {
      status: "done",
      title: "Backend & API",
      date: "June 2026",
      items: [
        "FastAPI backend with OAuth (GitHub PKCE) and email auth",
        "6 AI provider adapters with fallback chain",
        "OpenAI-compatible /v1/chat endpoint (streaming + non-streaming)",
        "API key management, rate limiting, usage tracking",
        "Security hardening: secret scrubbing, CORS, TLS verification",
      ],
    },
    {
      status: "done",
      title: "Desktop IDE",
      date: "June 2026",
      link: "https://github.com/Raunderz/rta-desktop",
      items: [
        "Lite XL fork — C core, Lua plugins, <100ms startup",
        "Chat panel with streaming, tool display, diff previews",
        "CLI integration via JSON-lines pipe IPC",
        "Session history, auto-approve, keyboard shortcuts",
        "61 plugins including minimap, autosave, sticky scroll",
      ],
    },
    {
      status: "done",
      title: "Mobile App",
      date: "June 2026",
      items: [
        "React Native (Expo) with chat, editor, terminal, file browser",
        "Cloud session sync with conflict detection and resolution",
        "Git integration via isomorphic-git",
        "WebSocket terminal with xterm.js",
        "Auto-save, session recovery, error boundaries, retry logic",
      ],
    },
    {
      status: "active",
      title: "Billing & Payments",
      date: "In Progress",
      items: [
        "Stripe integration for tier upgrades",
        "Usage-based billing with per-user limits",
        "Webhook handling for subscription events",
        "Invoice generation and history",
      ],
    },
    {
      status: "active",
      title: "CLI Performance",
      date: "In Progress",
      items: [
        "Lazy MCP server loading (defer to first use)",
        "Tool schema caching (skip recomputation each turn)",
        "Async git context (parallel subprocess calls)",
        "Session index caching",
      ],
    },
    {
      status: "planned",
      title: "PR Review Bot",
      date: "Q3 2026",
      items: [
        "GitHub webhook integration for pull request events",
        "Automated code review with inline comments",
        "Security vulnerability scanning",
        "Dependency audit and license checking",
      ],
    },
    {
      status: "planned",
      title: "Research Pipeline",
      date: "Q3 2026",
      items: [
        "Multi-query depth: sub-query expansion for better search",
        "ArXiv, GitHub, Stack Overflow, YouTube transcript sources",
        "Source credibility scoring",
        "Research sessions with persistent context",
      ],
    },
    {
      status: "planned",
      title: "v1.0 Public Launch",
      date: "Q4 2026",
      items: [
        "Stable API with SLA guarantees",
        "Paid tier rollout with Stripe",
        "Desktop IDE: macOS and Windows builds",
        "Mobile app: iOS release",
        "Documentation site with interactive examples",
      ],
    },
  ];

  const statusColors = {
    done: { bg: "rgba(16, 185, 129, 0.15)", color: "#10B981", label: "Shipped" },
    active: { bg: "var(--accent-glow)", color: "var(--primary)", label: "In Progress" },
    planned: { bg: "var(--secondary-soft)", color: "#B45309", label: "Planned" },
  };

  return (
    <div class="container" style="padding-top: clamp(100px, 15vh, 140px); padding-bottom: 80px; max-width: 900px;">
      <div class="section-header">
        <h2>Roadmap</h2>
        <p>Where we've been and where we're going.</p>
      </div>

      <div style="display: flex; gap: 2rem; margin-bottom: 3rem; flex-wrap: wrap;">
        {Object.entries(statusColors).map(([key, s]) => (
          <div key={key} style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
            <span style={{ width: 10, height: 10, borderRadius: "50%", background: s.color, display: "inline-block" }} />
            <span style={{ fontSize: "0.85rem", color: "var(--text-secondary)" }}>{s.label}</span>
          </div>
        ))}
      </div>

      <div style={{ display: "flex", flexDirection: "column", gap: "2rem" }}>
        {phases.map((phase, i) => {
          const s = statusColors[phase.status];
          return (
            <div key={i} style={{
              background: "var(--bg-card)", border: "1px solid var(--border)",
              borderRadius: "var(--radius-md)", padding: "1.5rem",
              opacity: phase.status === "planned" ? 0.7 : 1,
            }}>
              <div style={{ display: "flex", alignItems: "center", gap: "0.75rem", marginBottom: "1rem" }}>
                <span style={{
                  background: s.bg, color: s.color, padding: "3px 10px",
                  borderRadius: "var(--radius-sm)", fontSize: "11px",
                  fontWeight: 600, letterSpacing: "0.03em",
                }}>{s.label}</span>
                <span style={{ fontSize: "0.8rem", color: "var(--text-muted)" }}>{phase.date}</span>
              </div>
              <h3 style={{ margin: "0 0 0.75rem", fontSize: "1.1rem" }}>
                {phase.link ? (
                  <a href={phase.link} target="_blank" rel="noopener noreferrer" style={{ color: "var(--text-primary)", textDecoration: "none", borderBottom: "1px solid var(--border)" }}>
                    {phase.title} ↗
                  </a>
                ) : phase.title}
              </h3>
              <ul style={{ margin: 0, paddingLeft: "1.25rem", color: "var(--text-secondary)", fontSize: "0.9rem", lineHeight: 1.8 }}>
                {phase.items.map((item, j) => <li key={j}>{item}</li>)}
              </ul>
            </div>
          );
        })}
      </div>
    </div>
  );
};
