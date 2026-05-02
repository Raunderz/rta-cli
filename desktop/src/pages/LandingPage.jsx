import { h } from 'preact';
import { useState } from 'preact/hooks';
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
  const [apiKey, setApiKey] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

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
        localStorage.setItem("rta_api_key", apiKey);
        // App.jsx will detect this change and switch to MainLayout
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

  return (
    <div className="app-container min-h-[100dvh] flex items-center justify-center p-6 bg-[#09090b]">
      <div className="glass-panel w-full max-w-md p-10 md:p-12 rounded-[2.5rem] shadow-2xl relative overflow-hidden group">
        <div className="absolute top-0 left-0 right-0 h-1 bg-gradient-to-r from-blue-500 via-purple-500 to-blue-500 opacity-50" />
        
        <div className="flex flex-col items-center text-center space-y-8">
          <div className="animate-float w-20 h-20 rounded-3xl bg-zinc-900 border border-white/5 flex items-center justify-center shadow-2xl">
            <img src={iconImage} alt="RTA Logo" className="w-12 h-12 rounded-xl" />
          </div>
          
          <div className="space-y-3">
            <h1 className="text-3xl md:text-4xl font-bold tracking-tight text-white">
              Connect to RTA
            </h1>
            <p className="text-zinc-500 text-sm max-w-[280px] mx-auto leading-relaxed">
              Enter your secure API key to unlock the power of Rta Desktop.
            </p>
          </div>

          <form onSubmit={handleLogin} className="w-full space-y-4">
            <div className="relative group">
              <input
                type="password"
                value={apiKey}
                onInput={(e) => setApiKey(e.target.value)}
                placeholder="Secure API Key"
                className="w-full px-5 py-4 bg-zinc-900 border border-zinc-800 rounded-2xl text-zinc-100 placeholder-zinc-600 focus:outline-none focus:ring-4 focus:ring-blue-500/10 focus:border-blue-500/50 transition-all text-sm"
                disabled={loading}
              />
            </div>
            
            {error && (
              <p className="text-red-400 text-xs font-medium px-2 animate-pulse">{error}</p>
            )}
            
            <button
              type="submit"
              disabled={loading}
              className="w-full px-6 py-4 bg-zinc-100 hover:bg-white text-zinc-950 font-bold rounded-2xl transition-all shadow-lg active:scale-[0.98] disabled:opacity-50"
            >
              {loading ? "Establishing connection..." : "Access Dashboard"}
            </button>
          </form>

          <div className="pt-4">
            <p className="text-zinc-600 text-xs">
              Need a key? Visit <a href="https://rta-three.vercel.app" target="_blank" className="text-zinc-400 hover:text-zinc-200 underline underline-offset-4 decoration-zinc-700 transition-colors">the dashboard</a>
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
