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
const reveal = (el) => {
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('visible')
                observer.unobserve(entry.target)
            }
        })
    }, { threshold: 0.1 })
    
    el.setAttribute('data-reveal', '')
    observer.observe(el)
}

const Icon = (d, size = "16") => svg({ width: size, height: size, viewBox: "0 0 24 24", fill: "none", stroke: "currentColor", "stroke-width": "2", "stroke-linecap": "round", "stroke-linejoin": "round" }, path({ d }))

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
            p({ style: "margin-top: 16px; font-size: 14px; max-width: 240px; color: var(--text-muted);" }, 
                "Building the next generation of mobile development tools."
            )
        ),
        div({},
            p({ class: "mono mb-4" }, "Product"),
            div({ style: "display: flex; flex-direction: column; gap: 8px;" },
                NavLink("Pricing", "pricing"),
                NavLink("Roadmap", "roadmap"),
                NavLink("Status", "status")
            )
        ),
        div({},
            p({ class: "mono mb-4" }, "Company"),
            div({ style: "display: flex; flex-direction: column; gap: 8px;" },
                a({ href: "#", class: "nav-link" }, "About"),
                a({ href: "#", class: "nav-link" }, "Contact"),
                a({ href: "/waitlist.html", class: "nav-link" }, "Waitlist")
            )
        )
    ),
    div({ class: "container footer-bottom" },
        p({ style: "font-size: 12px;" }, "© 2026 Rta Software"),
        div({ style: "display: flex; gap: 24px;" },
            a({ href: "#", class: "nav-link", style: "font-size: 12px;" }, "Privacy"),
            a({ href: "#", class: "nav-link", style: "font-size: 12px;" }, "Terms")
        )
    )
)

// --- Page Components ---

const Hero = () => {
    const el = section({ class: "container hero" },
        h1({}, "Build faster. ", span({}, "Everywhere.")),
        p({ class: "description mb-8" }, "Rta is a high-performance code editor for Android and a powerful CLI for Linux and Windows. Designed for mobile-first precision."),
        div({ style: "display: flex; gap: 12px; justify-content: center;" },
            a({ class: "btn btn-primary", href: "#", onclick: (e) => { e.preventDefault(); currentPage.val = "auth" } }, "Get Started"),
            a({ class: "btn btn-secondary", href: "#", onclick: (e) => { e.preventDefault(); currentPage.val = "releases" } }, "Download CLI")
        )
    )
    reveal(el)
    return el
}

const Capabilities = () => {
    const items = [
        { title: "Native Git", desc: "Pure mobile Git implementation. No proxies, just performance." },
        { title: "AI Assisted", desc: "Context-aware code generation and refactoring built-in." },
        { title: "Local First", desc: "Lightning fast execution with zero round-trip latency." }
    ]

    const el = section({ class: "container" },
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
    const el = section({ class: "container" },
        div({ class: "text-center mb-8" },
            h2({ class: "mb-4" }, "Pricing"),
            p({ class: "description" }, "Simple, transparent tiers for every developer.")
        ),
        div({ style: "display: flex; justify-content: center; gap: 8px; margin-bottom: 32px;" },
            button({ class: () => `btn ${currency.val === "INR" ? "btn-primary" : "btn-secondary"}`, onclick: () => currency.val = "INR" }, "INR"),
            button({ class: () => `btn ${currency.val === "USD" ? "btn-primary" : "btn-secondary"}`, onclick: () => currency.val = "USD" }, "USD")
        ),
        div({ class: "pricing-wrapper" },
            table({ class: "pricing-table" },
                thead({}, tr({}, th({}, "Plan"), th({}, "Daily Calls"), th({}, "Monthly Tokens"), th({}, "Price"))),
                tbody({},
                    tr({}, td({ style: "font-weight: 500;" }, "Starter"), td({}, "10"), td({}, "25k"), td({ style: "font-weight: 600;" }, () => priceMap[currency.val].free)),
                    tr({ class: "featured" }, td({ style: "font-weight: 500;" }, "Basic"), td({}, "200"), td({}, "500k"), td({ style: "font-weight: 600;" }, () => priceMap[currency.val].basic)),
                    tr({}, td({ style: "font-weight: 500;" }, "Pro"), td({}, "1000"), td({}, "5M"), td({ style: "font-weight: 600;" }, () => priceMap[currency.val].pro))
                )
            )
        )
    )
    reveal(el)
    return main({}, el)
}

const RoadmapPage = () => {
    const phases = [
        { title: "Phase 1", tag: "Active", items: ["Core CLI", "Auth System", "Telemetry"] },
        { title: "Phase 2", tag: "Soon", items: ["Public Beta", "Context Sync", "AI Refactor"] },
        { title: "Phase 3", tag: "Future", items: ["Mobile App", "Desktop Sync", "Native Git"] }
    ]

    const el = section({ class: "container" },
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
    reveal(el)
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

    const el = section({ class: "container" },
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
    reveal(el)
    return main({}, el)
}

const ReleasesPage = () => {
    const selectedOS = van.state("linux")
    const el = section({ class: "container" },
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
    reveal(el)
    return main({}, el)
}

const AuthPage = () => {
    const mode = van.state("login")
    const el = section({ class: "container", style: "padding: 100px 0;" },
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
    reveal(el)
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
