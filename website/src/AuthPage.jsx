import { useState, useRef, useEffect } from 'preact/hooks';
import { Link } from 'wouter';
import { useHead } from './useHead';

const API_BASE_URL = import.meta.env.VITE_BACKEND_URL || "https://rta-tb0k.onrender.com";

export const AuthPage = () => {
  useHead({ title: "Account", description: "Login or create your Rta account." });
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
    <div class="container" style="padding-top: clamp(100px, 15vh, 140px); padding-bottom: 80px;">
      <div class="auth-box">
        <h2 style="margin-bottom: 2rem; text-align: center; font-size: 1.5rem;">{isLogin ? "Welcome back" : "Create account"}</h2>

        <div style="background: var(--primary-light); border: 1px solid var(--primary); border-radius: var(--radius-sm); padding: 12px 16px; margin-bottom: 24px;">
          <p style="font-size: 0.85rem; color: var(--primary); margin: 0; line-height: 1.5; font-weight: 500;">
            GitHub authentication is recommended for CLI integration.
          </p>
        </div>

        {authError && <div style="color: var(--red); margin-bottom: 1rem; font-size: 14px; padding: 10px; border: 1px solid var(--red); border-radius: var(--radius-sm); background: var(--red-soft);">{authError}</div>}

        <button class="btn" style="width: 100%; margin-bottom: 1.5rem;" onClick={() => window.location.href = `${API_BASE_URL}/v1/auth/github`}>
          {isLogin ? "Continue with GitHub" : "Sign up with GitHub"}
        </button>

        {isLogin && (
          <>
            <div style="display: flex; align-items: center; gap: 1rem; margin-bottom: 1.5rem; opacity: 0.4;">
              <div style="flex: 1; height: 1px; background: var(--border);"></div>
              <span style="font-size: 0.75rem; color: var(--text-muted);">or</span>
              <div style="flex: 1; height: 1px; background: var(--border);"></div>
            </div>

            <form class="auth-form" onSubmit={handleAuth}>
              <input type="email" name="email" class="auth-input" placeholder="Email" required />
              <input type="password" name="password" class="auth-input" placeholder="Password" required />
              <div ref={captchaRef} class="h-captcha" data-sitekey="51b06ce2-0f58-4148-8fec-b2944c54e718" style="margin-bottom: 1rem;"></div>
              <button type="submit" class="btn btn-primary" style="width: 100%;" disabled={isLoading}>
                {isLoading ? "Processing..." : "Login"}
              </button>
            </form>
          </>
        )}

        <div style="margin-top: 2rem; text-align: center;">
          <a href="#" class="nav-link" onClick={e => { e.preventDefault(); setIsLogin(!isLogin); setAuthError(""); }}>
            {isLogin ? "No account? Sign up" : "Have an account? Login"}
          </a>
        </div>
      </div>
    </div>
  );
};
