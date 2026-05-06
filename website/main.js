import van from "vanjs-core"

const { div, h1, h2, h3, h4, p, img, main, section, a, button, pre, li, span, form, input, svg, path, nav, ul, footer, table, tr, th, td, tbody, thead } = van.tags

const API_BASE_URL = import.meta.env.VITE_BACKEND_URL || "http://localhost:8000"

// --- State Management ---
const getInitialPage = () => {
    const path = window.location.pathname.slice(1)
    const validPages = ["home", "pricing", "roadmap", "status", "releases", "auth", "legal", "privacy", "blog"]
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

// --- Terminal Animation Component ---
const TerminalDemo = () => {
    let infoDiv = null
    let commandDiv = null
    let timeoutIds = []

    const sleep = (ms) => new Promise((r) => {
        const id = setTimeout(r, ms)
        timeoutIds.push(id)
    })

    const scrollToBottom = () => {
        if (commandDiv) {
            commandDiv.scrollTop = commandDiv.scrollHeight
        }
    }

    const addInfoLine = async (label, value, delay = 0) => {
        await sleep(delay)
        if (!infoDiv) return
        const line = div({
            style: "display: flex; justify-content: space-between; margin-bottom: 0.3rem; font-size: 10px; line-height: 1.4;"
        },
            span({ style: "color: #a0a0a0;" }, label),
            span({ style: "color: #ff6b6b;" }, value)
        )
        van.add(infoDiv, line)
    }

    const typeCommand = async (text, speed = 30) => {
        if (!commandDiv) return
        const cmdSpan = span({ style: "color: #ff6b6b;" })
        commandDiv.lastChild.appendChild(cmdSpan)
        for (let char of text) {
            cmdSpan.textContent += char
            scrollToBottom()
            await sleep(speed)
        }
    }

    const showLoader = async (duration = 1800) => {
        if (!commandDiv) return
        const frames = ['-', '\\', '|', '/']
        let frame = 0
        const start = Date.now()
        const loaderSpan = span({ style: "color: #ff6b6b; font-size: 10px;" })
        van.add(commandDiv, loaderSpan)

        return new Promise((r) => {
            const iv = setInterval(() => {
                loaderSpan.textContent = frames[frame % frames.length] + ' Processing...'
                frame++
                scrollToBottom()
                if (Date.now() - start > duration) {
                    clearInterval(iv)
                    loaderSpan.remove()
                    r()
                }
            }, 80)
        })
    }

    const addTool = async (name) => {
        await sleep(400)
        if (!commandDiv) return
        const line = div({
            style: "color: #a0a0a0; margin-bottom: 0.4rem; font-size: 10px; display: flex; align-items: center; gap: 0.5rem;"
        },
            span({ style: "color: #ff6b6b; font-weight: bold;" }, "[+]"),
            span(name)
        )
        van.add(commandDiv, line)
        scrollToBottom()

        await sleep(500)
        if (!commandDiv) return
        const check = div({
            style: "color: #cc2222; margin-bottom: 0.4rem; font-size: 9px; margin-left: 1.5rem;"
        }, "[done]")
        van.add(commandDiv, check)
        scrollToBottom()
    }

    const agentMsg = async (msg) => {
        await sleep(600)
        if (!commandDiv) return
        const line = div({
            style: "color: #ff6b6b; margin-top: 0.5rem; padding: 0.6rem; background: rgba(255, 107, 107, 0.05); border-left: 2px solid #ff6b6b; border-radius: 4px; font-size: 10px; line-height: 1.4;"
        })
        van.add(commandDiv, line)

        for (let char of msg) {
            line.textContent += char
            scrollToBottom()
            await sleep(15)
        }
    }

    const runDemo = async () => {
        if (!infoDiv || !commandDiv) return
        infoDiv.innerHTML = ''
        commandDiv.innerHTML = ''

        const scenarios = [
            {
                command: 'create a todo app with nextjs and stripe',
                tools: ['read_directory', 'create_file', 'install_package', 'configure_env', 'run_build'],
                message: 'Done! Created a Next.js todo app with Stripe integration and auth setup.'
            },
            {
                command: 'train a simple neural network in c++ for mnist',
                tools: ['create_file', 'configure_compiler', 'optimize_weights', 'run_simulation'],
                message: 'Training complete. Accuracy: 98.4%. Weights saved to model.bin.'
            },
            {
                command: 'generate the rta landing page with vanjs',
                tools: ['analyze_branding', 'scaffold_project', 'generate_components', 'apply_styling'],
                message: 'Website generated! High-performance landing page with terminal animations ready.'
            }
        ]

        const scenario = scenarios[Math.floor(Math.random() * scenarios.length)]

        await addInfoLine('Version', 'v0.2.0', 0)
        await addInfoLine('User', 'test@example.com', 100)
        await addInfoLine('Provider', 'rta', 100)
        await addInfoLine('Model', 'auto', 100)
        await addInfoLine('RAM', '42.5 MB', 100)

        await sleep(400)
        const prompt = div({
            style: "color: #cc2222; margin-bottom: 0.4rem; font-size: 10px; margin-top: 0.8rem;"
        }, "rta > ")
        van.add(commandDiv, prompt)

        await typeCommand(scenario.command, 40)
        await showLoader(2000)

        for (const tool of scenario.tools) {
            await addTool(tool)
        }

        await agentMsg(scenario.message)

        await sleep(4000)
        if (infoDiv.isConnected) runDemo()
    }

    const container = div({
        style: "background: #050505; border: 1px solid var(--dark-border); border-radius: 8px; font-family: var(--font-mono); overflow: hidden; width: 100%; height: 100%; display: flex; flex-direction: column;"
    },
        div({
            style: "background: #111; padding: 0.5rem 1rem; border-bottom: 1px solid var(--dark-border); display: flex; justify-content: space-between; align-items: center;"
        }, 
            span({ style: "font-size: 10px; color: #a0a0a0; font-weight: 600;" }, "rta-terminal-demo"),
            div({ style: "display: flex; gap: 4px;" },
                div({ style: "width: 6px; height: 6px; border-radius: 50%; background: #333;" }),
                div({ style: "width: 6px; height: 6px; border-radius: 50%; background: #333;" }),
                div({ style: "width: 6px; height: 6px; border-radius: 50%; background: #333;" })
            )
        ),
        div({
            style: "display: flex; flex-direction: column; gap: 1rem; padding: 1.2rem; flex: 1; overflow: hidden;"
        },
            // Top section: Branding + Info
            div({
                style: "display: flex; gap: 2rem; align-items: flex-start; border-bottom: 1px solid rgba(255,107,107,0.1); padding-bottom: 1rem; flex-shrink: 0;"
            },
                pre({
                    style: "font-family: monospace; font-size: 7px; line-height: 1.1; color: #ff6b6b; font-weight: bold; white-space: pre; margin: 0;"
                }, ` _  .-')   .-') _      ('-.     
( \\( -O ) (  OO) )    ( OO ).-. 
 ,------.  /     '._   / . --. / 
|   /\`. '|'--...__)  | \\-.  \\  
|  /  | |'--.  .--'.-'-'  |  | 
|  |_.' |   |  |    \\| |_.'  | 
|  .  '.'   |  |     |  .-.  | 
|  |\\  \\    |  |     |  | |  | 
 \\'--' '--'   \\'--'     \\'--' \\'--'`),
                div({ style: "min-width: 140px; flex: 1;" }) // Info container
            ),
            // Bottom section: Command output
            div({
                style: "color: #ff6b6b; font-size: 10px; line-height: 1.5; overflow-y: auto; flex: 1; padding-right: 5px;"
            })
        )
    )

    const mainArea = container.lastChild
    infoDiv = mainArea.firstChild.lastChild
    commandDiv = mainArea.lastChild

    setTimeout(() => runDemo(), 100)

    return container
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
        div({ class: "hero-visual animate-fade-up", style: "animation-delay: 0.5s; padding: 20px;" },
            TerminalDemo()
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
        div({ class: "features-cta", style: "margin-bottom: 4rem;" },
            p({}, "Want to see what we're building?"),
            a({ class: "btn btn-primary", href: "#", onclick: (e) => { e.preventDefault(); currentPage.val = "blog" } }, "Read Our Blog")
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

const BlogPage = () => {
    const articles = [
        {
            slug: "why-built-rta",
            title: "Why We Built Rta",
            date: "May 7, 2026",
            readTime: "4 min read",
            excerpt: "Understanding the purpose and motivation behind Rta: A mobile-first, AI-assisted code editor.",
            tags: ["Product", "Vision"],
            commit: "initial"
        },
        {
            slug: "daily-api-limiting",
            title: "Implementing Daily API Call Limiting with Supabase",
            date: "May 6, 2026",
            readTime: "6 min read",
            excerpt: "How we built a daily API call limiting system using Supabase profiles to track usage per user.",
            tags: ["Backend", "Supabase"],
            commit: "1cc10cb"
        },
        {
            slug: "mobile-navigation",
            title: "Building Responsive Mobile Navigation",
            date: "May 5, 2026",
            readTime: "5 min read",
            excerpt: "Implementing accessible mobile navigation with touch gestures and provider fallback logic.",
            tags: ["UI/UX", "Mobile"],
            commit: "8e1e1e8"
        },
        {
            slug: "introducing-rta",
            title: "Introducing Rta: The Developer Toolkit",
            date: "April 28, 2026",
            readTime: "5 min read",
            excerpt: "Announcing Rta - a developer toolkit for efficient code editing and automation.",
            tags: ["Announcement", "Product"],
            commit: "72330da"
        },
        {
            slug: "why-local-first",
            title: "Cloud Architecture Behind Rta",
            date: "April 15, 2026",
            readTime: "7 min read",
            excerpt: "How we built Rta with a cloud-centric backend using Supabase for auth and data.",
            tags: ["Architecture", "Backend"],
            commit: "16f712a"
        }
    ]

    const selectedArticle = van.state(null)

    window.addEventListener('keydown', (e) => {
        if (e.key === 'Escape' && selectedArticle.val) {
            selectedArticle.val = null
        }
    })

    const ArticleCard = (article) => {
        const el = div({ 
            id: `post-${article.slug}`,
            class: "feature-card", 
            style: "cursor: pointer; text-align: left; padding: 2rem; border-radius: 12px; transition: transform 0.2s, box-shadow 0.2s;",
            onclick: () => { selectedArticle.val = article; window.scrollTo(0, 0); }
        },
            div({ style: "display: flex; gap: 0.5rem; margin-bottom: 1.2rem;" },
                article.tags.map(tag => span({ 
                    class: "mono", 
                    style: "font-size: 11px; padding: 4px 10px; background: rgba(0, 217, 255, 0.1); border-radius: 100px; color: var(--accent);" 
                }, tag))
            ),
            h3({ style: "font-size: 24px; margin-bottom: 1rem; color: var(--text-primary);" }, article.title),
            p({ style: "font-size: 16px; color: var(--text-secondary); line-height: 1.6; margin-bottom: 2rem;" }, article.excerpt),
            div({ style: "display: flex; justify-content: space-between; align-items: center; border-top: 1px solid var(--dark-border); padding-top: 1.5rem;" },
                span({ class: "mono", style: "font-size: 13px; color: var(--text-secondary);" }, article.date),
                span({ class: "mono", style: "font-size: 13px; color: var(--text-secondary);" }, article.readTime)
            )
        )
        reveal(el)
        return el
    }

    const ArticleView = (article) => {
        const contentMap = {
            "why-built-rta": {
                readTime: "6 min read",
                body: `Rta addresses the friction in mobile-based development workflows, particularly the heavy constraints of Termux-based setups. While powerful, Termux requires manual POSIX environment setup, package dependency resolution (apt/pkg), and raw shell proficiency that creates a steep barrier for immediate use.

Our technical approach completely bypasses this by embedding an isolated execution context. Rather than simulating a full GNU/Linux environment, Rta focuses heavily on:
• Abstracted Git primitives over HTTP proxies
• Lightweight AST-based code analysis
• Direct bridge to native OS file systems

By utilizing Expo and React Native, we avoid the heavy overhead of generic web-wrappers. The editor component uses a custom virtualized list implementation to handle large source files without crashing the UI thread. Instead of parsing the entire project locally, we serialize file chunks and stream them to our cloud inference engine, maintaining a stable 60fps on low-end ARM devices.`
            },
            "daily-api-limiting": {
                readTime: "8 min read",
                body: `Implementing rate limiting required balancing latency against consistency. We opted for Supabase (PostgreSQL) profiles rather than an intermediate Redis layer to reduce infrastructure complexity.

When an API request hits our FastAPI backend, we execute a highly optimized PostgreSQL RPC call:
\`\`\`sql
CREATE OR REPLACE FUNCTION increment_api_call(user_id UUID)
RETURNS INT AS $$
  UPDATE profiles
  SET daily_calls = daily_calls + 1, last_active = NOW()
  WHERE id = user_id
  RETURNING daily_calls;
$$ LANGUAGE sql;
\`\`\`

By utilizing row-level locking (FOR UPDATE) inside the transaction, we guarantee atomicity even under concurrent burst requests. If the returned value exceeds the tier limit (e.g., 10 for Free, 50 for Basic), the middleware immediately intercepts the request and issues an HTTP 429 Too Many Requests. 

We also leverage PostgreSQL partial indexes on \`last_active\` to efficiently sweep and reset counters at midnight UTC via a pg_cron scheduled job, avoiding the O(N) scan across millions of users.`
            },
            "mobile-navigation": {
                readTime: "7 min read",
                body: `Mobile navigation requires strict adherence to frame budgets (16.6ms per frame). We implemented a hamburger menu with swipe-to-dismiss gestures using a custom touch-event dispatcher in VanJS.

Instead of animating layout properties (width, left, margin), we strictly animate composite properties:
\`\`\`css
.nav-menu {
  transform: translate3d(100%, 0, 0);
  transition: transform 0.3s cubic-bezier(0.25, 1, 0.5, 1);
  will-change: transform;
}
.nav-menu.open {
  transform: translate3d(0, 0, 0);
}
\`\`\`

By forcing GPU hardware acceleration (\`translate3d\`) and utilizing \`will-change\`, we bypassed main-thread layout recalculations entirely. 

On the provider fallback logic: we implemented a circuit breaker pattern. If the primary LLM provider times out or returns a 5xx error, the request automatically routes to a secondary provider. The circuit remains 'open' for a cooldown period (30s) before attempting to resume primary routing, preventing cascading latency spikes for our user base.`
            },
            "introducing-rta": {
                readTime: "6 min read",
                body: `Announcing Rta - a robust developer toolkit engineered for mobile-first precision. The tooling ecosystem has historically ignored mobile-native capabilities, forcing developers into compromised SSH clients or clunky browser IDEs.

Rta consists of a multi-tier architecture:
1. **The CLI & Core Engine**: Built in Python/Rust, providing local AST parsing, Git operations, and telemetry processing.
2. **The Desktop Layer**: A Tauri + Preact application for low-memory footprint UI on Windows/Linux.
3. **The Mobile Application**: An Expo-based React Native app that interfaces directly with our cloud layer.
4. **The Cloud Backend**: A FastAPI service routing LLM inference, managing authentication via Supabase, and orchestrating billing.

The unified CLI means developers get exactly the same deterministic behavior whether they're scripting in bash on Linux, or debugging via the mobile UI on Android.`
            },
            "why-local-first": {
                readTime: "9 min read",
                body: `Despite being 'mobile-first', Rta employs a cloud-centric architecture to handle heavy computation. We use a headless API schema that offloads vector tokenization, code AST analysis, and LLM orchestration to our servers.

The backend uses Supabase for authentication and session state. However, the real engineering challenge is context caching. We implemented a multi-level cache:
1. **L1 Cache**: In-memory Redis for high-frequency token queries.
2. **L2 Cache**: Persistent pgvector storage for project-wide semantic search.

When a user requests a refactor, the local client diffs the file and sends only the delta. The server reconstructing the full context tree uses the \`pgvector\` index to find semantic matches in neighboring files:
\`\`\`sql
SELECT id, content FROM code_embeddings 
ORDER BY embedding <-> query_embedding LIMIT 5;
\`\`\`

This architecture guarantees that the CLI binary remains under 15MB, while still providing enterprise-grade semantic intelligence. Security is enforced via strict ephemerality—code snippets hit RAM for inference and are instantly garbage collected.`
            }
        }

        const content = contentMap[article.slug] || { readTime: "5 min read", body: "Full article coming soon..." }

        return div({ style: "max-width: 800px; margin: 0 auto; text-align: left;" },
            div({ style: "margin-bottom: 2rem;" },
                a({ 
                    href: "#", 
                    class: "nav-link", 
                    style: "display: inline-block; padding: 0.5rem 0;",
                    onclick: (e) => { e.preventDefault(); selectedArticle.val = null }
                }, "← Back to Blog")
            ),
            div({ style: "display: flex; gap: 0.5rem; margin-bottom: 1.5rem;" },
                article.tags.map(tag => span({ 
                    class: "mono", 
                    style: "font-size: 11px; padding: 4px 10px; background: rgba(0, 217, 255, 0.1); border-radius: 100px; color: var(--accent);" 
                }, tag))
            ),
            h2({ style: "margin-bottom: 1rem; font-size: 36px; line-height: 1.2;" }, article.title),
            div({ style: "display: flex; gap: 2rem; margin-bottom: 3rem; color: var(--text-secondary); font-size: 14px; align-items: center; border-bottom: 1px solid var(--dark-border); padding-bottom: 1.5rem;" },
                span({ class: "mono" }, article.date),
                span({ class: "mono" }, content.readTime),
                a({ 
                    href: `https://github.com/schallten/Rta/commit/${article.commit}`, 
                    class: "nav-link",
                    target: "_blank"
                }, `View commit →`)
            ),
            div({ class: "description", style: "font-size: 18px; line-height: 1.8; white-space: pre-wrap; color: var(--text-primary);" }, content.body)
        )
    }

    const el = section({ class: "container", style: "padding-top: 160px; padding-bottom: 80px;" },
        () => selectedArticle.val ? ArticleView(selectedArticle.val) : div({},
            div({ class: "section-header" },
                h2({ class: "section-title" }, "Blog"),
                p({ class: "description section-description" }, "Updates from the frontlines of building Rta.")
            ),
            div({ style: "display: flex; flex-direction: column; gap: 2rem; max-width: 800px; margin: 0 auto;" },
                articles.map(article => ArticleCard(article))
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
                NavLink("Blog", "blog"),
                a({ href: "#", class: "nav-link" }, "Community")
            ),
            div({ class: "footer-column" },
                h4({}, "Legal"),
                NavLink("Privacy", "privacy"),
                NavLink("Blog", "blog"),
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
            case "blog": return BlogPage()
            default: return Hero()
        }
    },
    AppFooter()
)

van.add(document.body, App())
