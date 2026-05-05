import van from "vanjs-core"

const { div, h1, h2, h3, p, img, main, section, a, button, pre, li, span, form, input, svg, path, nav, ul, footer, table, tr, th, td, tbody, thead } = van.tags

const API_BASE_URL = import.meta.env.VITE_BACKEND_URL || "http://localhost:8000"

// --- State Management ---
const getInitialPage = () => {
    const path = window.location.pathname.slice(1)
    const validPages = ["home", "pricing", "roadmap", "status", "releases", "auth"]
    return validPages.includes(path) ? path : "home"
}

const currentPage = van.state(getInitialPage())
const authMode = van.state("login") // Added back
const currency = van.state("INR")
const user = van.state(JSON.parse(localStorage.getItem("rta_user") || "null"))
const authError = van.state("") // Added back
const isLoading = van.state(false) // Added back
const statusData = van.state({ loading: true, status: "Checking", services: {} })

const priceMap = {
    INR: { free: "₹0", basic: "₹75", pro: "₹299" },
    USD: { free: "$0", basic: "$1.49", pro: "$4.49" }
}

// --- Auth Helpers ---
const saveUser = (userData) => {
    user.val = userData
    localStorage.setItem("rta_user", JSON.stringify(userData))
    window.location.href = "/dashboard.html"
}

const logout = () => {
    user.val = null
    localStorage.removeItem("rta_user")
    currentPage.val = "home"
    window.history.pushState({ page: "home" }, "", "/")
}

const handleAuth = async (e, type) => {
    e.preventDefault()
    authError.val = ""
    isLoading.val = true

    const formData = new FormData(e.target)
    const data = Object.fromEntries(formData.entries())

    // Get hCaptcha token
    const captchaToken = window.hcaptcha ? window.hcaptcha.getResponse() : "test_token"
    if (!captchaToken && import.meta.env.PROD) {
        authError.val = "Please complete the captcha."
        isLoading.val = false
        return
    }

    data.captcha_token = captchaToken

    try {
        const endpoint = type === "signup" ? "/v1/auth/signup" : "/v1/auth/login"
        const res = await fetch(`${API_BASE_URL}${endpoint}`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(data)
        })

        const result = await res.json()
        if (!res.ok) throw new Error(result.detail || "Authentication failed")

        if (type === "signup") {
            authMode.val = "login"
            authError.val = "Signup successful! Please log in."
        } else {
            saveUser(result)
        }
    } catch (err) {
        authError.val = err.message
    } finally {
        isLoading.val = false
        if (window.hcaptcha) window.hcaptcha.reset()
    }
}

// --- Global Mouse Tracking (throttled, disabled on touch) ---
let ticking = false
const isTouchDevice = () => 'ontouchstart' in window || navigator.maxTouchPoints > 0

if (!isTouchDevice()) {
    window.addEventListener('mousemove', (e) => {
        if (ticking) return
        ticking = true
        requestAnimationFrame(() => {
            const cards = document.querySelectorAll('.bento-item, .pricing-card, .status-card')
            cards.forEach(card => {
                const rect = card.getBoundingClientRect()
                if (rect.width === 0 || rect.height === 0) return
                const x = ((e.clientX - rect.left) / rect.width) * 100
                const y = ((e.clientY - rect.top) / rect.height) * 100
                card.style.setProperty('--x', `${x}%`)
                card.style.setProperty('--y', `${y}%`)
            })
            ticking = false
        })
    })
}

// --- Animation Engine ---
const reveal = (el, immediate = false) => {
    el.setAttribute('data-reveal', '')
    if (immediate) {
        requestAnimationFrame(() => { el.classList.add('visible') })
        return
    }
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('visible')
                observer.unobserve(entry.target)
            }
        })
    }, { threshold: 0.01 })
    observer.observe(el)
}

const Icon = (d, size = "16") => svg({ width: size, height: size, viewBox: "0 0 24 24", fill: "none", stroke: "currentColor", "stroke-width": "2", "stroke-linecap": "round", "stroke-linejoin": "round" }, path({ d }))

const GifPlaceholder = () => {
    return div({ class: "gif-placeholder" },
        div({ class: "gif-placeholder-inner" },
            svg({ 
                class: "gif-placeholder-icon",
                viewBox: "0 0 24 24", 
                fill: "none", 
                stroke: "currentColor", 
                "stroke-width": "1.5" 
            }, 
                path({ d: "M21 12a9 9 0 11-18 0 9 9 0 0118 0z" }),
                path({ d: "M15.91 11.672a.375.375 0 010 .656l-5.603 3.113a.375.375 0 01-.557-.328V8.887c0-.286.307-.466.557-.327l5.603 3.112z" })
            ),
            p({ style: "font-family: var(--font-mono); font-size: 11px; text-transform: uppercase; letter-spacing: 0.2em;" }, "Visual Preview Placeholder")
        )
    )
}

const LegalPage = () => {
    const el = section({ class: "container", style: "padding-top: 160px; padding-bottom: 120px;" },
        div({ class: "mb-16", style: "max-width: 800px;" },
            span({ class: "mono" }, "Legal Framework"),
            h2({ class: "mt-6 mb-8" }, "Terms of Service"),
            div({ class: "description", style: "font-size: 14px; display: flex; flex-direction: column; gap: 24px;" },
                div({},
                    h3({ style: "color: var(--text); margin-bottom: 12px; font-size: 16px;" }, "1. Acceptance of Terms"),
                    p({}, "By accessing Rta, you agree to be bound by these terms. If you disagree with any part, you may not access our services.")
                ),
                div({},
                    h3({ style: "color: var(--text); margin-bottom: 12px; font-size: 16px;" }, "2. Subscription & Payments"),
                    p({}, "Billing is processed via secure payment gateways. Subscriptions renew automatically unless cancelled. All fees are non-refundable except as required by law.")
                ),
                div({},
                    h3({ style: "color: var(--text); margin-bottom: 12px; font-size: 16px;" }, "3. License & Restrictions"),
                    p({}, "We grant you a personal, non-exclusive license to use Rta. You may not reverse engineer or attempt to extract source code.")
                ),
                div({},
                    h3({ style: "color: var(--text); margin-bottom: 12px; font-size: 16px;" }, "4. Limitation of Liability"),
                    p({}, "Rta is provided 'as is'. We are not liable for any indirect, incidental, or consequential damages arising from your use of the software.")
                )
            )
        )
    )
    reveal(el, true)
    return main({}, el)
}

const PrivacyPage = () => {
    const el = section({ class: "container", style: "padding-top: 160px; padding-bottom: 120px;" },
        div({ class: "mb-16", style: "max-width: 800px;" },
            span({ class: "mono" }, "Data Protection"),
            h2({ class: "mt-6 mb-8" }, "Privacy Policy"),
            div({ class: "description", style: "font-size: 14px; display: flex; flex-direction: column; gap: 24px;" },
                div({},
                    h3({ style: "color: var(--text); margin-bottom: 12px; font-size: 16px;" }, "1. Information Collection"),
                    p({}, "We collect email addresses and basic telemetry to provide services and improve performance. No private code is ever stored on our servers.")
                ),
                div({},
                    h3({ style: "color: var(--text); margin-bottom: 12px; font-size: 16px;" }, "2. Payment Processing"),
                    p({}, "Payment data is handled exclusively by PCI-compliant third-party processors. We do not store credit card information.")
                ),
                div({},
                    h3({ style: "color: var(--text); margin-bottom: 12px; font-size: 16px;" }, "3. Third-Party Sharing"),
                    p({}, "We do not sell your data. Information is shared only with essential service providers (e.g., auth, billing) to maintain functionality.")
                )
            )
        )
    )
    reveal(el, true)
    return main({}, el)
}

// --- Shared Components ---
const Navbar = () => nav({},
    div({ class: "container nav-container" },
        a({ href: "/", class: "logo", onclick: (e) => { e.preventDefault(); currentPage.val = "home"; window.history.pushState({}, "", "/") } }, "rta"),
        div({ class: "nav-links" },
            NavLink("Pricing", "pricing"),
            NavLink("Roadmap", "roadmap"),
            NavLink("Status", "status"),
            NavLink("Releases", "releases"),
            () => user.val ? a({ href: "/dashboard.html", class: "nav-link active" }, "Dashboard") : NavLink("Account", "auth")
        )
    )
)

const NavLink = (text, page) => a({
    href: `#/${page}`,
    class: () => `nav-link ${currentPage.val === page ? "active" : ""}`,
    onclick: (e) => { 
        e.preventDefault()
        currentPage.val = page
        window.history.pushState({ page }, "", `/${page}`)
        window.scrollTo(0, 0)
    }
}, text)

const AppFooter = () => footer({},
    div({ class: "container footer-grid" },
        div({},
            a({ href: "/", class: "logo" }, "rta"),
            p({ style: "margin-top: 24px; font-size: 14px; max-width: 240px; color: var(--text-muted);" }, 
                "The high-performance developer toolkit for the next era of computing."
            )
        ),
        div({},
            p({ class: "mono", style: "margin-bottom: 24px;" }, "Platform"),
            div({ style: "display: flex; flex-direction: column; gap: 12px;" },
                NavLink("Pricing", "pricing"),
                NavLink("Roadmap", "roadmap"),
                NavLink("Status", "status")
            )
        ),
        div({},
            p({ class: "mono", style: "margin-bottom: 24px;" }, "Resources"),
            div({ style: "display: flex; flex-direction: column; gap: 12px;" },
                a({ href: "#", class: "nav-link" }, "Documentation"),
                a({ href: "/waitlist.html", class: "nav-link" }, "Waitlist"),
                a({ href: "#", class: "nav-link" }, "Contact")
            )
        )
    ),
    div({ class: "container footer-bottom" },
        p({}, "© 2026 Rta Software — All Rights Reserved"),
        div({ style: "display: flex; gap: 32px;" },
            NavLink("Privacy", "privacy"),
            NavLink("Terms", "legal")
        )
    )
)

// --- Page Components ---

const Hero = () => {
    const el = section({ class: "container hero" },
        div({ class: "hero-content" },
            h1({ class: "text-balance" }, "Build faster. ", span({}, "Everywhere.")),
            p({ class: "description" }, "Rta is a high-performance code editor for Android and a powerful CLI for Linux and Windows. Designed for mobile-first precision."),
            div({ style: "display: flex; gap: 16px; margin-top: 48px;" },
                a({ class: "btn btn-primary", href: "#", onclick: (e) => { e.preventDefault(); currentPage.val = "auth" } }, "Get Started"),
                a({ class: "btn btn-secondary", href: "#", onclick: (e) => { e.preventDefault(); currentPage.val = "releases" } }, "Download CLI")
            )
        ),
        GifPlaceholder()
    )
    reveal(el, true)
    return el
}

const Capabilities = () => {
    const items = [
        { title: "Native Git", desc: "Pure mobile Git implementation. No proxies, just performance." },
        { title: "AI Assisted", desc: "Context-aware code generation and refactoring built-in." },
        { title: "Local First", desc: "Lightning fast execution with zero round-trip latency." }
    ]

    const el = section({ class: "container", style: "padding-top: 0; padding-bottom: 120px;" },
        div({ class: "bento-grid" },
            items.map(item => div({ class: "bento-item" },
                h3({}, item.title),
                p({ class: "description", style: "font-size: 14px;" }, item.desc)
            ))
        )
    )
    reveal(el)
    return el
}

const PricingPage = () => {
    const tiers = [
        { 
            name: "Starter", 
            price: () => priceMap[currency.val].free, 
            features: ["10 Daily AI Calls", "25k Monthly Tokens", "Standard Support", "Core Editor Access"] 
        },
        { 
            name: "Basic", 
            featured: true,
            price: () => priceMap[currency.val].basic, 
            features: ["200 Daily AI Calls", "500k Monthly Tokens", "Priority Support", "Advanced CLI Tools", "Early Access Features"] 
        },
        { 
            name: "Pro", 
            price: () => priceMap[currency.val].pro, 
            features: ["1000 Daily AI Calls", "5M Monthly Tokens", "24/7 Dedicated Support", "Enterprise CLI Suite", "Custom Model Tuning"] 
        }
    ]

    const el = section({ class: "container", style: "padding-top: 160px; padding-bottom: 120px;" },
        div({ class: "text-center mb-12", style: "max-width: 700px; margin: 0 auto;" },
            h2({ class: "mb-12 text-balance" }, "Simple, transparent pricing for teams"),
            p({ class: "description text-center" }, "Choose the plan that fits your development workflow. No hidden fees, just raw performance.")
        ),
        div({ style: "display: flex; justify-content: center; gap: 12px; margin-bottom: 64px;" },
            button({ class: () => `btn ${currency.val === "INR" ? "btn-primary" : "btn-secondary"}`, onclick: () => currency.val = "INR" }, "INR"),
            button({ class: () => `btn ${currency.val === "USD" ? "btn-primary" : "btn-secondary"}`, onclick: () => currency.val = "USD" }, "USD")
        ),
        div({ class: "pricing-grid" },
            tiers.map(tier => div({ class: `pricing-card ${tier.featured ? 'featured' : ''}` },
                div({ class: "pricing-tier" }, tier.name),
                div({ class: "pricing-price" }, tier.price(), span({}, "/ month")),
                ul({ class: "pricing-features" },
                    tier.features.map(f => li({}, f))
                ),
                button({ class: `btn ${tier.featured ? 'btn-primary' : 'btn-secondary'}`, style: "width: 100%; border-radius: 16px;" }, "Select Plan")
            ))
        )
    )
    reveal(el, true)
    return main({}, el)
}

const RoadmapPage = () => {
    const phases = [
        { title: "Phase 1", tag: "Active", items: ["Core CLI v1.0", "Auth & Telemetry", "Project Indexing"] },
        { title: "Phase 2", tag: "Soon", items: ["Public Beta", "Context Sync", "AI Refactor Engine"] },
        { title: "Phase 3", tag: "Future", items: ["Mobile App (iOS/Android)", "Desktop Sync", "Native Git Core"] }
    ]

    const el = section({ class: "container", style: "padding-top: 160px; padding-bottom: 120px;" },
        div({ class: "mb-16", style: "max-width: 600px;" },
            span({ class: "mono" }, "Development Path"),
            h2({ class: "mt-6 text-balance" }, "Our journey toward the perfect developer toolkit"),
        ),
        div({ class: "bento-grid" },
            phases.map(p => div({ class: "bento-item" },
                div({},
                    span({ class: "mono", style: "opacity: 0.5;" }, p.tag),
                    h3({ class: "mt-6", style: "color: var(--text);" }, p.title),
                    ul({ style: "list-style: none; margin-top: 32px; display: flex; flex-direction: column; gap: 16px;" },
                        p.items.map(i => li({ style: "font-size: 14px; color: var(--text-muted); display: flex; align-items: center; gap: 12px;" }, 
                            span({ style: "width: 4px; height: 4px; border-radius: 50%; background: var(--border-hover);" }),
                            i
                        ))
                    )
                )
            ))
        )
    )
    reveal(el, true)
    return main({}, el)
}

const StatusPage = () => {
    const checkStatus = async () => {
        try {
            const res = await fetch(`${API_BASE_URL}/v1/status`, { headers: { "ngrok-skip-browser-warning": "true" } })
            const data = await res.json()
            statusData.val = { loading: false, ...data }
        } catch {
            statusData.val = { loading: false, status: "Offline", services: { api: "Unavailable" } }
        }
    }
    checkStatus()

    const el = section({ class: "container", style: "padding-top: 160px; padding-bottom: 120px;" },
        div({ class: "text-center mb-16" }, // Increased mb-12 to mb-16
            span({ class: "mono" }, "Real-time Telemetry"),
            h2({ class: "mt-6" }, "System Integrity")
        ),
        div({ class: "status-card", style: "max-width: 540px; margin: 0 auto;" },
            () => statusData.val.loading ? div({ class: "text-center" }, p({ class: "mono" }, "Scanning...")) : div({},
                div({ style: "display: flex; justify-content: space-between; align-items: center; margin-bottom: 40px; padding-bottom: 24px; border-bottom: 1px solid var(--border);" },
                    h3({ style: "margin: 0; color: var(--text);" }, "Global Status"),
                    span({ 
                        style: `font-size: 11px; font-weight: 700; font-family: var(--font-mono); padding: 4px 12px; border-radius: 100px; background: ${statusData.val.status === 'operational' ? 'rgba(16, 185, 129, 0.1)' : 'rgba(239, 68, 68, 0.1)'}; color: ${statusData.val.status === 'operational' ? '#10B981' : '#EF4444'}` 
                    }, statusData.val.status.toUpperCase())
                ),
                Object.entries(statusData.val.services).map(([name, status]) => div({ class: "status-row" },
                    span({ style: "color: var(--text-muted); font-size: 13px; text-transform: capitalize;" }, name),
                    span({ 
                        style: `font-weight: 600; font-size: 13px; color: ${status === 'operational' ? '#10B981' : '#EF4444'}` 
                    }, status.toUpperCase())
                ))
            )
        )
    )
    reveal(el, true)
    return main({}, el)
}

const ReleasesPage = () => {
    const selectedOS = van.state("linux")
    const el = section({ class: "container", style: "padding-top: 160px; padding-bottom: 120px;" },
        div({ class: "text-center mb-16" }, // Increased mb-12 to mb-16
            span({ class: "mono" }, "Distribution"),
            h2({ class: "mt-6" }, "Download CLI")
        ),
        div({ class: "text-center" },
            div({ style: "display: flex; justify-content: center; gap: 12px; margin-bottom: 64px;" }, // Increased mb-48 to mb-64
                button({ class: () => `btn ${selectedOS.val === 'linux' ? 'btn-primary' : 'btn-secondary'}`, onclick: () => selectedOS.val = 'linux' }, "Linux"),
                button({ class: () => `btn ${selectedOS.val === 'windows' ? 'btn-primary' : 'btn-secondary'}`, onclick: () => selectedOS.val = 'windows' }, "Windows")
            ),
            div({ class: "status-card", style: "max-width: 720px; text-align: left; padding: 48px; margin: 0 auto;" },
                div({ style: "display: flex; justify-content: space-between; align-items: center; margin-bottom: 48px;" },
                    div({},
                        h3({ style: "color: var(--text); margin-bottom: 8px;" }, "Stable Release"),
                        p({ class: "mono", style: "font-size: 10px; opacity: 0.5;" }, "v1.4.2 — Latest stable")
                    ),
                    () => selectedOS.val === 'linux' ? a({ href: "/rta", class: "btn btn-primary", download: "rta" }, "Download for Linux") : 
                    a({ href: "/rta.exe", class: "btn btn-primary", download: "rta.exe" }, "Download for Windows")
                ),
                h3({ class: "mb-6", style: "font-size: 12px; color: var(--text);" }, "Quick Install"),
                pre({ 
                    style: "background: rgba(0,0,0,0.3); padding: 24px; border-radius: 16px; border: 1px solid var(--border); font-family: var(--font-mono); color: var(--text-muted); font-size: 13px; overflow-x: auto; line-height: 1.6;" 
                }, () => selectedOS.val === 'linux' ? "chmod +x rta\nsudo mv rta /usr/local/bin/\nrta chat" : "rta.exe chat")
            )
        )
    )
    reveal(el, true)
    return main({}, el)
}

const AuthPage = () => {
    const isLogin = () => authMode.val === "login"

    const el = section({ class: "container", style: "padding-top: 160px; padding-bottom: 120px;" },
        div({ style: "display: flex; justify-content: center;" },
            div({ class: "status-card", style: "width: 100%; max-width: 440px; padding: 48px;" },
                div({ class: "text-center mb-10" },
                    span({ class: "mono" }, "Access Control"),
                    h2({ class: "mt-4 text-balance", style: "font-size: 28px;" }, () => isLogin() ? "Login" : "Sign Up"),
                    () => authError.val ? p({ style: "color: #EF4444; font-size: 13px; margin-top: 16px; background: rgba(239, 68, 68, 0.1); padding: 12px; border-radius: 8px;" }, authError.val) : ""
                ),
                div({ class: "mb-8" },
                    button({ 
                        class: "btn btn-secondary", 
                        style: "width: 100%; display: flex; align-items: center; justify-content: center; gap: 12px; border-radius: 12px; padding: 14px;",
                        onclick: () => window.location.href = `${API_BASE_URL}/v1/auth/github`
                    }, 
                        svg({ width: "20", height: "20", viewBox: "0 0 24 24", fill: "currentColor" },
                            path({ d: "M12 0c-6.626 0-12 5.373-12 12 0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.042-1.416-4.042-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23.957-.266 1.983-.399 3.003-.404 1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576 4.765-1.589 8.199-6.086 8.199-11.386 0-6.627-5.373-12-12-12z" })
                        ),
                        "Continue with GitHub"
                    )
                ),
                div({ style: "display: flex; align-items: center; gap: 16px; margin-bottom: 32px; opacity: 0.3;" },
                    div({ style: "flex: 1; height: 1px; background: var(--text);" }),
                    span({ style: "font-size: 11px; font-family: var(--font-mono);" }, "OR"),
                    div({ style: "flex: 1; height: 1px; background: var(--text);" })
                ),
                form({ onsubmit: (e) => handleAuth(e, authMode.val) },
                    () => !isLogin() ? div({ class: "mb-4" }, 
                        input({ name: "username", style: "width:100%; background:rgba(255,255,255,0.02); border:1px solid var(--border); padding:14px; border-radius:12px; color:var(--text); font-family:var(--font-main);", placeholder: "Username", required: true })
                    ) : "",
                    div({ class: "mb-4" }, 
                        input({ name: "email", style: "width:100%; background:rgba(255,255,255,0.02); border:1px solid var(--border); padding:14px; border-radius:12px; color:var(--text); font-family:var(--font-main);", type: "email", placeholder: "Email", required: true })
                    ),
                    div({ class: "mb-6" }, 
                        input({ name: "password", style: "width:100%; background:rgba(255,255,255,0.02); border:1px solid var(--border); padding:14px; border-radius:12px; color:var(--text); font-family:var(--font-main);", type: "password", placeholder: "Password", required: true })
                    ),
                    div({ class: "hcaptcha-container", style: "margin-bottom: 24px; min-height: 78px;" },
                        div({ class: "h-captcha", "data-sitekey": "51b06ce2-0f58-4148-8fec-b2944c54e718" })
                    ),
                    button({ 
                        class: "btn btn-primary", 
                        style: "width: 100%; border-radius: 12px; padding: 14px;",
                        disabled: isLoading
                    }, () => isLoading.val ? "Processing..." : (isLogin() ? "Login" : "Sign Up"))
                ),
                div({ class: "text-center mt-10" },
                    a({ 
                        href: "#", 
                        class: "nav-link", 
                        style: "font-size: 13px;",
                        onclick: (e) => { 
                            e.preventDefault()
                            authMode.val = isLogin() ? "signup" : "login" 
                            authError.val = ""
                        }
                    }, () => isLogin() ? "Don't have an account? Sign up" : "Already have an account? Login")
                )
            )
        )
    )
    reveal(el, true)
    return main({}, el)
}

// --- App Entry Point ---

const App = () => div({ id: "app" },
    Navbar(),
    () => {
        // Handle hCaptcha rendering
        if (currentPage.val === "auth") {
            setTimeout(() => {
                const container = document.querySelector('.h-captcha');
                if (container && window.hcaptcha) {
                    try { window.hcaptcha.render(container); } catch (e) {}
                }
            }, 100);
        }

        switch (currentPage.val) {
            case "home": return div({}, Hero(), Capabilities())
            case "pricing": return PricingPage()
            case "roadmap": return RoadmapPage()
            case "status": return StatusPage()
            case "releases": return ReleasesPage()
            case "auth": return AuthPage()
            case "legal": return LegalPage()
            case "privacy": return PrivacyPage()
            default: return Hero()
        }
    },
    AppFooter()
)

van.add(document.body, App())
