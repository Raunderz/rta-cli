import { h } from 'preact';
import { useState } from 'preact/hooks';

export function LandingPage() {
  const [apiKey, setApiKey] = useState('');

  const handleLogin = () => {
    if (apiKey.trim()) {
      localStorage.setItem("rta_api_key", apiKey.trim());
      // App will detect and switch
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900 flex items-center justify-center p-4">
      <div className="max-w-md w-full space-y-8">
        <div className="text-center">
          <div className="mx-auto h-12 w-12 bg-white rounded-lg flex items-center justify-center">
            <span className="text-2xl font-bold text-gray-900">RTA</span>
          </div>
          <h2 className="mt-6 text-3xl font-bold text-white">Welcome to RTA Desktop</h2>
          <p className="mt-2 text-sm text-gray-400">
            Enter your API key to get started
          </p>
        </div>
        <div className="space-y-4">
          <input
            type="password"
            value={apiKey}
            onInput={(e) => setApiKey(e.target.value)}
            placeholder="API Key"
            className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm placeholder-gray-400 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
          />
          <button
            onClick={handleLogin}
            className="w-full flex justify-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
          >
            Login
          </button>
        </div>
      </div>
    </div>
  );
}