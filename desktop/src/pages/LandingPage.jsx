import { h } from 'preact';
import { useState } from 'preact/hooks';
import backgroundImage from '../assets/background.png';
import iconImage from '../assets/icon.png';

const API_BASE_URL = "https://divisive-herbs-jolly.ngrok-free.dev";
const CLI_VERSION = "0.2.0";

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
    "X-CLI-Version": CLI_VERSION,
    "ngrok-skip-browser-warning": "69420",
    "User-Agent": "rta-desktop/1.0",
  };
}

export function LandingPage() {
  const [isLoggedIn, setIsLoggedIn] = useState(() => !!localStorage.getItem("rta_api_key"));
  const [apiKey, setApiKey] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [userInfo, setUserInfo] = useState(null);

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
        setError("Invalid API key. Please check and try again.");
      } else {
        setError(`Server error (${res.status}). Please try again later.`);
      }
    } catch (err) {
      setError("Cannot connect to server. Check your connection.");
    } finally {
      setLoading(false);
    }
  };

  const handleLogout = () => {
    localStorage.removeItem("rta_api_key");
    setIsLoggedIn(false);
    setApiKey("");
    setUserInfo(null);
  };

  if (isLoggedIn) {
    return (
      <div className="app-container min-h-screen flex items-center justify-center p-4">
        <div className="glass-panel w-full max-w-2xl p-12 md:p-16 text-center">
          <div className="animate-fade-in">
            <img 
              src={iconImage} 
              alt="RTA Logo" 
              className="w-24 h-24 mx-auto mb-8 drop-shadow-2xl"
            />
          </div>
          
          <h1 className="animate-fade-in text-4xl md:text-5xl font-extrabold text-white mb-4 tracking-widest">
            RTA Desktop
          </h1>
          
          <div className="animate-fade-in-delay mb-8">
            <div className="glass-card px-6 py-4 inline-block">
              <p className="text-white/80 text-lg">Logged in</p>
              <p className="text-white/50 text-sm">{userInfo?.email || "User"}</p>
              <p className="text-white/40 text-xs">Tier: {userInfo?.tier || "free"}</p>
            </div>
          </div>

          <p className="animate-fade-in-delay-2 text-white/50 text-lg max-w-md mx-auto leading-relaxed">
            Desktop app is under development. In the meantime, use the CLI for Rta operations.
          </p>

          <button 
            onClick={handleLogout}
            className="animate-fade-in-delay-2 mt-8 px-6 py-2 bg-red-600/20 hover:bg-red-600/40 text-red-400 rounded-lg transition-colors"
          >
            Sign Out
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="app-container min-h-screen flex items-center justify-center p-4">
      <div className="glass-panel w-full max-w-2xl p-12 md:p-16 text-center">
        <div className="animate-fade-in">
          <img 
            src={iconImage} 
            alt="RTA Logo" 
            className="w-24 h-24 mx-auto mb-8 drop-shadow-2xl"
          />
        </div>
        
        <h1 className="animate-fade-in text-4xl md:text-5xl font-extrabold text-white mb-4 tracking-widest">
          RTA
        </h1>
        
        <div className="animate-fade-in-delay">
          <div className="flex items-center justify-center gap-3 mb-6">
            <div className="h-px w-12 bg-gradient-to-r from-transparent via-white/40 to-transparent"></div>
            <span className="text-white/60 text-lg font-medium uppercase tracking-wider">API Key Entry</span>
            <div className="h-px w-12 bg-gradient-to-r from-transparent via-white/40 to-transparent"></div>
          </div>
        </div>
        
        <p className="animate-fade-in-delay-2 text-white/50 text-sm max-w-md mx-auto mb-8">
          Enter your Rta API key to continue. Get your key from the dashboard.
        </p>

        <form onSubmit={handleLogin} className="animate-fade-in-delay-2 max-w-sm mx-auto">
          <input
            type="password"
            value={apiKey}
            onInput={(e) => setApiKey(e.target.value)}
            placeholder="Enter your Rta API key"
            className="w-full px-4 py-3 bg-white/5 border border-white/10 rounded-lg text-white placeholder-white/30 focus:outline-none focus:border-white/30 mb-4"
            disabled={loading}
          />
          
          {error && (
            <p className="text-red-400 text-sm mb-4">{error}</p>
          )}
          
          <button
            type="submit"
            disabled={loading}
            className="w-full px-6 py-3 bg-[#ff3333]/20 hover:bg-[#ff3333]/40 text-[#ff3333] font-medium rounded-lg transition-colors disabled:opacity-50"
          >
            {loading ? "Validating..." : "Login"}
          </button>
        </form>

        <p className="animate-fade-in-delay-2 text-white/30 text-xs mt-8">
          Get your API key at <span className="underline">https://rta-three.vercel.app/dashboard.html</span>
        </p>
      </div>
    </div>
  );
}
