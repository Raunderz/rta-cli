import { h } from 'preact';
import { useState } from 'preact/hooks';
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

export function ChatPanel() {
  const [isLoggedIn, setIsLoggedIn] = useState(() => !!localStorage.getItem("rta_api_key"));
  const [apiKey, setApiKey] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [userInfo, setUserInfo] = useState(null);
  const [messages, setMessages] = useState([]);
  const [inputValue, setInputValue] = useState("");
  const [isTyping, setIsTyping] = useState(false);

  const handleLogin = async (e) => {
    e.preventDefault();
    if (!apiKey.trim()) {
      setError("Please enter your API key");
      return;
    }

    setLoading(true);
    setError("");

    try {
      const res = await fetch(`${API_BASE_URL}/v1/auth/me`, {
        method: "GET",
        headers: getHeaders(apiKey),
      });

      if (res.status === 200) {
        const data = await res.json();
        localStorage.setItem("rta_api_key", apiKey);
        setIsLoggedIn(true);
        setUserInfo(data);
      } else if (res.status === 401) {
        setError("Invalid API key");
      } else {
        setError(`Server error (${res.status})`);
      }
    } catch (err) {
      setError("Cannot connect to server");
    } finally {
      setLoading(false);
    }
  };

  const handleLogout = () => {
    localStorage.removeItem("rta_api_key");
    setIsLoggedIn(false);
    setApiKey("");
    setUserInfo(null);
    setMessages([]);
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

  if (!isLoggedIn) {
    return (
      <div className="h-full flex flex-col bg-[#1e1e1e] border-r border-[#3c3c3c]">
        <div className="p-4 border-b border-[#3c3c3c]">
          <div className="flex items-center gap-2 mb-4">
            <img src={iconImage} alt="RTA" className="w-6 h-6" />
            <span className="text-[#cccccc] font-semibold">RTA</span>
          </div>
        </div>
        
        <div className="flex-1 flex items-center justify-center p-4">
          <form onSubmit={handleLogin} className="w-full max-w-[200px]">
            <p className="text-[#858585] text-xs mb-3 text-center">Enter your API key to continue</p>
            <input
              type="password"
              value={apiKey}
              onInput={(e) => setApiKey(e.target.value)}
              placeholder="API Key"
              className="w-full px-3 py-2 bg-[#2d2d2d] border border-[#3c3c3c] rounded text-[#cccccc] text-sm placeholder-[#6b6b6b] focus:outline-none focus:border-[#007acc] mb-2"
              disabled={loading}
            />
            {error && <p className="text-[#f14c4c] text-xs mb-2">{error}</p>}
            <button
              type="submit"
              disabled={loading}
              className="w-full px-3 py-2 bg-[#0e639c] hover:bg-[#1177bb] text-white rounded text-sm font-medium transition-colors disabled:opacity-50"
            >
              {loading ? "..." : "Login"}
            </button>
            <p className="text-[#6b6b6b] text-xs mt-3 text-center">
              Get key at rta-three.vercel.app
            </p>
          </form>
        </div>
      </div>
    );
  }

  return (
    <div className="h-full flex flex-col bg-[#1e1e1e] border-r border-[#3c3c3c]">
      {/* Header */}
      <div className="flex items-center justify-between px-3 py-2 border-b border-[#3c3c3c]">
        <div className="flex items-center gap-2">
          <img src={iconImage} alt="RTA" className="w-5 h-5" />
          <span className="text-[#cccccc] font-medium text-sm">RTA</span>
        </div>
        <button 
          onClick={handleLogout}
          className="text-[#858585] hover:text-[#cccccc] text-xs px-2 py-1 rounded hover:bg-[#2d2d2d]"
        >
          Logout
        </button>
      </div>

      {/* User info */}
      <div className="px-3 py-2 border-b border-[#3c3c3c]">
        <p className="text-[#858585] text-xs">
          {userInfo?.email || "User"} · {userInfo?.tier || "free"}
        </p>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-3 space-y-3">
        {messages.length === 0 && (
          <p className="text-[#6b6b6b] text-sm text-center mt-8">
            Chat with AI to edit files, run commands, and more.
          </p>
        )}
        {messages.map((msg, i) => (
          <div key={i} className={`${msg.role === "user" ? "ml-8" : "mr-4"}`}>
            <div className={`px-3 py-2 rounded text-sm ${
              msg.role === "user" 
                ? "bg-[#2d4f7c] text-[#cccccc]" 
                : "bg-[#2d2d2d] text-[#d4d4d4]"
            }`}>
              {msg.content}
            </div>
          </div>
        ))}
        {isTyping && (
          <div className="mr-4">
            <div className="px-3 py-2 rounded text-sm bg-[#2d2d2d] text-[#6b6b6b]">
              Thinking...
            </div>
          </div>
        )}
      </div>

      {/* Input */}
      <div className="p-3 border-t border-[#3c3c3c]">
        <div className="flex gap-2">
          <input
            type="text"
            value={inputValue}
            onInput={(e) => setInputValue(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && !e.shiftKey && handleSendMessage()}
            placeholder="Ask AI..."
            className="flex-1 px-3 py-2 bg-[#2d2d2d] border border-[#3c3c3c] rounded text-[#cccccc] text-sm placeholder-[#6b6b6b] focus:outline-none focus:border-[#007acc]"
            disabled={isTyping}
          />
          <button
            onClick={handleSendMessage}
            disabled={isTyping || !inputValue.trim()}
            className="px-3 py-2 bg-[#0e639c] hover:bg-[#1177bb] text-white rounded text-sm disabled:opacity-50"
          >
            Send
          </button>
        </div>
      </div>
    </div>
  );
}