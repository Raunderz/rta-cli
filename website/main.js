import van from "vanjs-core"

const { div, h1, h2, h3, p, img, main, section, a, button, pre, li, span, form, input } = van.tags

const API_BASE_URL = import.meta.env.VITE_BACKEND_URL || "http://localhost:8000"

// State for current page
const currentPage = van.state("home")
const currency = van.state("INR")
const authMode = van.state("login") // "login" or "signup"
const user = van.state(JSON.parse(localStorage.getItem("rta_user") || "null"))
const authError = van.state("")
const isLoading = van.state(false)
const dashboardTheme = van.state(localStorage.getItem("rta_dash_theme") || "light")

const priceMap = {
    INR: { basic: "₹75", pro: "₹299" },
    USD: { basic: "$1.49", pro: "$4.49" }
}

// Auth Helpers
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

// Parallax logic
const setupParallax = () => {
    let ticking = false;
    window.addEventListener('mousemove', (e) => {
        if (!ticking) {
            window.requestAnimationFrame(() => {
                const x = (e.clientX / window.innerWidth - 0.5) * 2;
                const y = (e.clientY / window.innerHeight - 0.5) * 2;
                document.body.style.setProperty('--mx', `${x.toFixed(2)}`);
                document.body.style.setProperty('--my', `${y.toFixed(2)}`);
                ticking = false;
            });
            ticking = true;
        }
    });
}

const NavLink = (text, page) => {
    if (page === "dashboard") {
        return a({
            href: "/dashboard.html",
            class: "nav-link"
        }, text)
    }
    return a({
        href: `#/${page}`,
        class: "nav-link",
        onclick: (e) => {
            e.preventDefault()
            currentPage.val = page
            window.history.pushState({ page }, "", `/${page}`)
            window.scrollTo(0, 0)
        }
    }, text)
}

const Footer = () => div({ class: "footer-links" },
    NavLink("pricing", "pricing"),
    NavLink("roadmap", "roadmap"),
    NavLink("privacy", "privacy"),
    NavLink("terms", "terms"),
    () => user.val ? NavLink("dashboard", "dashboard") : NavLink("sign in", "auth"),
    p({ class: "footer-line" }, "Coming Soon — October 2026")
)

const HomePage = () => {
    return main({ class: "container" },
        section({ class: "hero" },
            div({ class: "title-container" },
                h1({ class: "app-name" }, "rta"),
                p({ class: "description" },
                    "a mobile-first, ai-assisted code editor for android. built for speed, precision, and surgical development on the go."
                ),
                div({ class: "cta-container" },
                    () => !user.val ? a({
                        class: "waitlist-btn",
                        href: "#/auth",
                        onclick: (e) => {
                            e.preventDefault()
                            currentPage.val = "auth"
                            window.history.pushState({ page: "auth" }, "", "/auth")
                        }
                    }, "get started") : a({
                        class: "waitlist-btn",
                        href: "/dashboard.html"
                    }, "open dashboard"),
                    a({
                        class: "release-link-btn",
                        href: "#/releases",
                        onclick: (e) => {
                            e.preventDefault()
                            currentPage.val = "releases"
                            window.history.pushState({ page: "releases" }, "", "/releases")
                        }
                    }, "get rta cli (linux)")
                )
            ),
            div({ class: "logo-container" },
                img({ class: "logo", src: "/assets/icon.png", alt: "Rta Icon" })
            )
        ),
        section({ class: "features-grid" },
            div({ class: "feature-card" },
                h3({}, "Surgical AI"),
                p({}, "Real-time AI assistance tuned for mobile constraints. Code faster with surgical precision.")
            ),
            div({ class: "feature-card" },
                h3({}, "Git Native"),
                p({}, "Full version control in your pocket. Commit, push, and pull without ever leaving the editor.")
            ),
            div({ class: "feature-card" },
                h3({}, "Cloud Sync"),
                p({}, "Sync your workspaces and API keys across devices. Move from CLI to Mobile seamlessly.")
            )
        ),
        Footer()
    )
}

const PricingPage = () => {
    return div({ class: "content-page" },
        NavLink("← back to home", "home"),
        h1({ class: "page-title" }, "Pricing Plans"),
        div({ class: "currency-selector" },
            p({}, "Select Currency:"),
            button({
                class: () => currency.val === "INR" ? "active" : "",
                onclick: () => currency.val = "INR"
            }, "INR"),
            button({
                class: () => currency.val === "USD" ? "active" : "",
                onclick: () => currency.val = "USD"
            }, "USD")
        ),
        p({ class: "page-subtitle" }, "Sustainable intelligence for your pocket."),
        div({ class: "pricing-grid" },
            div({ class: "price-card" },
                h2({}, "Free"),
                div({ class: "price" }, "₹0 / $0"),
                p({ class: "tier-desc" }, "Perfect for light edits."),
                pre({}, "10 calls / day\n2,000 tokens / request\n25,000 tokens / month")
            ),
            div({ class: "price-card featured" },
                h2({}, "Basic"),
                div({ class: "price" }, () => priceMap[currency.val].basic + "/mo"),
                p({ class: "tier-desc" }, "For the focused student."),
                pre({}, "20 calls / minute\n4,000 tokens / request\n500,000 tokens / month")
            ),
            div({ class: "price-card" },
                h2({}, "Pro"),
                div({ class: "price" }, () => priceMap[currency.val].pro + "/mo"),
                p({ class: "tier-desc" }, "For the daily builder."),
                pre({}, "100 calls / minute\n10,000 tokens / request\n5,000,000 tokens / month")
            )
        ),
        Footer()
    )
}

const RoadmapPage = () => {
    const phases = [
        {
            title: "Phase I",
            tag: "Current",
            status: "active",
            items: [
                "Build the central backend: secure auth, API routing, and billing.",
                "Ship the initial headless CLI for early developer testing.",
                "Begin logging anonymized telemetry to understand real-world workflows."
            ]
        },
        {
            title: "Phase II",
            tag: "Next",
            items: [
                "Open public access to the Rta CLI experience.",
                "Introduce fast, context-aware AI code generation straight from the terminal.",
                "Deploy initial subscription tiers to ensure stable server performance."
            ]
        },
        {
            title: "Phase III",
            tag: "Soon",
            items: [
                "Release the full Rta Desktop application.",
                "Add deep project navigation and file-system indexing.",
                "Integrate advanced, multi-step AI reasoning for complex refactoring."
            ]
        },
        {
            title: "Phase IV",
            tag: "Later",
            items: [
                "Launch the core Rta mobile app for Android — the pocket workstation.",
                "Enable seamless, encrypted workspace syncing between CLI, Desktop, and Mobile.",
                "Bring native Git integration (commit, push, pull) straight to your phone."
            ]
        },
        {
            title: "Phase V",
            tag: "Future",
            items: [
                "Train custom models fine-tuned purely on the anonymized Rta developer dataset.",
                "Dramatically reduce subscription costs by running our own intelligence layer.",
                "Explore open-sourcing non-critical parts of the Rta infrastructure."
            ]
        }
    ]

    return div({ class: "roadmap-page" },
        NavLink("← back to home", "home"),
        h1({ class: "page-title" }, "Roadmap"),
        p({ class: "page-subtitle" }, "The architectural evolution of Rta."),
        div({ class: "roadmap-timeline" },
            phases.map(phase => div({ class: "roadmap-phase" },
                div({ class: `phase-marker ${phase.status || ""}` }),
                div({ class: "phase-header" },
                    h2({ class: "phase-title" }, phase.title),
                    div({ class: "phase-tag" }, phase.tag)
                ),
                div({ class: "roadmap-card" },
                    div({ class: "roadmap-list" },
                        phase.items.map(item => li({}, item))
                    )
                )
            ))
        ),
        Footer()
    )
}

const PrivacyPage = () => {
    return div({ class: "content-page doc-page" },
        NavLink("← back to home", "home"),
        h1({ class: "page-title" }, "Privacy Policy"),
        section({},
            h2({}, "1. Information We Collect"),
            p({}, "We take privacy seriously. However, to improve Rta and bill correctly, we collect minimal data required to provide our AI services:"),
            pre({}, "- Account Data: Username.\n- Telemetry: Scans of AI interactions (anonymized & scrubbed).\n- Usage: Token consumption for billing accuracy.\n- Payment Info: Processed securely by our payment partners (Stripe/Razorpay)."),
            h2({}, "2. Data Sanitization"),
            p({}, "Our server-side sanitizers automatically strip secrets (AWS keys, auth tokens) and local file paths from AI interaction logs before storage."),
            h2({}, "3. Data Security"),
            p({}, "We use industry-standard encryption (HTTPS/TLS) and hashed credentials. We never sell your data to third parties."),
            h2({}, "4. Support"),
            p({}, "Privacy-related inquiries can be submitted via our future ticket system.")
        ),
        Footer()
    )
}

const TermsPage = () => {
    return div({ class: "content-page doc-page" },
        NavLink("← back to home", "home"),
        h1({ class: "page-title" }, "Terms of Service"),
        section({},
            h2({}, "1. Terms of Use"),
            p({}, "By using Rta, you agree to these terms. Rta is a productivity tool for developers."),
            h2({}, "2. Subscription & Payments"),
            p({}, "Payments are billed monthly. Access to specific tiers (Basic/Pro) is granted immediately upon successful payment."),
            h2({}, "3. Refund Policy"),
            p({}, "We offer a 7-day no-questions-asked refund policy for your first subscription month if you are unsatisfied with the service."),
            h2({}, "4. Limitations"),
            p({}, "You may not use Rta to generate malicious code or engage in activity that disrupts our server infrastructure."),
            h2({}, "5. Business Info"),
            p({}, "Rta Software Solutions. Registered in India.")
        ),
        Footer()
    )
}

const AuthPage = () => {
    const isLogin = () => authMode.val === "login"

    return div({ class: "content-page auth-page" },
        NavLink("← back to home", "home"),
        div({ class: "auth-card" },
            h1({ class: "page-title" }, () => isLogin() ? "Login" : "Sign Up"),
            p({ class: "page-subtitle" }, () => isLogin() ? "Welcome back, developer." : "Join the medical-grade coding era."),

            () => authError.val ? p({ class: "error-msg" }, authError.val) : "",

            form({ onsubmit: (e) => handleAuth(e, authMode.val) },
                () => !isLogin() ? div({ class: "input-group" },
                    input({ name: "username", placeholder: "Username", required: true, class: "auth-input" })
                ) : "",
                div({ class: "input-group" },
                    input({ name: "email", type: "email", placeholder: "Email", required: true, class: "auth-input" })
                ),
                div({ class: "input-group" },
                    input({ name: "password", type: "password", placeholder: "Password", required: true, class: "auth-input" })
                ),
                div({ class: "hcaptcha-container" },
                    div({ class: "h-captcha", "data-sitekey": "51b06ce2-0f58-4148-8fec-b2944c54e718" })
                ),
                button({
                    type: "submit",
                    class: "auth-btn",
                    disabled: isLoading
                }, () => isLoading.val ? "Processing..." : (isLogin() ? "Login" : "Sign Up"))
            ),

            p({ class: "auth-toggle" },
                () => isLogin() ? "New to Rta?" : "Already have an account?",
                button({
                    class: "toggle-btn",
                    onclick: () => {
                        authMode.val = isLogin() ? "signup" : "login"
                        authError.val = ""
                    }
                }, () => isLogin() ? " Create an account" : " Login")
            )
        ),
        Footer()
    )
}


const ReleasesPage = () => {
    return div({ class: "releases-page" },
        NavLink("← back to home", "home"),
        div({ class: "release-card" },
            h1({ class: "release-title" }, "rta cli v0.1.0"),
            p({ class: "release-subtitle" }, "free tier • signup required"),
            div({ class: "download-section" },
                a({
                    href: "/rta",
                    class: "download-btn",
                    download: "rta"
                }, "Download for Linux (x64)"),
                p({ class: "platform-note" }, "Currently Linux only. macOS & Windows coming soon.")
            ),
            div({ class: "guide-section" },
                h2({}, "Installation & Setup"),
                div({ class: "guide-step" },
                    h3({}, "1. Authentication"),
                    p({}, "Login to your Rta account via the CLI:"),
                    pre({}, "rta login")
                ),
                div({ class: "guide-step" },
                    h3({}, "2. Configuration"),
                    p({}, "Your config.json will automatically update. To run from anywhere:"),
                    pre({}, "chmod +x rta\nsudo mv rta /usr/local/bin/")
                )
            )
        ),
        Footer()
    )
}

const WaitlistPage = () => {
    return div({ class: "waitlist-page" },
        NavLink("← back to home", "home"),
        div({ class: "iframe-container" },
            div({},
                `Loading form...`
            )
        ),
        Footer()
    )
}

// Load iframe dynamically
const loadWaitlistIframe = () => {
    setTimeout(() => {
        const container = document.querySelector('.iframe-container')
        if (container && currentPage.val === "waitlist") {
            container.innerHTML = `
                <iframe 
                    src="https://docs.google.com/forms/d/e/1FAIpQLSfnm1xCMBLUks3NIFWDfcyjvc6zIzC5gkQkevuXnTSGUnPQOQ/viewform?embedded=true" 
                    frameborder="0" 
                    marginheight="0" 
                    marginwidth="0">Loading…</iframe>
            `
        }
    }, 0)
}

const App = () => {
    return () => {
        setupParallax()
        switch (currentPage.val) {
            case "home": return HomePage()
            case "waitlist": loadWaitlistIframe(); return WaitlistPage()
            case "releases": return ReleasesPage()
            case "pricing": return PricingPage()
            case "roadmap": return RoadmapPage()
            case "privacy": return PrivacyPage()
            case "terms": return TermsPage()
            case "auth":
                setTimeout(() => {
                    const container = document.querySelector('.h-captcha');
                    if (container && window.hcaptcha) {
                        try {
                            window.hcaptcha.render(container);
                        } catch (e) {
                            console.warn("hCaptcha already rendered or failed:", e);
                        }
                    }
                }, 200);
                return AuthPage();
            default: return HomePage()
        }
    }
}

// Handle browser back/forward buttons
window.addEventListener('popstate', (e) => {
    const page = e.state?.page || "home"
    currentPage.val = page
})

// Parse URL on initial load
const initRoute = () => {
    const path = window.location.pathname.slice(1) || "home"
    currentPage.val = path
}

const root = document.getElementById("app")
if (root) {
    initRoute()
    van.add(root, App())
}

