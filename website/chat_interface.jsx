import { h, Fragment } from 'preact';
import { useState, useRef, useEffect } from 'preact/hooks';
import { marked } from 'marked';
import DOMPurify from 'dompurify';

const API_BASE_URL = import.meta.env.VITE_BACKEND_URL ? import.meta.env.VITE_BACKEND_URL.replace(/\/?$/, "") : "";

const getGreeting = () => {
  const hour = new Date().getHours();
  if (hour < 12) return "Good morning";
  if (hour < 18) return "Good afternoon";
  return "Good evening";
};

const gravatarUrl = (email) => {
  const hash = email ? Array.from(new TextEncoder().encode(email.toLowerCase().trim()), b => b.toString(16).padStart(2, '0')).join('') : "";
  return `https://www.gravatar.com/avatar/${hash}?d=mp&s=200`;
};

const loadConversations = () => {
  try {
    const saved = localStorage.getItem("rta_conversations");
    return saved ? JSON.parse(saved) : [];
  } catch { return []; }
};

const saveConversations = (convs) => {
  localStorage.setItem("rta_conversations", JSON.stringify(convs));
};

const makeConv = () => ({
  id: crypto.randomUUID(),
  title: "New chat",
  messages: [],
  sessionId: crypto.randomUUID(),
  turnIndex: 0,
  createdAt: Date.now(),
});

const ChatInterface = ({ user: propUser }) => {
  const [user, setUser] = useState(() => JSON.parse(localStorage.getItem("rta_user") || "null"));
  const [dashData, setDashData] = useState(null);
  const [conversations, setConversations] = useState(() => {
    const convs = loadConversations();
    if (convs.length === 0) {
      const fresh = makeConv();
      localStorage.setItem("rta_conversations", JSON.stringify([fresh]));
      return [fresh];
    }
    return convs;
  });
  const [activeId, setActiveId] = useState(() => {
    const convs = loadConversations();
    if (convs.length === 0) return null;
    const saved = localStorage.getItem("rta_active_conv");
    if (saved && convs.some((c) => c.id === saved)) return saved;
    return convs[convs.length - 1].id;
  });
  const [input, setInput] = useState("");
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [isTyping, setIsTyping] = useState(false);
  const [userMenuOpen, setUserMenuOpen] = useState(false);
  const inputRef = useRef(null);
  const menuRef = useRef(null);
  const messagesEndRef = useRef(null);
  const [deletingId, setDeletingId] = useState(null);

  useEffect(() => {
    if (!user) window.location.href = "/";
    localStorage.removeItem("rta_chat_messages");
    localStorage.removeItem("rta_chat_session");
    localStorage.removeItem("rta_chat_turn");
  }, []);

  useEffect(() => {
    const fetchDashboard = async () => {
      try {
        const headers = { "ngrok-skip-browser-warning": "true" };
        if (user?.api_key) headers["X-API-KEY"] = user.api_key;
        else if (user?.access_token) headers["Authorization"] = `Bearer ${user.access_token}`;
        const res = await fetch(`${API_BASE_URL}/v1/dashboard`, { headers });
        if (!res.ok) throw new Error("Failed to load dashboard");
        const data = await res.json();
        setDashData(data);
        if (data.api_key && !user?.api_key) {
          const newUser = { ...user, api_key: data.api_key };
          setUser(newUser);
          localStorage.setItem("rta_user", JSON.stringify(newUser));
        }
      } catch (e) { console.error("Dashboard fetch failed:", e); }
    };
    if (user) fetchDashboard();
  }, []);

  useEffect(() => {
    saveConversations(conversations);
  }, [conversations]);

  useEffect(() => {
    if (activeId) localStorage.setItem("rta_active_conv", activeId);
    else localStorage.removeItem("rta_active_conv");
  }, [activeId]);

  useEffect(() => {
    if (!activeId && conversations.length > 0) {
      setActiveId(conversations[conversations.length - 1].id);
    }
  }, []);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [conversations, activeId, isTyping]);

  useEffect(() => {
    const handleClick = (e) => {
      if (menuRef.current && !menuRef.current.contains(e.target)) setUserMenuOpen(false);
    };
    document.addEventListener("mousedown", handleClick);
    return () => document.removeEventListener("mousedown", handleClick);
  }, []);

  const activeConv = conversations.find((c) => c.id === activeId) || null;
  const messages = activeConv?.messages || [];
  const sessionId = activeConv?.sessionId || "";
  const turnIndex = activeConv?.turnIndex || 0;
  const username = dashData?.username || user?.username || "User";
  const email = dashData?.email || user?.email || "";
  const tier = dashData?.tier || user?.tier || "free";

  const updateConv = (id, updates) => {
    setConversations((prev) => prev.map((c) => (c.id === id ? { ...c, ...updates } : c)));
  };

  const switchConv = (id) => {
    if (isTyping) return;
    setActiveId(id);
    setInput("");
  };

  const startNewChat = () => {
    const conv = makeConv();
    setConversations((prev) => [...prev, conv]);
    setActiveId(conv.id);
    setInput("");
  };

  const deleteConv = (id, e) => {
    e.stopPropagation();
    const updated = conversations.filter((c) => c.id !== id);
    setConversations(updated);
    if (activeId === id) {
      const next = updated.length > 0 ? updated[updated.length - 1].id : null;
      setActiveId(next);
      if (!next) {
        const fresh = makeConv();
        setConversations([fresh]);
        setActiveId(fresh.id);
      }
    }
  };

  const handleSend = async () => {
    if (!input.trim() || isTyping || !activeConv) return;

    let conv = conversations.find((c) => c.id === activeId);
    if (!conv) return;

    const userMsg = { role: "user", content: input };
    const updatedMessages = [...conv.messages, userMsg];
    const title = conv.title === "New chat" ? input.trim().slice(0, 40) + (input.trim().length > 40 ? "..." : "") : conv.title;

    updateConv(activeId, { messages: updatedMessages, title });
    setInput("");
    setIsTyping(true);

    try {
      const res = await fetch(`${API_BASE_URL}/v1/chat`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-API-KEY": user?.api_key || "",
          "ngrok-skip-browser-warning": "true",
        },
        body: JSON.stringify({
          messages: [
            { role: "system", content: "You are Rta, an expert coding assistant. Be concise, technical, and helpful." },
            ...updatedMessages,
          ],
          model: "auto",
          provider: "auto",
          session_id: conv.sessionId,
          turn_index: conv.turnIndex,
        }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Chat failed");

      const newTurnIndex = conv.turnIndex + 2;
      const assistantMsg = { role: "assistant", content: data.choices[0].message.content };
      updateConv(activeId, {
        messages: [...updatedMessages, assistantMsg],
        turnIndex: newTurnIndex,
      });
    } catch (e) {
      updateConv(activeId, {
        messages: [...updatedMessages, { role: "assistant", content: "Error: " + e.message }],
      });
    } finally {
      setIsTyping(false);
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const hasUserMessages = messages.some((m) => m.role === "user");

  const markdownCss = [
    ".chat-markdown{color:#e0e0e0;font-size:15px;line-height:1.6}",
    ".chat-markdown p{margin:0 0 12px}",
    ".chat-markdown p:last-child{margin-bottom:0}",
    ".chat-markdown h1,.chat-markdown h2,.chat-markdown h3,.chat-markdown h4{color:#fff;margin:16px 0 8px;font-weight:600}",
    ".chat-markdown h1{font-size:1.3rem}",
    ".chat-markdown h2{font-size:1.2rem}",
    ".chat-markdown h3{font-size:1.1rem}",
    ".chat-markdown ul,.chat-markdown ol{padding-left:20px;margin:8px 0}",
    ".chat-markdown li{margin-bottom:4px}",
    ".chat-markdown code{background:#2a2a2a;padding:2px 6px;border-radius:4px;font-size:13px;color:#ff7a33}",
    ".chat-markdown pre{background:#0d0d0d;padding:16px;border-radius:8px;overflow-x:auto;margin:12px 0;border:1px solid #2a2a2a}",
    ".chat-markdown pre code{background:none;padding:0;color:#e0e0e0;font-size:13px}",
    ".chat-markdown blockquote{border-left:3px solid #ff7a33;padding-left:12px;color:#999;margin:12px 0}",
    ".chat-markdown a{color:#ff7a33;text-decoration:underline}",
    ".chat-markdown hr{border:none;border-top:1px solid #2a2a2a;margin:16px 0}",
    ".chat-markdown table{border-collapse:collapse;width:100%;margin:12px 0}",
    ".chat-markdown th,.chat-markdown td{border:1px solid #2a2a2a;padding:8px 12px;text-align:left}",
    ".chat-markdown th{background:#0d0d0d;color:#fff;font-weight:600}",
  ].join("");

  return (
    <Fragment>
    <style>{markdownCss}</style>
    <div
      style={{
        display: "flex",
        height: "100vh",
        backgroundColor: "#1a1a1a",
        color: "#ffffff",
        fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
        overflow: "hidden",
      }}
    >
      <div
        style={{
          width: sidebarOpen ? "300px" : "0",
          backgroundColor: "#0d0d0d",
          borderRight: "1px solid #2a2a2a",
          display: "flex",
          flexDirection: "column",
          transition: "width 0.3s ease",
          overflow: "hidden",
          flexShrink: 0,
        }}
      >
        <div style={{ padding: "16px" }}>
          <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: "16px" }}>
            <h2 style={{ margin: 0, fontSize: "16px", fontWeight: 600 }}>Rta</h2>
            <button
              onClick={() => setSidebarOpen(false)}
              style={{ background: "none", border: "none", color: "#999", cursor: "pointer", fontSize: "18px", padding: "4px" }}
            >
              ✕
            </button>
          </div>
          <button
            onClick={startNewChat}
            style={{
              width: "100%", padding: "10px 16px", backgroundColor: "transparent",
              border: "1px solid #3a3a3a", borderRadius: "8px", color: "#fff",
              cursor: "pointer", display: "flex", alignItems: "center", gap: "8px", fontSize: "13px",
            }}
            onMouseOver={(e) => (e.target.style.backgroundColor = "#2a2a2a")}
            onMouseOut={(e) => (e.target.style.backgroundColor = "transparent")}
          >
            <span>+</span> New chat
          </button>
        </div>

        <div style={{ flex: 1, overflowY: "auto", padding: "0 8px" }}>
          {conversations.length === 0 ? (
            <div style={{ padding: "16px", color: "#555", fontSize: "13px", textAlign: "center" }}>
              No conversations yet
            </div>
          ) : (
            [...conversations].reverse().map((conv) => (
              <div
                key={conv.id}
                onClick={() => switchConv(conv.id)}
                onMouseOver={(e) => { if (conv.id !== activeId) e.currentTarget.style.backgroundColor = "#1a1a1a"; }}
                onMouseOut={(e) => { if (conv.id !== activeId) e.currentTarget.style.backgroundColor = "transparent"; }}
                style={{
                  display: "flex", alignItems: "center", gap: "10px", padding: "10px 12px",
                  borderRadius: "8px", cursor: "pointer", marginBottom: "2px",
                  backgroundColor: conv.id === activeId ? "#1a1a1a" : "transparent",
                  position: "relative",
                }}
              >
                <div
                  style={{
                    width: "28px", height: "28px", borderRadius: "50%",
                    backgroundColor: conv.id === activeId ? "#ff7a33" : "#2a2a2a",
                    display: "flex", alignItems: "center", justifyContent: "center",
                    fontSize: "11px", fontWeight: 600, flexShrink: 0, color: "#fff",
                  }}
                >
                  {(conv.title || "N")[0].toUpperCase()}
                </div>
                <div style={{ flex: 1, minWidth: 0 }}>
                  <div style={{ fontSize: "13px", fontWeight: 500, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                    {conv.title}
                  </div>
                  <div style={{ fontSize: "11px", color: "#555" }}>
                    {conv.messages.length > 0 ? `${conv.messages.length} messages` : "Empty"}
                  </div>
                </div>
                <button
                  onClick={(e) => deleteConv(conv.id, e)}
                  style={{
                    background: "none", border: "none", color: "#555", cursor: "pointer",
                    fontSize: "14px", padding: "4px", borderRadius: "4px", flexShrink: 0, opacity: 0,
                    transition: "opacity 0.15s",
                  }}
                  onMouseOver={(e) => { e.currentTarget.style.color = "#ff4444"; e.currentTarget.style.opacity = "1"; }}
                  onMouseOut={(e) => { e.currentTarget.style.color = "#555"; e.currentTarget.style.opacity = "0"; }}
                  onFocus={(e) => e.currentTarget.style.opacity = "1"}
                  onBlur={(e) => e.currentTarget.style.opacity = "0"}
                >
                  ✕
                </button>
              </div>
            ))
          )}
        </div>

        <div
          onClick={() => setUserMenuOpen(!userMenuOpen)}
          style={{
            padding: "12px 16px", borderTop: "1px solid #2a2a2a", display: "flex",
            alignItems: "center", gap: "12px", cursor: "pointer", position: "relative",
          }}
          onMouseOver={(e) => (e.currentTarget.style.backgroundColor = "#1a1a1a")}
          onMouseOut={(e) => (e.currentTarget.style.backgroundColor = "transparent")}
        >
          <div
            style={{
              width: "32px", height: "32px", borderRadius: "50%",
              backgroundColor: "#2a2a2a", display: "flex", alignItems: "center",
              justifyContent: "center", fontSize: "14px", fontWeight: 600, flexShrink: 0,
              backgroundImage: email ? `url(${gravatarUrl(email)})` : "none",
              backgroundSize: "cover",
            }}
          >
            {!email && (username[0] || "U").toUpperCase()}
          </div>
          <div style={{ flex: 1, minWidth: 0 }}>
            <div style={{ fontSize: "13px", fontWeight: 500, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
              {username}
            </div>
            <div style={{ fontSize: "12px", color: "#666" }}>{tier.toLowerCase()} plan</div>
          </div>

          {userMenuOpen && (
            <div
              ref={menuRef}
              style={{
                position: "absolute", bottom: "100%", left: "16px", right: "16px",
                backgroundColor: "#1a1a1a", border: "1px solid #2a2a2a", borderRadius: "10px",
                padding: "16px", zIndex: 100, boxShadow: "0 4px 20px rgba(0,0,0,0.4)",
              }}
              onClick={(e) => e.stopPropagation()}
            >
              <div style={{ display: "flex", alignItems: "center", gap: "12px", marginBottom: "12px" }}>
                <img
                  src={gravatarUrl(email)}
                  alt=""
                  style={{ width: "40px", height: "40px", borderRadius: "50%", backgroundColor: "#2a2a2a" }}
                />
                <div>
                  <div style={{ fontSize: "14px", fontWeight: 600 }}>{username}</div>
                  <div style={{ fontSize: "12px", color: "#999" }}>{email}</div>
                </div>
              </div>
              <div style={{ fontSize: "12px", color: "#666", paddingTop: "8px", borderTop: "1px solid #2a2a2a" }}>
                {tier.toUpperCase()} plan
              </div>
            </div>
          )}
        </div>
      </div>

      <div
        style={{
          flex: 1, display: "flex", flexDirection: "column", backgroundColor: "#1a1a1a", minWidth: 0,
        }}
      >
        <div
          style={{
            padding: "12px 24px", borderBottom: "1px solid #2a2a2a",
            display: "flex", alignItems: "center", gap: "12px",
          }}
        >
          {!sidebarOpen && (
            <button
              onClick={() => setSidebarOpen(true)}
              style={{ background: "none", border: "none", color: "#999", cursor: "pointer", fontSize: "20px", padding: 0 }}
            >
              ☰
            </button>
          )}
          <div style={{ fontSize: "14px", fontWeight: 500, marginRight: "16px" }}>Rta Chat</div>
          <a href="/" style={{ color: "#999", fontSize: "13px", textDecoration: "none", marginRight: "12px" }}
            onMouseOver={(e) => (e.target.style.color = "#fff")}
            onMouseOut={(e) => (e.target.style.color = "#999")}
          >
            Home
          </a>
          <a href="/dashboard" style={{ color: "#999", fontSize: "13px", textDecoration: "none" }}
            onMouseOver={(e) => (e.target.style.color = "#fff")}
            onMouseOut={(e) => (e.target.style.color = "#999")}
          >
            Dashboard
          </a>
          <div style={{ flex: 1 }} />
        </div>

        <div style={{ flex: 1, overflowY: "auto", display: "flex", flexDirection: "column" }}>
          {!activeConv ? (
            <div style={{ flex: 1, display: "flex", alignItems: "center", justifyContent: "center", color: "#555" }}>
              Select a conversation or start a new one
            </div>
          ) : !hasUserMessages ? (
            <div
              style={{
                flex: 1, display: "flex", flexDirection: "column", alignItems: "center",
                justifyContent: "center", textAlign: "center", padding: "40px 24px",
              }}
            >
              <div style={{ fontSize: "28px", fontWeight: 600, marginBottom: "8px", color: "#fff" }}>
                {getGreeting()}, {username}
              </div>
              <div style={{ fontSize: "14px", color: "#666", maxWidth: "400px" }}>
                I'm Rta. Ask me anything about coding, debugging, or building software.
              </div>
            </div>
          ) : (
            <div style={{ padding: "24px 24px 0", flex: 1, maxWidth: "800px", width: "100%", margin: "0 auto" }}>
              {messages.map((msg, idx) => (
                <div
                  key={idx}
                  style={{
                    display: "flex", gap: "12px", marginBottom: "20px",
                    justifyContent: msg.role === "user" ? "flex-end" : "flex-start",
                  }}
                >
                  <div
                    style={{
                      display: "flex", gap: "12px", maxWidth: "85%",
                      flexDirection: msg.role === "user" ? "row-reverse" : "row",
                      alignItems: "flex-start",
                    }}
                  >
                    <div
                      style={{
                        width: "28px", height: "28px", borderRadius: "50%",
                        backgroundColor: msg.role === "user" ? "#ff7a33" : "#2a2a2a",
                        display: "flex", alignItems: "center", justifyContent: "center",
                        fontSize: "12px", fontWeight: 600, flexShrink: 0, color: "#fff",
                      }}
                    >
                      {msg.role === "user" ? (username[0] || "U").toUpperCase() : "R"}
                    </div>
                    <div style={{ display: "flex", flexDirection: "column", gap: "4px", maxWidth: "100%" }}>
                      <div
                        style={{
                          padding: "10px 16px",
                          backgroundColor: msg.role === "user" ? "#2a2a2a" : "transparent",
                          borderRadius: "12px", fontSize: "15px", lineHeight: 1.6, color: "#fff",
                          maxWidth: "100%", wordBreak: "break-word",
                        }}
                      >
                        {msg.role === "assistant" ? (
                          <div class="chat-markdown" dangerouslySetInnerHTML={{ __html: DOMPurify.sanitize(marked.parse(msg.content)) }} />
                        ) : (
                          <div style={{ whiteSpace: "pre-wrap" }}>{msg.content}</div>
                        )}
                      </div>
                      {msg.role === "assistant" && (
                        <button
                          onClick={() => navigator.clipboard.writeText(msg.content)}
                          style={{
                            alignSelf: "flex-start", background: "none", border: "none",
                            color: "#555", cursor: "pointer", fontSize: "12px", padding: "2px 4px",
                            borderRadius: "4px",
                          }}
                          onMouseOver={(e) => (e.target.style.color = "#999")}
                          onMouseOut={(e) => (e.target.style.color = "#555")}
                        >
                          Copy
                        </button>
                      )}
                    </div>
                  </div>
                </div>
              ))}
              {isTyping && (
                <div style={{ display: "flex", gap: "12px", marginBottom: "20px" }}>
                  <div
                    style={{
                      width: "28px", height: "28px", borderRadius: "50%",
                      backgroundColor: "#2a2a2a", display: "flex", alignItems: "center",
                      justifyContent: "center", fontSize: "12px", fontWeight: 600, flexShrink: 0, color: "#fff",
                    }}
                  >
                    R
                  </div>
                  <div style={{ color: "#999", fontSize: "14px", padding: "10px 0" }}>Thinking...</div>
                </div>
              )}
              <div ref={messagesEndRef} />
            </div>
          )}
        </div>

        <div
          style={{
            padding: "16px 24px 24px", borderTop: "1px solid #2a2a2a",
            display: "flex", flexDirection: "column", gap: "8px", alignItems: "center",
          }}
        >
          <div
            style={{
              display: "flex", gap: "8px", alignItems: "flex-end", maxWidth: "800px", width: "100%",
            }}
          >
            <textarea
              ref={inputRef}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Message Rta..."
              style={{
                flex: 1, padding: "14px 16px", backgroundColor: "#2a2a2a",
                border: "1px solid #3a3a3a", borderRadius: "12px", color: "#fff",
                fontSize: "15px", fontFamily: "inherit", resize: "none",
                minHeight: "52px", maxHeight: "200px", outline: "none",
              }}
              disabled={isTyping}
            />
            <button
              onClick={handleSend}
              disabled={isTyping || !input.trim()}
              style={{
                padding: "14px 20px",
                backgroundColor: isTyping || !input.trim() ? "#3a3a3a" : "#ff7a33",
                border: "none", borderRadius: "10px", color: "#fff",
                cursor: isTyping || !input.trim() ? "not-allowed" : "pointer",
                fontSize: "16px", fontWeight: 600, transition: "background 0.2s",
              }}
            >
              ↑
            </button>
          </div>
          <div style={{ fontSize: "12px", color: "#555" }}>
            Rta can make mistakes. Verify important information.
          </div>
        </div>
      </div>
    </div>
    </Fragment>
  );
};

export default ChatInterface;
