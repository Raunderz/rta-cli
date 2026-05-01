import van from "vanjs-core"

const { div, h1, h2, h3, p, img, main, section, a, button, pre, li, span, form, input, svg, path, nav, ul, footer, table, tr, th, td, tbody, thead } = van.tags

const API_BASE_URL = import.meta.env.VITE_BACKEND_URL || "http://localhost:8000"

// --- State Management ---
const currentPage = van.state("home")
const currency = van.state("INR")
const user = van.state(JSON.parse(localStorage.getItem("rta_user") || "null"))
const statusData = van.state({ loading: true, status: "Checking", services: {} })

const priceMap = {
    INR: { free: "₹0", basic: "₹75", pro: "₹299" },
    USD: { free: "$0", basic: "$1.49", pro: "$4.49" }
}

// --- Animation Engine ---
const reveal = (el, immediate = false) => {
    if (immediate) {
        el.classList.add('visible')
        return
    }
    
    // Safety check: if element is already in viewport, reveal immediately
    const rect = el.getBoundingClientRect()
    if (rect.top < window.innerHeight && rect.bottom > 0) {
        el.classList.add('visible')
        return
    }

    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('visible')
                observer.unobserve(entry.target)
            }
        })
    }, { threshold: 0.05 })
    
    el.setAttribute('data-reveal', '')
    observer.observe(el)
}

const Icon = (d, size = "16") => svg({ width: size, height: size, viewBox: "0 0 24 24", fill: "none", stroke: "currentColor", "stroke-width": "2", "stroke-linecap": "round", "stroke-linejoin": "round" }, path({ d }))

const GifPlaceholder = () => {
    return div({ class: "gif-placeholder floating" },
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

// --- Shared Components ---
const Navbar = () => nav({},
    div({ class: "container nav-container" },
        a({ href: "/", class: "logo", onclick: (e) => { e.preventDefault(); currentPage.val = "home"; window.history.pushState({}, "", "/") } }, "rta"),
        div({ class: "nav-links" },
            NavLink("Pricing", "pricing"),
            NavLink("Roadmap", "roadmap"),
            NavLink("Status", "status"),
            NavLink("Releases", "releases"),
            () => user.val ? a({ href: "/dashboard.html", class: "nav-link" }, "Dashboard") : NavLink("Account", "auth")
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
            a({ href: "#", class: "nav-link" }, "Privacy"),
            a({ href: "#", class: "nav-link" }, "Terms")
        )
    )
)

// --- Page Components ---

const Hero = () => {
    const el = section({ class: "container hero" },
        div({ class: "hero-content" },
            h1({}, "Build faster. ", span({}, "Everywhere.")),
            p({ class: "description" }, "Rta is a high-performance code editor for Android and a powerful CLI for Linux and Windows. Designed for mobile-first precision."),
            div({ style: "display: flex; gap: 16px; justify-content: center; margin-top: 40px;" },
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

    const el = section({ class: "container", style: "padding-top: 0;" },
        div({ class: "bento-grid" },
            items.map(item => div({ class: "bento-item" },
                h3({}, item.title),
                p({ class: "description" }, item.desc)
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

    const el = section({ class: "container", style: "padding-top: 120px;" },
        div({ class: "text-center mb-8" },
            h2({ class: "mb-4" }, "Pricing"),
            p({ class: "description" }, "Simple, transparent tiers for every developer.")
        ),
        div({ style: "display: flex; justify-content: center; gap: 8px; margin-bottom: 48px;" },
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
                button({ class: `btn ${tier.featured ? 'btn-primary' : 'btn-secondary'}`, style: "width: 100%;" }, "Select Plan")
            ))
        )
    )
    reveal(el, true) // Instant visibility for first section
    return main({}, el)
}

const RoadmapPage = () => {
    const phases = [
        { title: "Phase 1", tag: "Active", items: ["Core CLI", "Auth System", "Telemetry"] },
        { title: "Phase 2", tag: "Soon", items: ["Public Beta", "Context Sync", "AI Refactor"] },
        { title: "Phase 3", tag: "Future", items: ["Mobile App", "Desktop Sync", "Native Git"] }
    ]

    const el = section({ class: "container", style: "padding-top: 120px;" },
        h2({ class: "text-center mb-8" }, "Roadmap"),
        div({ class: "bento-grid" },
            phases.map(p => div({ class: "bento-item" },
                div({},
                    span({ class: "mono" }, p.tag),
                    h3({ class: "mt-4" }, p.title),
                    ul({ style: "list-style: none; margin-top: 24px; display: flex; flex-direction: column; gap: 12px;" },
                        p.items.map(i => li({ style: "font-size: 14px; color: var(--text-muted);" }, "→ " + i))
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

    const el = section({ class: "container", style: "padding-top: 120px;" },
        h2({ class: "text-center mb-8" }, "System Status"),
        div({ class: "status-card" },
            () => statusData.val.loading ? div({ class: "text-center" }, p({}, "Loading...")) : div({},
                div({ style: "display: flex; justify-content: space-between; align-items: center; margin-bottom: 32px;" },
                    h3({ style: "margin: 0;" }, "Status"),
                    span({ 
                        style: `font-size: 12px; font-weight: 600; color: ${statusData.val.status === 'operational' ? '#10B981' : '#EF4444'}` 
                    }, statusData.val.status.toUpperCase())
                ),
                Object.entries(statusData.val.services).map(([name, status]) => div({ class: "status-row" },
                    span({ style: "color: var(--text-muted); font-size: 14px;" }, name),
                    span({ 
                        style: `font-weight: 500; font-size: 14px; color: ${status === 'operational' ? '#10B981' : '#EF4444'}` 
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
    const el = section({ class: "container", style: "padding-top: 120px;" },
        div({ class: "text-center" },
            h2({ class: "mb-4" }, "Releases"),
            p({ class: "description mb-8" }, "Get the latest Rta CLI for your platform."),
            div({ style: "display: flex; justify-content: center; gap: 8px; margin-bottom: 40px;" },
                button({ class: () => `btn ${selectedOS.val === 'linux' ? 'btn-primary' : 'btn-secondary'}`, onclick: () => selectedOS.val = 'linux' }, "Linux"),
                button({ class: () => `btn ${selectedOS.val === 'windows' ? 'btn-primary' : 'btn-secondary'}`, onclick: () => selectedOS.val = 'windows' }, "Windows")
            ),
            div({ class: "status-card", style: "max-width: 800px; text-align: left;" },
                div({ style: "text-align: center; margin-bottom: 40px;" },
                    () => selectedOS.val === 'linux' ? a({ href: "/rta", class: "btn btn-primary", download: "rta" }, "Download for Linux") : 
                    a({ href: "/rta.exe", class: "btn btn-primary", download: "rta.exe" }, "Download for Windows")
                ),
                h3({ class: "mb-4" }, "Installation"),
                pre({ 
                    style: "background: #111; padding: 24px; border-radius: 8px; font-family: var(--font-mono); color: #888; font-size: 14px; overflow-x: auto;" 
                }, () => selectedOS.val === 'linux' ? "chmod +x rta\nsudo mv rta /usr/local/bin/\nrta chat" : "rta.exe chat")
            )
        )
    )
    reveal(el, true)
    return main({}, el)
}

const AuthPage = () => {
    const mode = van.state("login")
    const el = section({ class: "container", style: "padding-top: 120px; padding-bottom: 100px;" },
        div({ style: "display: flex; justify-content: center;" },
            div({ class: "status-card", style: "width: 100%; max-width: 400px;" },
                h2({ class: "text-center mb-8", style: "font-size: 24px;" }, mode.val === "login" ? "Login" : "Sign Up"),
                form({ onsubmit: (e) => e.preventDefault() },
                    () => mode.val === "signup" ? div({ class: "mb-4" }, 
                        input({ style: "width:100%; background:var(--bg); border:1px solid var(--border); padding:12px; border-radius:6px; color:var(--text);", placeholder: "Username" })
                    ) : "",
                    div({ class: "mb-4" }, 
                        input({ style: "width:100%; background:var(--bg); border:1px solid var(--border); padding:12px; border-radius:6px; color:var(--text);", type: "email", placeholder: "Email" })
                    ),
                    div({ class: "mb-8" }, 
                        input({ style: "width:100%; background:var(--bg); border:1px solid var(--border); padding:12px; border-radius:6px; color:var(--text);", type: "password", placeholder: "Password" })
                    ),
                    button({ class: "btn btn-primary", style: "width: 100%;" }, mode.val === "login" ? "Continue" : "Create Account")
                ),
                div({ class: "text-center mt-8" },
                    a({ 
                        href: "#", 
                        class: "nav-link", 
                        style: "font-size: 13px;",
                        onclick: (e) => { e.preventDefault(); mode.val = mode.val === "login" ? "signup" : "login" }
                    }, mode.val === "login" ? "Don't have an account? Sign up" : "Already have an account? Login")
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
        switch (currentPage.val) {
            case "home": return div({}, Hero(), Capabilities())
            case "pricing": return PricingPage()
            case "roadmap": return RoadmapPage()
            case "status": return StatusPage()
            case "releases": return ReleasesPage()
            case "auth": return AuthPage()
            default: return Hero()
        }
    },
    AppFooter()
)

van.add(document.body, App())
