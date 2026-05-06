import van from "vanjs-core"

const { div, h1, h2, h3, h4, p, img, main, section, a, button, pre, li, span, form, input, svg, path, nav, ul, footer, table, tr, th, td, tbody, thead } = van.tags

const API_BASE_URL = import.meta.env.VITE_BACKEND_URL || "http://localhost:8000"

// --- State Management ---
const getInitialPage = () => {
    const path = window.location.pathname.slice(1)
    const validPages = ["home", "pricing", "roadmap", "status", "releases", "auth", "legal", "privacy"]
    return validPages.includes(path) ? path : "home"
}

const currentPage = van.state(getInitialPage())
const authMode = van.state("login")
const currency = van.state("INR")
const user = van.state(JSON.parse(localStorage.getItem("rta_user") || "null"))
const authError = van.state("")
const isLoading = van.state(false)
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

const handleAuth = async (e, type) => {
    e.preventDefault()
    authError.val = ""
    isLoading.val = true

    const formData = new FormData(e.target)
    const data = Object.fromEntries(formData.entries())

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
    }, { threshold: 0.1 })
    observer.observe(el)
}

// --- Components ---

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

const Navbar = () => {
    const menuOpen = van.state(false)
    return nav({},
        div({ class: "container nav-container" },
            a({ 
                href: "/", 
                class: "logo", 
                onclick: (e) => { 
                    e.preventDefault(); 
                    currentPage.val = "home"; 
                    window.history.pushState({}, "", "/");
                    window.scrollTo(0, 0);
                } 
            }, "rta"),
            button({ 
                class: "nav-toggle", 
                onclick: () => menuOpen.val = !menuOpen.val,
                children: () => [span({}), span({}), span({})]
            }),
            div({ class: () => `nav-links ${menuOpen.val ? 'open' : ''}` },
                NavLink("Pricing", "pricing"),
                NavLink("Roadmap", "roadmap"),
                NavLink("Status", "status"),
                NavLink("Releases", "releases"),
                () => user.val ? a({ href: "/dashboard.html", class: "nav-link active" }, "Dashboard") : NavLink("Account", "auth")
            )
        )
    )
}

const Hero = () => {
    const el = section({ class: "container hero" },
        div({ class: "hero-content" },
            h1({ class: "hero-headline animate-fade-up", style: "animation-delay: 0.1s;" }, "Build faster."),
            h2({ class: "hero-subheadline gradient-text animate-fade-up", style: "animation-delay: 0.2s;" }, "Everywhere."),
            p({ class: "description hero-description animate-fade-up", style: "animation-delay: 0.3s;" }, 
                "Rta is a high-performance developer toolkit designed for mobile-first precision. Efficient code editing and automation for modern engineering teams."
            ),
            div({ class: "cta-group animate-fade-up", style: "animation-delay: 0.4s;" },
                a({ class: "btn btn-primary", href: "#", onclick: (e) => { e.preventDefault(); currentPage.val = "auth" } }, "Get Started Free"),
                a({ class: "btn btn-secondary", href: "#", onclick: (e) => { e.preventDefault(); currentPage.val = "releases" } }, "Download CLI")
            )
        ),
        div({ class: "hero-visual animate-fade-up", style: "animation-delay: 0.5s;" },
            div({ style: "text-align: center; opacity: 0.5;" },
                svg({ width: "64", height: "64", viewBox: "0 0 24 24", fill: "none", stroke: "var(--accent)", "stroke-width": "1.5" },
                    path({ d: "M21 12a9 9 0 11-18 0 9 9 0 0118 0z" }),
                    path({ d: "M15.91 11.672a.375.375 0 010 .656l-5.603 3.113a.375.375 0 01-.557-.328V8.887c0-.286.307-.466.557-.327l5.603 3.112z" })
                ),
                p({ class: "mono", style: "margin-top: 1rem; color: var(--accent);" }, "Watch Demo")
            )
        )
    )
    return el
}

const FeaturesSection = () => {
    const features = [
        { 
            icon: "🔀", 
            title: "Native Git", 
            desc: "Pure mobile Git implementation.",
            bullets: ["No proxies, just performance", "Full git compatibility", "Works offline"]
        },
        { 
            icon: "✨", 
            title: "AI Assisted", 
            desc: "Context-aware code generation.",
            bullets: ["Understands your codebase", "Intelligent refactoring", "Zero learning curve"]
        },
        { 
            icon: "⚡", 
            title: "Local First", 
            desc: "Lightning fast with zero round-trips.",
            bullets: ["Sub-millisecond response", "Works anywhere", "Privacy first"]
        }
    ]

    const el = section({ class: "container" },
        div({ class: "section-header" },
            h2({ class: "section-title" }, "Engineered for Performance"),
            p({ class: "description section-description" }, "Experience the power of a desktop environment in the palm of your hand.")
        ),
        div({ class: "features-grid" },
            features.map((f, i) => div({ class: "feature-card", style: `animation-delay: ${i * 0.15}s;` },
                div({ class: "feature-icon" }, f.icon),
                h3({ class: "feature-title" }, f.title),
                p({ class: "feature-description" }, f.desc),
                ul({ class: "feature-bullets" },
                    f.bullets.map(b => li({}, b))
                )
            ))
        ),
        div({ class: "features-cta" },
            p({}, "Want to see RTA in action?"),
            a({ class: "btn btn-primary", href: "#", onclick: (e) => { e.preventDefault(); currentPage.val = "auth" } }, "Get Started Free")
        )
    )
    reveal(el)
    return el
}

const CTASection = () => {
    const el = section({ class: "cta-section" },
        div({ class: "container" },
            h2({}, "Ready to elevate your workflow?"),
            p({ class: "description" }, "Join thousands of developers building the future with Rta. Available now for Linux, Windows, and Android."),
            div({ class: "cta-group", style: "justify-content: center;" },
                a({ class: "btn btn-primary", href: "#", onclick: (e) => { e.preventDefault(); currentPage.val = "auth" } }, "Create Free Account"),
                a({ class: "btn btn-secondary", href: "#", onclick: (e) => { e.preventDefault(); currentPage.val = "releases" } }, "View Releases")
            )
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
            features: ["10 Daily AI Calls", "25k Context (Monthly)", "Standard Support", "Core Editor Access"] 
        },
        { 
            name: "Basic", 
            featured: true,
            price: () => priceMap[currency.val].basic, 
            features: ["50 Daily AI Calls", "100k Context (Monthly)", "Priority Support", "Advanced CLI Tools", "Early Access Features"] 
        },
        { 
            name: "Pro", 
            price: () => priceMap[currency.val].pro, 
            features: ["100 Daily AI Calls", "1M Context (Monthly)", "24/7 Dedicated Support", "Enterprise CLI Suite", "Custom Model Tuning"] 
        }
    ]

    const el = section({ class: "container", style: "padding-top: 160px;" },
        div({ class: "section-header" },
            h2({ class: "section-title" }, "Simple, transparent pricing"),
            p({ class: "description section-description" }, "Choose the plan that fits your development workflow. No hidden fees.")
        ),
        div({ style: "display: flex; justify-content: center; gap: 1rem; margin-bottom: 4rem;" },
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
                button({ 
                    class: `btn ${tier.featured ? 'btn-primary' : 'btn-secondary'}`, 
                    style: "width: 100%;" 
                }, "Select Plan")
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

    const el = section({ class: "container", style: "padding-top: 160px;" },
        div({ class: "section-header" },
            h2({ class: "section-title" }, "Roadmap"),
            p({ class: "description section-description" }, "Our journey toward the perfect developer toolkit.")
        ),
        div({ class: "features-grid" },
            phases.map(p => div({ class: "feature-card" },
                span({ class: "mono", style: "color: var(--accent); opacity: 0.8;" }, p.tag),
                h3({ class: "feature-title", style: "margin-top: 1rem;" }, p.title),
                ul({ class: "feature-bullets", style: "margin-top: 1rem;" },
                    p.items.map(i => li({}, i))
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

    const el = section({ class: "container", style: "padding-top: 160px;" },
        div({ class: "section-header" },
            h2({ class: "section-title" }, "System Status"),
            p({ class: "description section-description" }, "Real-time telemetry and system integrity.")
        ),
        div({ class: "status-card", style: "max-width: 600px; margin: 0 auto;" },
            () => statusData.val.loading ? p({ class: "text-center mono" }, "Scanning systems...") : div({},
                div({ style: "display: flex; justify-content: space-between; align-items: center; margin-bottom: 2rem; padding-bottom: 1.5rem; border-bottom: 1px solid var(--dark-border);" },
                    h3({ style: "margin: 0;" }, "Global Status"),
                    span({ 
                        style: `font-size: 12px; font-weight: 700; font-family: var(--font-mono); padding: 4px 12px; border-radius: 100px; background: ${statusData.val.status === 'operational' ? 'rgba(16, 185, 129, 0.1)' : 'rgba(239, 68, 68, 0.1)'}; color: ${statusData.val.status === 'operational' ? 'var(--success)' : '#EF4444'}` 
                    }, statusData.val.status.toUpperCase())
                ),
                Object.entries(statusData.val.services).map(([name, status]) => div({ class: "status-row" },
                    span({ class: "description", style: "text-transform: capitalize;" }, name),
                    span({ 
                        style: `font-weight: 600; font-size: 14px; color: ${status === 'operational' ? 'var(--success)' : '#EF4444'}` 
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
    const el = section({ class: "container", style: "padding-top: 160px;" },
        div({ class: "section-header" },
            h2({ class: "section-title" }, "Download CLI"),
            p({ class: "description section-description" }, "Get the latest version of Rta for your platform.")
        ),
        div({ style: "display: flex; justify-content: center; gap: 1rem; margin-bottom: 4rem;" },
            button({ class: () => `btn ${selectedOS.val === 'linux' ? 'btn-primary' : 'btn-secondary'}`, onclick: () => selectedOS.val = 'linux' }, "Linux"),
            button({ class: () => `btn ${selectedOS.val === 'windows' ? 'btn-primary' : 'btn-secondary'}`, onclick: () => selectedOS.val = 'windows' }, "Windows")
        ),
        div({ class: "status-card", style: "max-width: 800px; margin: 0 auto;" },
            div({ style: "display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 2rem; margin-bottom: 3rem;" },
                div({},
                    h3({ style: "margin-bottom: 0.5rem;" }, "Stable Release"),
                    p({ class: "mono", style: "opacity: 0.5; font-size: 12px;" }, "v1.4.2 — Latest stable")
                ),
                () => selectedOS.val === 'linux' ? a({ href: "/rta", class: "btn btn-primary", download: "rta" }, "Download for Linux") : 
                a({ href: "/rta.exe", class: "btn btn-primary", download: "rta.exe" }, "Download for Windows")
            ),
            h4({ class: "mono", style: "margin-bottom: 1.5rem; font-size: 12px; color: var(--accent);" }, "Quick Install"),
            pre({ 
                style: "background: rgba(0,0,0,0.3); padding: 1.5rem; border-radius: 8px; border: 1px solid var(--dark-border); font-family: var(--font-mono); color: var(--text-secondary); font-size: 14px; overflow-x: auto; line-height: 1.6;" 
            }, () => selectedOS.val === 'linux' ? "chmod +x rta\nsudo mv rta /usr/local/bin/\nrta chat" : "rta.exe chat")
        )
    )
    reveal(el, true)
    return main({}, el)
}

const AuthPage = () => {
    const isLogin = () => authMode.val === "login"

    const el = section({ class: "container", style: "padding-top: 160px;" },
        div({ style: "display: flex; justify-content: center;" },
            div({ class: "status-card", style: "width: 100%; max-width: 440px;" },
                div({ class: "text-center mb-8" },
                    h2({ style: "margin-bottom: 1rem;" }, () => isLogin() ? "Welcome Back" : "Create Account"),
                    () => authError.val ? p({ style: "color: #EF4444; font-size: 14px; background: rgba(239, 68, 68, 0.1); padding: 1rem; border-radius: 8px;" }, authError.val) : ""
                ),
                button({ 
                    class: "btn btn-secondary", 
                    style: "width: 100%; margin-bottom: 2rem;",
                    onclick: () => window.location.href = `${API_BASE_URL}/v1/auth/github`
                }, "Continue with GitHub"),
                div({ style: "display: flex; align-items: center; gap: 1rem; margin-bottom: 2rem; opacity: 0.2;" },
                    div({ style: "flex: 1; height: 1px; background: var(--text-primary);" }),
                    span({ class: "mono", style: "font-size: 12px;" }, "OR"),
                    div({ style: "flex: 1; height: 1px; background: var(--text-primary);" })
                ),
                form({ onsubmit: (e) => handleAuth(e, authMode.val) },
                    () => !isLogin() ? div({ style: "margin-bottom: 1rem;" }, 
                        input({ name: "username", style: "width:100%; background:var(--dark-primary); border:1px solid var(--dark-border); padding:12px; border-radius:8px; color:white; font-family:var(--font-body);", placeholder: "Username", required: true })
                    ) : "",
                    div({ style: "margin-bottom: 1rem;" }, 
                        input({ name: "email", style: "width:100%; background:var(--dark-primary); border:1px solid var(--dark-border); padding:12px; border-radius:8px; color:white; font-family:var(--font-body);", type: "email", placeholder: "Email", required: true })
                    ),
                    div({ style: "margin-bottom: 1.5rem;" }, 
                        input({ name: "password", style: "width:100%; background:var(--dark-primary); border:1px solid var(--dark-border); padding:12px; border-radius:8px; color:white; font-family:var(--font-body);", type: "password", placeholder: "Password", required: true })
                    ),
                    div({ class: "h-captcha", "data-sitekey": "51b06ce2-0f58-4148-8fec-b2944c54e718", style: "margin-bottom: 1.5rem;" }),
                    button({ 
                        class: "btn btn-primary", 
                        style: "width: 100%;",
                        disabled: isLoading
                    }, () => isLoading.val ? "Processing..." : (isLogin() ? "Login" : "Sign Up"))
                ),
                div({ class: "text-center", style: "margin-top: 2rem;" },
                    a({ 
                        href: "#", 
                        class: "nav-link", 
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

const LegalPage = () => {
    const el = section({ class: "container", style: "padding-top: 160px;" },
        div({ style: "max-width: 800px; margin: 0 auto;" },
            h2({ style: "margin-bottom: 3rem;" }, "Terms of Service"),
            div({ class: "description", style: "display: flex; flex-direction: column; gap: 2rem;" },
                div({},
                    h3({ style: "font-size: 20px; margin-bottom: 1rem;" }, "1. Acceptance of Terms"),
                    p({}, "By accessing Rta, you agree to be bound by these terms. If you disagree with any part, you may not access our services.")
                ),
                div({},
                    h3({ style: "font-size: 20px; margin-bottom: 1rem;" }, "2. Subscription & Payments"),
                    p({}, "Billing is processed via secure payment gateways. Subscriptions renew automatically unless cancelled. All fees are non-refundable except as required by law.")
                ),
                div({},
                    h3({ style: "font-size: 20px; margin-bottom: 1rem;" }, "3. License & Restrictions"),
                    p({}, "We grant you a personal, non-exclusive license to use Rta. You may not reverse engineer or attempt to extract source code.")
                )
            )
        )
    )
    reveal(el, true)
    return main({}, el)
}

const PrivacyPage = () => {
    const el = section({ class: "container", style: "padding-top: 160px;" },
        div({ style: "max-width: 800px; margin: 0 auto;" },
            h2({ style: "margin-bottom: 3rem;" }, "Privacy Policy"),
            div({ class: "description", style: "display: flex; flex-direction: column; gap: 2rem;" },
                div({},
                    h3({ style: "font-size: 20px; margin-bottom: 1rem;" }, "1. Information Collection"),
                    p({}, "We collect email addresses and basic telemetry to provide services and improve performance. No private code is ever stored on our servers.")
                ),
                div({},
                    h3({ style: "font-size: 20px; margin-bottom: 1rem;" }, "2. Payment Processing"),
                    p({}, "Payment data is handled exclusively by PCI-compliant third-party processors. We do not store credit card information.")
                )
            )
        )
    )
    reveal(el, true)
    return main({}, el)
}

const AppFooter = () => footer({ class: "footer" },
    div({ class: "container" },
        div({ class: "footer-content" },
            div({ class: "footer-column" },
                a({ href: "/", class: "logo" }, "rta"),
                p({ style: "margin-top: 1.5rem; font-size: 14px; color: var(--text-secondary);" }, 
                    "The high-performance developer toolkit for the next era of computing."
                )
            ),
            div({ class: "footer-column" },
                h4({}, "Platform"),
                NavLink("Pricing", "pricing"),
                NavLink("Roadmap", "roadmap"),
                NavLink("Status", "status"),
                NavLink("Releases", "releases")
            ),
            div({ class: "footer-column" },
                h4({}, "Resources"),
                a({ href: "#", class: "nav-link" }, "Documentation"),
                a({ href: "/waitlist.html", class: "nav-link" }, "Waitlist"),
                a({ href: "#", class: "nav-link" }, "Community")
            ),
            div({ class: "footer-column" },
                h4({}, "Legal"),
                NavLink("Privacy", "privacy"),
                NavLink("Terms", "legal"),
                a({ href: "#", class: "nav-link" }, "Contact")
            )
        ),
        div({ class: "footer-bottom" },
            p({}, "© 2026 Rta Software — All Rights Reserved"),
            div({ style: "display: flex; gap: 2rem;" },
                a({ href: "#", class: "nav-link" }, "Twitter"),
                a({ href: "#", class: "nav-link" }, "GitHub")
            )
        )
    )
)

// --- App Entry Point ---

const App = () => div({ id: "app" },
    Navbar(),
    () => {
        if (currentPage.val === "auth") {
            setTimeout(() => {
                const container = document.querySelector('.h-captcha');
                if (container && window.hcaptcha) {
                    try { window.hcaptcha.render(container); } catch (e) {}
                }
            }, 100);
        }

        switch (currentPage.val) {
            case "home": return div({}, Hero(), FeaturesSection(), CTASection())
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
