import van from "vanjs-core"

const { div, h1, h2, h3, h4, p, img, main, section, a, button, pre, li, span, form, input, svg, path, nav, ul, footer, table, tr, th, td, tbody, thead } = van.tags

const API_BASE_URL = import.meta.env.VITE_BACKEND_URL || "http://localhost:8000"

// State
const currentPage = van.state("home")
const currency = van.state("INR")
const user = van.state(JSON.parse(localStorage.getItem("rta_user") || "null"))
const isLoading = van.state(false)
const authError = van.state("")
const authMode = van.state("login")

const priceMap = {
    INR: { free: "₹0", basic: "₹75", pro: "₹299" },
    USD: { free: "$0", basic: "$1.49", pro: "$4.49" }
}

// Icons
const IconCode = () => svg({ class: "feature-icon-box", viewBox: "0 0 24 24", fill: "none", stroke: "currentColor", "stroke-width": "1.5" }, 
    path({ d: "M16 18l6-6-6-6M8 6l-6 6 6 6" })
)
const IconGit = () => svg({ class: "feature-icon-box", viewBox: "0 0 24 24", fill: "none", stroke: "currentColor", "stroke-width": "1.5" },
    path({ d: "M9 19c-5 1.5-5-2.5-7-3m14 6v-3.87a3.37 3.37 0 0 0-.94-2.61c3.14-.35 6.44-1.54 6.44-7A5.44 5.44 0 0 0 20 4.77 5.07 5.07 0 0 0 19.91 1S18.73.65 16 2.48a13.38 13.38 0 0 0-7 0C6.27.65 5.09 1 5.09 1A5.07 5.07 0 0 0 5 4.77a5.44 5.44 0 0 0-1.5 3.78c0 5.42 3.3 6.61 6.44 7A3.37 3.37 0 0 0 9 18.13V22" })
)
const IconCloud = () => svg({ class: "feature-icon-box", viewBox: "0 0 24 24", fill: "none", stroke: "currentColor", "stroke-width": "1.5" },
    path({ d: "M18 10h-1.26A8 8 0 1 0 9 20h9a5 5 0 0 0 0-10z" })
)

// Scroll Reveal Observer
const observe = (el) => {
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

const Navbar = () => nav({ class: "container" },
    a({ href: "/", class: "logo", onclick: (e) => { e.preventDefault(); currentPage.val = "home" } }, "rta"),
    div({ class: "nav-links" },
        NavLink("Pricing", "pricing"),
        NavLink("Roadmap", "roadmap"),
        NavLink("Status", "status"),
        NavLink("Releases", "releases"),
        () => user.val ? a({ href: "/dashboard.html", class: "nav-link" }, "Dashboard") : NavLink("Account", "auth")
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
            a({ href: "/", class: "footer-logo" }, "Rta"),
            p({ class: "description", style: "max-width: 300px;" }, "Bringing medical-grade surgical development to the modern developer's pocket.")
        ),
        div({},
            p({ class: "mono mb-8", style: "color: var(--color-primary);" }, "Platform"),
            div({ style: "display: flex; flex-direction: column; gap: 16px;" },
                NavLink("Pricing", "pricing"),
                NavLink("Roadmap", "roadmap"),
                NavLink("Status", "status"),
                NavLink("Releases", "releases")
            )
        ),
        div({},
            p({ class: "mono mb-8", style: "color: var(--color-primary);" }, "Legal"),
            div({ style: "display: flex; flex-direction: column; gap: 16px;" },
                NavLink("Privacy", "privacy"),
                NavLink("Terms", "terms")
            )
        )
    ),
    div({ class: "container", style: "margin-top: 80px; padding-top: 40px; border-top: 1px solid var(--color-border); opacity: 0.4;" },
        p({ style: "font-size: 14px; font-family: var(--font-mono);" }, "© 2026 Rta Software Solutions. Built with anatomical precision.")
    )
)

const HomePage = () => {
    const s1 = section({ class: "container" },
        div({ class: "hero-grid" },
            div({ class: "hero-text" },
                h1({}, "Surgical development. In your pocket."),
                p({ class: "description mb-8" }, "Rta is the mobile workstation for the modern developer. Architected for high-precision coding, Git native workflows, and surgical AI assistance."),
                div({ style: "display: flex; gap: 20px;" },
                    a({ class: "btn btn-primary", href: "#/auth", onclick: (e) => { e.preventDefault(); currentPage.val = "auth" } }, "Get Started"),
                    a({ class: "btn btn-secondary", href: "#/releases", onclick: (e) => { e.preventDefault(); currentPage.val = "releases" } }, "Download CLI")
                )
            ),
            div({ class: "hero-icon-wrapper" },
                img({ src: "/assets/icon.png", class: "hero-icon" })
            )
        )
    )
    observe(s1)

    const s2 = section({ class: "alternate" },
        div({ class: "container" },
            h2({}, "Core Capabilities."),
            div({ class: "feature-list" },
                div({ class: "feature-row" },
                    div({ class: "feature-meta" }, IconCode(), h3({ style: "margin:0" }, "Surgical AI")),
                    p({ class: "description" }, "Context-aware intelligence tuned for mobile. Our models are trained for anatomical precision in refactoring and generation.")
                ),
                div({ class: "feature-row" },
                    div({ class: "feature-meta" }, IconGit(), h3({ style: "margin:0" }, "Git Native")),
                    p({ class: "description" }, "Full version control without compromise. Commit, push, and pull directly from your device with native performance.")
                ),
                div({ class: "feature-row" },
                    div({ class: "feature-meta" }, IconCloud(), h3({ style: "margin:0" }, "Cloud Sync")),
                    p({ class: "description" }, "Seamless continuity between CLI and Mobile environments. Your workspace follows you everywhere.")
                )
            )
        )
    )
    observe(s2)

    const s3 = section({ class: "container" },
        div({ class: "grid-2", style: "align-items: center;" },
            div({},
                h2({}, "Terminal Access."),
                p({ class: "description mb-8" }, "The Rta CLI brings high-precision intelligence to your local environment. One command to diagnose and refactor."),
                div({ class: "code-preview" },
                    span({ style: "color: var(--color-primary);" }, "$ rta chat"), "\n",
                    span({ style: "color: #7CB342;" }, "i >"), " optimize database query...", "\n",
                    span({ style: "color: var(--color-text); opacity: 0.5;" }, "rta > analyzing project structure..."), "\n",
                    span({ style: "color: #E8A547;" }, "✓ surgical refactor applied. 42% faster.")
                )
            ),
            div({ class: "card" },
                h3({ style: "color: var(--color-text); margin-bottom: 24px;" }, "Experience Precision."),
                p({ class: "description mb-8" }, "Join the movement of developers building with surgical accuracy. Sign up to get started."),
                a({ class: "btn btn-primary", href: "#/auth", onclick: (e) => { e.preventDefault(); currentPage.val = "auth" } }, "Sign Up Now")
            )
        )
    )
    observe(s3)

    return main({}, s1, s2, s3)
}

const PricingPage = () => {
    const s = section({ class: "container" },
        h1({ class: "text-center" }, "Pricing Plans"),
        p({ class: "description text-center mb-8" }, "Sustainable intelligence for your pocket."),
        div({ style: "display: flex; justify-content: center; gap: 16px; margin-bottom: 60px;" },
            button({ class: () => `btn ${currency.val === "INR" ? "btn-primary" : "btn-secondary"}`, onclick: () => currency.val = "INR" }, "INR"),
            button({ class: () => `btn ${currency.val === "USD" ? "btn-primary" : "btn-secondary"}`, onclick: () => currency.val = "USD" }, "USD")
        ),
        div({ class: "pricing-wrapper" },
            table({ class: "pricing-table" },
                thead({}, tr({}, th({}, "Plan"), th({}, "Daily Calls"), th({}, "Monthly Tokens"), th({}, "Price"))),
                tbody({},
                    tr({}, td({}, "Free"), td({}, "10 Calls"), td({}, "25k Tokens"), td({ class: "price-cell" }, () => priceMap[currency.val].free)),
                    tr({ class: "featured" }, td({}, "Basic"), td({}, "20 / min"), td({}, "500k Tokens"), td({ class: "price-cell" }, () => priceMap[currency.val].basic)),
                    tr({}, td({}, "Pro"), td({}, "100 / min"), td({}, "5M Tokens"), td({ class: "price-cell" }, () => priceMap[currency.val].pro))
                )
            )
        )
    )
    observe(s)
    return main({}, s)
}

const RoadmapPage = () => {
    const phases = [
        { title: "Phase I", items: ["Central Backend & Auth", "Headless CLI Testing", "Telemetry Logging"] },
        { title: "Phase II", items: ["Public CLI Access", "Context-Aware Generation", "Subscription Tiers"] },
        { title: "Phase III", items: ["Rta Desktop Release", "Project Navigation", "Multi-Step Reasoning"] },
        { title: "Phase IV", items: ["Android Mobile App", "Workspace Syncing", "Native Git"] },
        { title: "Phase V", items: ["Custom Models", "Cost Reduction", "Open-Core"] }
    ]

    const s = section({ class: "container" },
        h1({ class: "mb-8" }, "Project Roadmap"),
        div({ class: "roadmap-container" },
            phases.map(p => div({ class: "roadmap-box" },
                h3({ style: "color: var(--color-text); margin-bottom: 24px;" }, p.title),
                ul({ style: "list-style: none; display: flex; flex-direction: column; gap: 12px; opacity: 0.7;" },
                    p.items.map(i => li({ style: "display: flex; gap: 10px;" }, span({ style: "color: var(--color-primary);" }, "→"), i))
                )
            ))
        )
    )
    observe(s)
    return main({}, s)
}

const StatusPage = () => {
    const statusData = van.state({ loading: true, status: "checking", services: {} })
    const check = async () => {
        try {
            const res = await fetch(`${API_BASE_URL}/v1/status`, { headers: { "ngrok-skip-browser-warning": "true" } })
            statusData.val = { loading: false, ...(await res.json()) }
        } catch {
            statusData.val = { loading: false, status: "down", services: { api: "offline" } }
        }
    }
    check()

    const s = section({ class: "container" },
        h1({ class: "text-center" }, "System Health"),
        div({ class: "status-card" },
            div({ class: "status-header" },
                h3({ style: "margin:0" }, "Global Status"),
                () => statusData.val.loading ? p({}, "Checking...") : 
                span({ 
                    class: "status-indicator", 
                    style: `background: ${statusData.val.status === "operational" ? "#7CB342" : "#E57373"}; color: #fff;` 
                }, statusData.val.status.toUpperCase())
            ),
            div({ class: "status-body" },
                () => Object.entries(statusData.val.services).map(([n, s]) => div({ class: "status-row" },
                    span({ style: "font-weight: 500;" }, n.charAt(0).toUpperCase() + n.slice(1)),
                    span({ style: `color: ${s === "operational" ? "#7CB342" : "#E57373"}; font-family: var(--font-mono); font-weight: 700;` }, s.toUpperCase())
                ))
            )
        )
    )
    observe(s)
    return main({}, s)
}

const ReleasesPage = () => {
    const selectedOS = van.state("linux")
    const s = section({ class: "container" },
        div({ class: "text-center" },
            h1({}, "Rta CLI v0.2.0"),
            p({ class: "description mb-8" }, "Anatomical precision in every command."),
            div({ style: "display: flex; justify-content: center; gap: 16px; margin-bottom: 60px;" },
                button({ class: () => `btn ${selectedOS.val === "linux" ? "btn-primary" : "btn-secondary"}`, onclick: () => selectedOS.val = "linux" }, "Linux"),
                button({ class: () => `btn ${selectedOS.val === "macos" ? "btn-primary" : "btn-secondary"}`, onclick: () => selectedOS.val = "macos" }, "macOS"),
                button({ class: () => `btn ${selectedOS.val === "windows" ? "btn-primary" : "btn-secondary"}`, onclick: () => selectedOS.val = "windows" }, "Windows")
            ),
            div({ class: "card", style: "max-width: 800px; margin: 0 auto; text-align: left;" },
                div({ style: "text-align: center; margin-bottom: 48px;" },
                    () => selectedOS.val === "linux" ? a({ href: "/rta", class: "btn btn-primary", download: "rta" }, "Download Binary") : 
                    selectedOS.val === "windows" ? a({ href: "/rta.exe", class: "btn btn-primary", download: "rta.exe" }, "Download Binary (.exe)") : 
                    p({ class: "description" }, "macOS Binary Coming Soon")
                ),
                h3({ class: "mb-4" }, "Quick Start"),
                pre({ class: "code-preview" }, () => selectedOS.val === "linux" ? "chmod +x rta\nsudo mv rta /usr/local/bin/\nrta chat" : "rta.exe chat")
            )
        )
    )
    observe(s)
    return main({}, s)
}

const AuthPage = () => {
    const isLogin = () => authMode.val === "login"
    const s = section({ class: "container" },
        div({ style: "display: flex; justify-content: center;" },
            div({ class: "card", style: "width: 100%; max-width: 480px;" },
                h2({ class: "text-center" }, () => isLogin() ? "Welcome Back" : "Create Account"),
                p({ class: "description text-center mb-8" }, () => isLogin() ? "Access your workstation." : "Start your surgical journey."),
                form({ onsubmit: (e) => e.preventDefault() },
                    !isLogin() ? div({ class: "mb-4" }, input({ style: "width:100%; background:var(--color-secondary); border:1px solid var(--color-border); padding:16px; border-radius:4px; color:var(--color-text);", placeholder: "Username" })) : "",
                    div({ class: "mb-4" }, input({ style: "width:100%; background:var(--color-secondary); border:1px solid var(--color-border); padding:16px; border-radius:4px; color:var(--color-text);", type: "email", placeholder: "Email Address" })),
                    div({ class: "mb-8" }, input({ style: "width:100%; background:var(--color-secondary); border:1px solid var(--color-border); padding:16px; border-radius:4px; color:var(--color-text);", type: "password", placeholder: "Secure Password" })),
                    button({ class: "btn btn-primary", style: "width: 100%;" }, () => isLogin() ? "Login" : "Sign Up")
                ),
                div({ class: "text-center mt-8" },
                    a({ 
                        href: "#", 
                        class: "description", 
                        style: "font-size: 14px; opacity: 0.6;",
                        onclick: (e) => { e.preventDefault(); authMode.val = isLogin() ? "signup" : "login" }
                    }, () => isLogin() ? "New to Rta? Create an account" : "Already have an account? Login")
                )
            )
        )
    )
    observe(s)
    return main({}, s)
}

const PrivacyPage = () => {
    const s = section({ class: "container" }, h1({}, "Privacy Policy"), p({ class: "description" }, "Your data remains yours. Anatomical precision means zero leak of sensitive information."))
    observe(s); return main({}, s)
}

const TermsPage = () => {
    const s = section({ class: "container" }, h1({}, "Terms of Service"), p({ class: "description" }, "Built with transparency. Billed with accuracy."))
    observe(s); return main({}, s)
}

const App = () => div({},
    Navbar(),
    () => {
        switch (currentPage.val) {
            case "home": return HomePage()
            case "pricing": return PricingPage()
            case "roadmap": return RoadmapPage()
            case "status": return StatusPage()
            case "releases": return ReleasesPage()
            case "auth": return AuthPage()
            case "privacy": return PrivacyPage()
            case "terms": return TermsPage()
            default: return HomePage()
        }
    },
    AppFooter()
)

const root = document.getElementById("app")
if (root) {
    van.add(root, App())
}
