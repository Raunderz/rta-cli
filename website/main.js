import van from "vanjs-core"

const { div, h1, h2, h3, p, img, main, section, a, button, pre, li, span, form, input } = van.tags

const API_BASE_URL = import.meta.env.VITE_BACKEND_URL || "http://localhost:8000"

// MD5 implementation for Gravatar (Tiny)
function getMD5(string) {
    function rotateLeft(lValue, iShiftBits) { return (lValue << iShiftBits) | (lValue >>> (32 - iShiftBits)); }
    function addUnsigned(lX, lY) {
        var lX4, lY4, lX8, lY8, lResult;
        lX8 = (lX & 0x80000000); lY8 = (lY & 0x80000000); lX4 = (lX & 0x40000000); lY4 = (lY & 0x40000000);
        lResult = (lX & 0x3FFFFFFF) + (lY & 0x3FFFFFFF);
        if (lX4 & lY4) return (lResult ^ 0x80000000 ^ lX8 ^ lY8);
        if (lX4 | lY4) { if (lResult & 0x40000000) return (lResult ^ 0xC0000000 ^ lX8 ^ lY8); else return (lResult ^ 0x40000000 ^ lX8 ^ lY8); }
        return (lResult ^ lX8 ^ lY8);
    }
    function F(x, y, z) { return (x & y) | ((~x) & z); }
    function G(x, y, z) { return (x & z) | (y & (~z)); }
    function H(x, y, z) { return (x ^ y ^ z); }
    function I(x, y, z) { return (y ^ (x | (~z))); }
    function FF(a, b, c, d, x, s, ac) { a = addUnsigned(a, addUnsigned(addUnsigned(F(b, c, d), x), ac)); return addUnsigned(rotateLeft(a, s), b); };
    function GG(a, b, c, d, x, s, ac) { a = addUnsigned(a, addUnsigned(addUnsigned(G(b, c, d), x), ac)); return addUnsigned(rotateLeft(a, s), b); };
    function HH(a, b, c, d, x, s, ac) { a = addUnsigned(a, addUnsigned(addUnsigned(H(b, c, d), x), ac)); return addUnsigned(rotateLeft(a, s), b); };
    function II(a, b, c, d, x, s, ac) { a = addUnsigned(a, addUnsigned(addUnsigned(I(b, c, d), x), ac)); return addUnsigned(rotateLeft(a, s), b); };
    function convertToWordArray(string) {
        var lWordCount; var lMessageLength = string.length; var lNumberOfWords_temp1 = lMessageLength + 8; var lNumberOfWords_temp2 = (lNumberOfWords_temp1 - (lNumberOfWords_temp1 % 64)) / 64; var lNumberOfWords = (lNumberOfWords_temp2 + 1) * 16; var lWordArray = Array(lNumberOfWords - 1); var lBytePosition = 0; var lByteCount = 0;
        while (lByteCount < lMessageLength) { lWordCount = (lByteCount - (lByteCount % 4)) / 4; lBytePosition = (lByteCount % 4) * 8; lWordArray[lWordCount] = (lWordArray[lWordCount] | (string.charCodeAt(lByteCount) << lBytePosition)); lByteCount++; }
        lWordCount = (lByteCount - (lByteCount % 4)) / 4; lBytePosition = (lByteCount % 4) * 8; lWordArray[lWordCount] = lWordArray[lWordCount] | (0x80 << lBytePosition); lWordArray[lNumberOfWords - 2] = lMessageLength << 3; lWordArray[lNumberOfWords - 1] = lMessageLength >>> 29; return lWordArray;
    };
    function wordToHex(lValue) { var WordToHexValue = "", WordToHexValue_temp = "", lByte, lCount; for (lCount = 0; lCount <= 3; lCount++) { lByte = (lValue >>> (lCount * 8)) & 255; WordToHexValue_temp = "0" + lByte.toString(16); WordToHexValue = WordToHexValue + WordToHexValue_temp.substr(WordToHexValue_temp.length - 2, 2); } return WordToHexValue; };
    var x = Array(); var k, AA, BB, CC, DD, a, b, c, d; var S11 = 7, S12 = 12, S13 = 17, S14 = 22; var S21 = 5, S22 = 9, S23 = 14, S24 = 20; var S31 = 4, S32 = 11, S33 = 16, S34 = 23; var S41 = 6, S42 = 10, S43 = 15, S44 = 21;
    string = unescape(encodeURIComponent(string)); x = convertToWordArray(string); a = 0x67452301; b = 0xEFCDAB89; c = 0x98BADCFE; d = 0x10325476;
    for (k = 0; k < x.length; k += 16) {
        AA = a; BB = b; CC = c; DD = d;
        a = FF(a, b, c, d, x[k + 0], S11, 0xD76AA478); d = FF(d, a, b, c, x[k + 1], S12, 0xE8C7B756); c = FF(c, d, a, b, x[k + 2], S13, 0x242070DB); b = FF(b, c, d, a, x[k + 3], S14, 0xC1BDCEEE); a = FF(a, b, c, d, x[k + 4], S11, 0xF57C0FAF); d = FF(d, a, b, c, x[k + 5], S12, 0x4787C62A); c = FF(c, d, a, b, x[k + 6], S13, 0xA8304613); b = FF(b, c, d, a, x[k + 7], S14, 0xFD469501); a = FF(a, b, c, d, x[k + 8], S11, 0x698098D8); d = FF(d, a, b, c, x[k + 9], S12, 0x8B44F7AF); c = FF(c, d, a, b, x[k + 10], S13, 0xFFFF5BB1); b = FF(b, c, d, a, x[k + 11], S14, 0x895CD7BE); a = FF(a, b, c, d, x[k + 12], S11, 0x6B901122); d = FF(d, a, b, c, x[k + 13], S12, 0xFD987193); c = FF(c, d, a, b, x[k + 14], S13, 0xA679438E); b = FF(b, c, d, a, x[k + 15], S14, 0x49B40821);
        a = GG(a, b, c, d, x[k + 1], S21, 0xF61E2562); d = GG(d, a, b, c, x[k + 6], S22, 0xC040B340); c = GG(c, d, a, b, x[k + 11], S23, 0x265E5A51); b = GG(b, c, d, a, x[k + 0], S24, 0xE9B6C7AA); a = GG(a, b, c, d, x[k + 5], S21, 0xD62F105D); d = GG(d, a, b, c, x[k + 10], S22, 0x02441453); c = GG(c, d, a, b, x[k + 15], S23, 0xD8A1E681); b = GG(b, c, d, a, x[k + 4], S24, 0xE7D3FBC8); a = GG(a, b, c, d, x[k + 9], S21, 0x21E1CDE6); d = GG(d, a, b, c, x[k + 14], S22, 0xC33707D6); c = GG(c, d, a, b, x[k + 3], S23, 0xF4D50D87); b = GG(b, c, d, a, x[k + 8], S24, 0x455A14ED); a = GG(a, b, c, d, x[k + 13], S21, 0xA9E3E905); d = GG(d, a, b, c, x[k + 2], S22, 0xFCEFA3F8); c = GG(c, d, a, b, x[k + 7], S23, 0x676F02D9); b = GG(b, c, d, a, x[k + 12], S24, 0x8D2A4C8A);
        a = HH(a, b, c, d, x[k + 5], S31, 0xFFFA3942); d = HH(d, a, b, c, x[k + 8], S32, 0x8771F681); c = HH(c, d, a, b, x[k + 11], S33, 0x6D9D6122); b = HH(b, c, d, a, x[k + 14], S34, 0xFDE5380C); a = HH(a, b, c, d, x[k + 1], S31, 0xA4BEEA44); d = HH(d, a, b, c, x[k + 4], S32, 0x4BDECFA9); c = HH(c, d, a, b, x[k + 7], S33, 0xF6BB4B60); b = HH(b, c, d, a, x[k + 10], S34, 0xBEBFBC70); a = HH(a, b, c, d, x[k + 13], S31, 0x289B7EC6); d = HH(d, a, b, c, x[k + 0], S32, 0xEAA127FA); c = HH(c, d, a, b, x[k + 3], S33, 0xD4EF3085); b = HH(b, c, d, a, x[k + 6], S34, 0x04881D05); a = HH(a, b, c, d, x[k + 9], S31, 0xD9D4D039); d = HH(d, a, b, c, x[k + 12], S32, 0xE6DB99E5); c = HH(c, d, a, b, x[k + 15], S33, 0x1FA27CF8); b = HH(b, c, d, a, x[k + 2], S34, 0xC4AC5665);
        a = II(a, b, c, d, x[k + 0], S41, 0xF4292244); d = II(d, a, b, c, x[k + 7], S42, 0x432AFF97); c = II(c, d, a, b, x[k + 14], S43, 0xAB9423A7); b = II(b, c, d, a, x[k + 5], S44, 0xFC93A039); a = II(a, b, c, d, x[k + 12], S41, 0x655B59C3); d = II(d, a, b, c, x[k + 3], S42, 0x8F0CCC92); c = II(c, d, a, b, x[k + 10], S43, 0xFFEFF47D); b = II(b, c, d, a, x[k + 1], S44, 0x85845DD1); a = II(a, b, c, d, x[k + 8], S41, 0x6FA87E4F); d = II(d, a, b, c, x[k + 15], S42, 0xFE2CE6E0); c = II(c, d, a, b, x[k + 6], S43, 0xA3014314); b = II(b, c, d, a, x[k + 13], S44, 0x4E0811A1); a = II(a, b, c, d, x[k + 4], S41, 0xF7537E82); d = II(d, a, b, c, x[k + 11], S42, 0xBD3AF235); c = II(c, d, a, b, x[k + 2], S43, 0x2AD7D2BB); b = II(b, c, d, a, x[k + 9], S44, 0xEB86D391);
        a = addUnsigned(a, AA); b = addUnsigned(b, BB); c = addUnsigned(c, CC); d = addUnsigned(d, DD);
    }
    var temp = wordToHex(a) + wordToHex(b) + wordToHex(c) + wordToHex(d); return temp.toLowerCase();
}

// State for current page
const currentPage = van.state("home")
const currency = van.state("INR")
const authMode = van.state("login") // "login" or "signup"
const user = van.state(JSON.parse(localStorage.getItem("rta_user") || "null"))
const authError = van.state("")
const isLoading = van.state(false)

const priceMap = {
    INR: { basic: "₹75", pro: "₹299" },
    USD: { basic: "$1.49", pro: "$4.49" }
}

// Auth Helpers
const saveUser = (userData) => {
    user.val = userData
    localStorage.setItem("rta_user", JSON.stringify(userData))
    currentPage.val = "dashboard"
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
                        href: "#/dashboard",
                        onclick: (e) => {
                            e.preventDefault()
                            currentPage.val = "dashboard"
                            window.history.pushState({ page: "dashboard" }, "", "/dashboard")
                        }
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

const DashboardPage = () => {
    if (!user.val) {
        setTimeout(() => {
            currentPage.val = "auth"
            window.history.pushState({ page: "auth" }, "", "/auth")
        }, 0)
        return div()
    }

    const { user: userData, api_key } = user.val
    const emailHash = getMD5(userData.email.trim().toLowerCase())
    const gravatarUrl = `https://www.gravatar.com/avatar/${emailHash}?s=64&d=identicon`

    const tier = userData.user_metadata?.tier || "Free"
    const tierClass = `tier-${tier.toLowerCase().slice(0, 3)}`

    // API Key State
    const keyVisible = van.state(false)

    return main({ class: "dashboard-container" },
        div({ class: "dash-header" },
            h1({ class: "dash-title" }, "Rta Dashboard"),
            div({ class: "dash-user-nav" },
                button({ class: "logout-btn-dash", onclick: logout }, "Logout")
            )
        ),

        div({ class: "dash-grid-top" },
            div({ class: "dash-card profile-card-new" },
                div({ class: "profile-section" },
                    img({ class: "avatar-large", src: gravatarUrl, alt: "Avatar" }),
                    div({ class: "profile-info" },
                        h2({}, userData.user_metadata?.username || "Developer"),
                        p({}, userData.email),
                        span({ class: `tier-badge ${tierClass}` }, tier)
                    )
                )
            ),
            div({ class: "dash-card usage-overview" },
                h3({ class: "dash-card-title" }, "Monthly Quota"),
                div({ class: "stats-row" },
                    div({ class: "stat-item" },
                        span({ class: "stat-label-dash" }, "Tokens Used"),
                        span({ class: "stat-value-dash" }, "1,420")
                    ),
                    div({ class: "stat-item" },
                        span({ class: "stat-label-dash" }, "Remaining"),
                        span({ class: "stat-value-dash" }, "23,580")
                    ),
                    div({ class: "stat-item" },
                        span({ class: "stat-label-dash" }, "Requests"),
                        span({ class: "stat-value-dash" }, "42")
                    )
                ),
                div({ class: "progress-container" },
                    div({ class: "progress-fill", style: "width: 5.6%" })
                ),
                p({ class: "usage-limit" }, "5.6% of monthly limit reached.")
            )
        ),

        div({ class: "dash-grid" },
            div({ class: "dash-card key-card-new" },
                h3({ class: "dash-card-title" }, "Root API Key"),
                div({ class: "key-container-dash" },
                    span({ class: "key-text" }, () => keyVisible.val ? (api_key || "No key found") : "••••••••••••••••••••••••••••••••"),
                    div({ class: "key-actions" },
                        button({
                            class: "icon-btn",
                            onclick: () => keyVisible.val = !keyVisible.val,
                            title: "Toggle Visibility"
                        }, () => keyVisible.val ? "🙈" : "👁️"),
                        button({
                            class: "icon-btn",
                            onclick: (e) => {
                                if (api_key) {
                                    navigator.clipboard.writeText(api_key)
                                    const orig = e.target.innerText
                                    e.target.innerText = "✅"
                                    setTimeout(() => e.target.innerText = orig, 2000)
                                }
                            },
                            title: "Copy Key"
                        }, "📋")
                    )
                ),
                p({ class: "key-warning", style: "margin-top: 1rem; color: #999; font-size: 0.8rem; font-style: italic" },
                    "Surgical Warning: This key gives full access to your Rta account via CLI. Keep it secret.")
            ),

            div({ class: "dash-card analytics-card" },
                h3({ class: "dash-card-title" }, "Analytics Activity"),
                div({ class: "chart-placeholder" },
                    [40, 70, 45, 90, 60, 85, 30].map((h, i) => div({
                        class: "chart-bar",
                        style: `height: ${h}px; left: ${i * 40}px;`
                    }))
                )
            )
        )
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
        // Handle theme switching
        if (currentPage.val === "dashboard") {
            document.body.className = "dashboard-body"

            // Load dashboard.css if not already present
            if (!document.getElementById("dash-styles")) {
                const link = document.createElement("link")
                link.id = "dash-styles"
                link.rel = "stylesheet"
                link.href = "./dashboard.css"
                document.head.appendChild(link)
            }
        } else {
            document.body.className = "landing-body"
            const dashStyle = document.getElementById("dash-styles")
            if (dashStyle) dashStyle.remove()
        }

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
            case "dashboard": return DashboardPage()
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

