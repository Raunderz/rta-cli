import { useState } from 'preact/hooks';
import { Link } from 'wouter';
import { useHead } from './useHead';

const API_BASE = import.meta.env.VITE_BACKEND_URL || "https://rta-tb0k.onrender.com";

const CodeBlock = ({ code, id, copied, onCopy }) => (
  <div style={{ position: 'relative', marginBottom: '1.5rem' }}>
    <button
      onClick={() => onCopy(code, id)}
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

export const ApiPage = () => {
  useHead({ title: "API", description: "Build with Rta. OpenAI-compatible endpoints for AI-powered development." });
  const [copied, setCopied] = useState(null);

  const copy = (text, id) => {
    navigator.clipboard.writeText(text);
    setCopied(id);
    setTimeout(() => setCopied(null), 2000);
  };

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
        <CodeBlock id="auth-header" code={`curl -H "X-API-KEY: your_api_key_here" ${API_BASE}/v1/chat`} copied={copied} onCopy={copy} />
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
}`} copied={copied} onCopy={copy} />

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
  }'`} copied={copied} onCopy={copy} />

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
}`} copied={copied} onCopy={copy} />

        <h4 style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginBottom: '0.75rem', letterSpacing: '0.05em', textTransform: 'uppercase' }}>Example — Streaming</h4>
        <CodeBlock id="chat-stream-curl" code={`curl -X POST ${API_BASE}/v1/chat \\
  -H "Content-Type: application/json" \\
  -H "X-API-KEY: your_api_key_here" \\
  -d '{
    "model": "rta-auto",
    "messages": [{"role": "user", "content": "Hello"}],
    "stream": true,
    "format": "openai"
  }'`} copied={copied} onCopy={copy} />

        <h4 style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginBottom: '0.75rem', letterSpacing: '0.05em', textTransform: 'uppercase' }}>Stream Events (OpenAI format)</h4>
        <CodeBlock id="chat-stream-events" code={`data: {"choices":[{"delta":{"role":"assistant"},"index":0}]}

data: {"choices":[{"delta":{"content":"Hello"},"index":0}]}

data: {"choices":[{"delta":{"content":"!"},"index":0}]}

data: {"choices":[{"delta":{},"finish_reason":"stop"}],"usage":{"prompt_tokens":12,"completion_tokens":2,"total_tokens":14}}

data: [DONE]`} copied={copied} onCopy={copy} />

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
}`} copied={copied} onCopy={copy} />
      </Endpoint>

      <Endpoint method="GET" path="/v1/usage" desc="Check your current token and call usage for today and this month.">
        <h4 style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginBottom: '0.75rem', letterSpacing: '0.05em', textTransform: 'uppercase' }}>Example</h4>
        <CodeBlock id="usage-curl" code={`curl ${API_BASE}/v1/usage \\
  -H "X-API-KEY: your_api_key_here"`} copied={copied} onCopy={copy} />

        <h4 style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginBottom: '0.75rem', letterSpacing: '0.05em', textTransform: 'uppercase' }}>Response</h4>
        <CodeBlock id="usage-response" code={`{
  "tier": "free",
  "calls_today": 3,
  "calls_limit": 10,
  "tokens_today": 1250,
  "tokens_month": 15420,
  "tokens_limit_day": 50000
}`} copied={copied} onCopy={copy} />
      </Endpoint>

      <Endpoint method="GET" path="/v1/status" desc="Public service status. No authentication required.">
        <h4 style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginBottom: '0.75rem', letterSpacing: '0.05em', textTransform: 'uppercase' }}>Example</h4>
        <CodeBlock id="status-curl" code={`curl ${API_BASE}/v1/status`} copied={copied} onCopy={copy} />

        <h4 style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginBottom: '0.75rem', letterSpacing: '0.05em', textTransform: 'uppercase' }}>Response</h4>
        <CodeBlock id="status-response" code={`{
  "status": "operational",
  "version": "0.1.0",
  "services": {
    "database": "operational",
    "api": "operational",
    "proxy": "operational"
  }
}`} copied={copied} onCopy={copy} />
      </Endpoint>

      <Endpoint method="GET" path="/health" desc="Simple health check. No authentication required.">
        <CodeBlock id="health-response" code={`{
  "status": "healthy"
}`} copied={copied} onCopy={copy} />
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
