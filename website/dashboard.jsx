import { render, h, Fragment } from 'preact';
import { useState, useEffect } from 'preact/hooks';

const API_BASE_URL = import.meta.env.VITE_BACKEND_URL || "http://localhost:8000";

// Handle OAuth Hash
const hashParams = new URLSearchParams(window.location.hash.substring(1));
if (hashParams.has("access_token")) {
    const oauthUser = {
        access_token: hashParams.get("access_token"),
        refresh_token: hashParams.get("refresh_token"),
        api_key: hashParams.get("api_key") || null
    };
    const existing = JSON.parse(localStorage.getItem("rta_user") || "{}");
    const finalUser = { ...existing, ...oauthUser };
    if (!finalUser.api_key && existing.api_key) finalUser.api_key = existing.api_key;
    
    localStorage.setItem("rta_user", JSON.stringify(finalUser));
    window.location.hash = "";
}

const Icon = ({ d, size = "16" }) => (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <path d={d} />
    </svg>
);

const SupportBot = ({ user }) => {
    const [chatOpen, setChatOpen] = useState(false);
    const [chatMessages, setChatMessages] = useState([{ role: "assistant", content: "Hello! I'm the Rta assistant. How can I help you today?" }]);
    const [chatInput, setChatInput] = useState("");
    const [isTyping, setIsTyping] = useState(false);

    const sendChatMessage = async () => {
        if (!chatInput.trim() || isTyping) return;
        
        const userMsg = chatInput;
        const newMessages = [...chatMessages, { role: "user", content: userMsg }];
        setChatMessages(newMessages);
        setChatInput("");
        setIsTyping(true);

        try {
            const res = await fetch(`${API_BASE_URL}/v1/chat`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "X-API-KEY": user?.api_key || "",
                    "ngrok-skip-browser-warning": "true"
                },
                body: JSON.stringify({
                    messages: [
                        { role: "system", content: "You are the Rta Support Bot. Rta is a professional code editor and CLI. Be concise and technical." },
                        ...newMessages
                    ],
                    model: "auto",
                    provider: "auto"
                })
            });
            const data = await res.json();
            if (!res.ok) throw new Error(data.detail || "Chat failed");
            
            const assistantMsg = data.choices[0].message.content;
            setChatMessages(prev => [...prev, { role: "assistant", content: assistantMsg }]);
        } catch (e) {
            setChatMessages(prev => [...prev, { role: "assistant", content: "Error: " + e.message }]);
        } finally {
            setIsTyping(false);
        }
    };

    return (
        <div class="chatbot-container">
            {chatOpen ? (
                <div class="chat-window">
                    <div class="chat-header">
                        <span style="font-weight: 600; font-size: 13px;">Support</span>
                        <button class="btn-ghost" onClick={() => setChatOpen(false)} style="padding: 2px; border:none;">
                            <Icon d="M18 6L6 18M6 6l12 12" />
                        </button>
                    </div>
                    <div class="chat-messages">
                        {chatMessages.map((m, i) => (
                            <div key={i} class={`chat-msg ${m.role}`}>{m.content}</div>
                        ))}
                        {isTyping && <div style="font-size: 11px; color: var(--text-muted); padding: 0.5rem;">Thinking...</div>}
                    </div>
                    <div class="chat-input-area">
                        <input 
                            class="chat-input"
                            placeholder="Ask a question..." 
                            value={chatInput}
                            onInput={(e) => setChatInput(e.target.value)}
                            onKeyDown={(e) => e.key === "Enter" && sendChatMessage()}
                        />
                        <button class="btn-ghost active" onClick={sendChatMessage} style="border: none; padding: 0 12px;">
                            <Icon d="M22 2L11 13M22 2l-7 20-4-9-9-4 20-7z" />
                        </button>
                    </div>
                </div>
            ) : null}
            <button class="chat-trigger" onClick={() => setChatOpen(!chatOpen)}>
                <Icon d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" size="20" />
            </button>
        </div>
    );
};

const Dashboard = () => {
    const [user, setUser] = useState(() => JSON.parse(localStorage.getItem("rta_user") || "null"));
    const [keyVisible, setKeyVisible] = useState(false);
    const [selectedOS, setSelectedOS] = useState("linux");
    const [dashData, setDashData] = useState(null);
    const [error, setError] = useState(null);
    const [isLoading, setIsLoading] = useState(true);

    const logout = () => {
        localStorage.removeItem("rta_user");
        window.location.href = "/";
    };

    useEffect(() => {
        if (!user) {
            window.location.href = "/";
            return;
        }

        const fetchDashboard = async () => {
            try {
                const headers = { "ngrok-skip-browser-warning": "true" };
                if (user.api_key) {
                    headers["X-API-KEY"] = user.api_key;
                } else if (user.access_token) {
                    headers["Authorization"] = `Bearer ${user.access_token}`;
                }

                const res = await fetch(`${API_BASE_URL}/v1/dashboard`, { headers });
                if (!res.ok) {
                    if (res.status === 401) logout();
                    throw new Error("Failed to load dashboard data");
                }
                const data = await res.json();
                setDashData(data);
                
                if (data.api_key && !user.api_key) {
                    const newUser = { ...user, api_key: data.api_key };
                    setUser(newUser);
                    localStorage.setItem("rta_user", JSON.stringify(newUser));
                }
            } catch (e) {
                setError(e.message);
            } finally {
                setIsLoading(false);
            }
        };

        fetchDashboard();
    }, []);

    if (!user) return null;

    return (
        <div style="position: relative; height: 100vh; width: 100vw;">
            <div class="app-shell">
                <nav class="sidebar">
                    <a href="/" class="sidebar-logo">rta</a>
                    <div class="nav-group">
                        <div class="nav-label">Overview</div>
                        <div class="nav-item active">
                            <Icon d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z" /> Dashboard
                        </div>
                        <div class="nav-item">
                            <Icon d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z" /> Projects
                        </div>
                    </div>
                    <div class="nav-group">
                        <div class="nav-label">Settings</div>
                        <div class="nav-item">
                            <Icon d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2" /> Profile
                        </div>
                        <div class="nav-item">
                            <Icon d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9" /> Alerts
                        </div>
                    </div>
                    <div style="margin-top: auto;">
                        <div class="nav-item" onClick={logout}>
                            <Icon d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4" /> Logout
                        </div>
                    </div>
                </nav>

                <main class="main-canvas">
                    {isLoading ? (
                        <div style="color: var(--text-muted); font-size: 14px;">Loading...</div>
                    ) : error ? (
                        <div style="color: #EF4444;">Error: {error}</div>
                    ) : dashData ? (
                        <div class="content-grid">
                            <div style="grid-column: 1 / -1; margin-bottom: 32px;">
                                <h2 style="font-size: 24px; margin: 0;">Welcome back, {dashData.username}</h2>
                                <p style="color: var(--text-muted); margin-top: 4px; font-size: 14px;">Member since {new Date(dashData.member_since).toLocaleDateString()}</p>
                            </div>

                            {[
                                { label: "Daily Calls", value: `${dashData.usage.calls_today} / ${dashData.usage.calls_limit_day}`, icon: "M22 12h-4l-3 9L9 3l-3 9H2" },
                                { label: "Tokens Used", value: dashData.usage.tokens_used_month.toLocaleString(), icon: "M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" },
                                { label: "Current Tier", value: dashData.tier.toUpperCase(), icon: "M12 11c0 3.517-1.009 6.799-2.753 9.571m-3.44-2.04l.054-.09A10.003 10.003 0 0012 21" }
                            ].map((m, i) => (
                                <div key={i} class="card">
                                    <div class="card-header">
                                        <span class="card-title">{m.label}</span>
                                        <Icon d={m.icon} />
                                    </div>
                                    <div class="metric-value">{m.value}</div>
                                </div>
                            ))}

                            <div class="card api-well">
                                <span class="card-title">API Key</span>
                                <span class="mono-key">{keyVisible ? (user.api_key || "UNSET") : "••••••••••••••••••••••••••••••••"}</span>
                                <div style="display: flex; gap: 8px;">
                                    <button class="btn-ghost" onClick={() => setKeyVisible(!keyVisible)}>Reveal</button>
                                    <button class="btn-ghost" onClick={() => user.api_key && navigator.clipboard.writeText(user.api_key)}>Copy</button>
                                </div>
                            </div>

                            <div class="card" style="grid-column: span 3;">
                                <span class="card-title">Recent Activity</span>
                                <div style="margin-top: 16px;">
                                    {dashData.recent_calls && dashData.recent_calls.length > 0 ? (
                                        dashData.recent_calls.map((a, i) => (
                                            <div key={i} class="activity-row">
                                                <div class="status-indicator" style="background: #10B981;"></div>
                                                <div style="display: flex; flex-direction: column;">
                                                    <span style="font-weight: 500;">{a.model_used || "AI Request"}</span>
                                                    <span style="font-size: 11px; color: var(--text-muted);">{a.provider}</span>
                                                </div>
                                                <span style="color: var(--text-muted); font-size: 11px; font-family: var(--font-mono);">{new Date(a.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</span>
                                            </div>
                                        ))
                                    ) : (
                                        <p style="color: var(--text-muted); font-size: 13px;">No recent activity.</p>
                                    )}
                                </div>
                            </div>

                            <div class="card" style="grid-column: span 3;">
                                <span class="card-title">Releases</span>
                                <div style="display: flex; gap: 8px; margin: 20px 0;">
                                    <button class={`btn-ghost ${selectedOS === 'linux' ? 'active' : ''}`} onClick={() => setSelectedOS('linux')}>Linux</button>
                                    <button class={`btn-ghost ${selectedOS === 'windows' ? 'active' : ''}`} onClick={() => setSelectedOS('windows')}>Windows</button>
                                </div>
                                <a
                                    href={selectedOS === "linux" ? "/rta" : "/rta.exe"}
                                    class="download-btn"
                                    download={selectedOS === "linux" ? "rta" : "rta.exe"}
                                >
                                    Download for {selectedOS.toUpperCase()} <Icon d="M12 15V3m0 12l-4-4m4 4l4-4" />
                                </a>
                            </div>
                        </div>
                    ) : null}
                </main>
            </div>
            <SupportBot user={user} />
        </div>
    );
};

render(<Dashboard />, document.getElementById("dash-app"));
