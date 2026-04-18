import van from "vanjs-core"

const { div, h1, h2, h3, p, img, main, section, a, button, pre } = van.tags

// State for current page
const currentPage = van.state("home")
const currency = van.state("INR")

const priceMap = {
    INR: { basic: "₹75", pro: "₹299" },
    USD: { basic: "$1.49", pro: "$4.49" }
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

const NavLink = (text, page) => a({
    href: `#/${page}`,
    class: "nav-link",
    onclick: (e) => {
        e.preventDefault()
        currentPage.val = page
        window.history.pushState({ page }, "", `/${page}`)
        window.scrollTo(0, 0)
    }
}, text)

const Footer = () => div({ class: "footer-links" },
    NavLink("pricing", "pricing"),
    NavLink("privacy", "privacy"),
    NavLink("terms", "terms"),
    NavLink("sign in", "auth"),
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
                    a({
                        class: "waitlist-btn",
                        href: "#/waitlist",
                        onclick: (e) => {
                            e.preventDefault()
                            currentPage.val = "waitlist"
                            window.history.pushState({ page: "waitlist" }, "", "/waitlist")
                        }
                    }, "join waitlist"),
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
                pre({}, "7 AI calls / day\nDesktop & CLI Access\nApp Access (Limited)")
            ),
            div({ class: "price-card featured" },
                h2({}, "Basic"),
                div({ class: "price" }, () => priceMap[currency.val].basic + "/mo"),
                p({ class: "tier-desc" }, "For the focused student."),
                pre({}, "13 AI calls / day\nFull Mobile Access\nCloud Code Execution")
            ),
            div({ class: "price-card" },
                h2({}, "Pro"),
                div({ class: "price" }, () => priceMap[currency.val].pro + "/mo"),
                p({ class: "tier-desc" }, "For the daily builder."),
                pre({}, "100 AI calls / day\nFull Mobile Access\nEarly Access to Models")
            )
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
    return div({ class: "content-page auth-page" },
        NavLink("← back to home", "home"),
        div({ class: "auth-card" },
            h1({ class: "page-title" }, "Welcome"),
            p({ class: "page-subtitle" }, "Sign in or create an account. (Coming Soon)"),
            div({ class: "hcaptcha-placeholder" },
                div({ class: "h-captcha", "data-sitekey": "51b06ce2-0f58-4148-8fec-b2944c54e718" })
            ),
            button({ class: "auth-btn", disabled: true }, "Continue")
        ),
        Footer()
    )
}

const ReleasesPage = () => {
    return div({ class: "releases-page" },
        NavLink("← back to home", "home"),
        div({ class: "release-card" },
            h1({ class: "release-title" }, "rta cli v0.1.0"),
            p({ class: "release-subtitle" }, "free • no signup required"),
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
                    h3({}, "1. Environment Setup"),
                    p({}, "Create a .env file in your project root with your Gemini API Key:"),
                    pre({}, "GEMINI_API_KEY=your_key_here")
                ),
                div({ class: "guide-step" },
                    h3({}, "2. Add to PATH (Optional)"),
                    p({}, "To run rta from anywhere, use:"),
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
    const path = window.location.pathname
    if (path === "/waitlist") currentPage.val = "waitlist"
    else if (path === "/releases") currentPage.val = "releases"
    else if (path === "/pricing") currentPage.val = "pricing"
    else if (path === "/privacy") currentPage.val = "privacy"
    else if (path === "/terms") currentPage.val = "terms"
    else if (path === "/auth") currentPage.val = "auth"
    else currentPage.val = "home"
}

const root = document.getElementById("app")
if (root) {
    initRoute()
    van.add(root, App())
}

