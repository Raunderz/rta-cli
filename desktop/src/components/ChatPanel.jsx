import { h } from 'preact';
import { useState, useEffect } from 'preact/hooks';
import iconImage from '../assets/icon.png';

function getDeviceId() {
  let deviceId = localStorage.getItem("rta_device_id");
  if (!deviceId) {
    deviceId = "desktop-" + Math.random().toString(36).substring(2, 15);
    localStorage.setItem("rta_device_id", deviceId);
  }
  return deviceId;
}

function getHeaders(apiKey) {
  return {
    "X-API-KEY": apiKey,
    "X-Device-ID": getDeviceId(),
    "X-CLI-Version": "0.2.0",
    "ngrok-skip-browser-warning": "69420",
    "User-Agent": "rta-desktop/1.0",
  };
}

const API_BASE_URL = "https://divisive-herbs-jolly.ngrok-free.dev";

const SendIcon = () => (
  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <line x1="22" y1="2" x2="11" y2="13"></line>
    <polygon points="22 2 15 22 11 13 2 9 22 2"></polygon>
  </svg>
);

const UserIcon = () => (
  <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path>
    <circle cx="12" cy="7" r="4"></circle>
  </svg>
);

export function ChatPanel() {
  const [userInfo, setUserInfo] = useState(null);
  const [messages, setMessages] = useState([]);
  const [inputValue, setInputValue] = useState("");
  const [isTyping, setIsTyping] = useState(false);

  useEffect(() => {
    const fetchUser = async () => {
      const apiKey = localStorage.getItem("rta_api_key");
      if (!apiKey) return;
      try {
        const res = await fetch(`${API_BASE_URL}/v1/auth/me`, {
          method: "GET",
          headers: getHeaders(apiKey),
        });
        if (res.status === 200) {
          const data = await res.json();
          setUserInfo(data);
        }
      } catch (err) {
        console.error("Failed to fetch user info", err);
      }
    };
    fetchUser();
  }, []);

  const handleLogout = () => {
    localStorage.removeItem("rta_api_key");
    // App.jsx will detect this and switch to LandingPage
  };

  const handleSendMessage = () => {
    if (!inputValue.trim() || isTyping) return;
    
    const userMsg = inputValue.trim();
    setInputValue("");
    
    setMessages(prev => [...prev, { role: "user", content: userMsg }]);
    setIsTyping(true);
    
    setTimeout(() => {
      setMessages(prev => [...prev, { 
        role: "assistant", 
        content: "This is a demo. Backend integration coming soon. You can type to test the UI." 
      }]);
      setIsTyping(false);
    }, 1000);
  };

  return (
    <div className="h-full flex flex-col bg-[#0c0c0e] border-r border-white/10">
      {/* Header */}
      <div className="flex items-center justify-between px-5 py-4 border-b border-white/10 bg-[#141417]">
        <div className="flex items-center gap-2.5">
          <img src={iconImage} alt="RTA" className="w-6 h-6 rounded shadow-sm" />
          <span className="text-zinc-100 font-semibold text-sm tracking-tight">RTA</span>
        </div>
        <button 
          onClick={handleLogout}
          className="text-zinc-400 hover:text-zinc-100 text-xs px-2.5 py-1.5 rounded-md hover:bg-zinc-800 transition-colors font-medium"
        >
          Logout
        </button>
      </div>

      {/* User info */}
      <div className="px-5 py-3 border-b border-white/10 bg-[#141417]/50">
        <div className="flex items-center gap-2 text-zinc-400 text-[11px] uppercase tracking-wider font-bold">
          <div className="text-zinc-300"><UserIcon /></div>
          <span>{userInfo?.email || "Anonymous"} · {userInfo?.tier || "free"}</span>
        </div>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-5 space-y-5 scrollbar-thin">
        {messages.length === 0 && (
          <div className="flex flex-col items-center justify-center h-full text-center space-y-4">
            <div className="w-12 h-12 bg-zinc-900 rounded-2xl flex items-center justify-center border border-white/10 shadow-inner text-zinc-400">
              <SendIcon />
            </div>
            <div className="space-y-1">
              <p className="text-zinc-200 font-medium">Ready to assist</p>
              <p className="text-zinc-400 text-xs max-w-[200px] mx-auto leading-relaxed">
                Ask me to edit files, run commands, or explain code.
              </p>
            </div>
          </div>
        )}
        {messages.map((msg, i) => (
          <div key={i} className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}>
            <div className={`max-w-[85%] px-4 py-2.5 rounded-2xl text-[13px] leading-relaxed shadow-md ${
              msg.role === "user" 
                ? "bg-blue-600 text-white rounded-tr-none" 
                : "bg-zinc-800 text-zinc-100 border border-white/5 rounded-tl-none"
            }`}>
              {msg.content}
            </div>
          </div>
        ))}
        {isTyping && (
          <div className="flex justify-start">
            <div className="bg-zinc-800 text-zinc-400 px-4 py-2.5 rounded-2xl rounded-tl-none border border-white/5 text-[13px] italic flex items-center gap-2">
              <span className="w-1.5 h-1.5 bg-zinc-500 rounded-full animate-bounce"></span>
              <span className="w-1.5 h-1.5 bg-zinc-500 rounded-full animate-bounce [animation-delay:0.2s]"></span>
              <span className="w-1.5 h-1.5 bg-zinc-500 rounded-full animate-bounce [animation-delay:0.4s]"></span>
            </div>
          </div>
        )}
      </div>

      {/* Input */}
      <div className="p-4 border-t border-white/10 bg-[#141417]">
        <div className="relative group">
          <input
            type="text"
            value={inputValue}
            onInput={(e) => setInputValue(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && !e.shiftKey && handleSendMessage()}
            placeholder="Ask anything..."
            className="w-full pl-4 pr-12 py-3 bg-zinc-900 border border-zinc-700 rounded-xl text-zinc-100 text-sm placeholder-zinc-500 focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500/50 transition-all shadow-inner"
            disabled={isTyping}
          />
          <button
            onClick={handleSendMessage}
            disabled={isTyping || !inputValue.trim()}
            className="absolute right-2 top-1.5 p-1.5 bg-zinc-100 hover:bg-white text-zinc-950 rounded-lg transition-all disabled:opacity-0 disabled:scale-95 scale-100 opacity-100 shadow-lg active:scale-95"
          >
            <SendIcon />
          </button>
        </div>
      </div>
    </div>
  );
}