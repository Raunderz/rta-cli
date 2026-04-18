import van from "vanjs-core"

const { div, h1, h2, h3, p, img, main, section, a, button, pre } = van.tags

// State for current page
const currentPage = van.state("home")

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

const HomePage = () => {
    return main({ class: "container" },
        section({ class: "hero" },
            div({ class: "title-container" },
                h1({ class: "app-name" }, "rta"),
                p({ class: "description" },
                    "a mobile-first, ai-assisted code editor for android. built for speed, precision, and surgical development on the go."
                )
            ),
            div({ class: "logo-container" },
                img({ class: "logo", src: "/assets/icon.png", alt: "Rta Icon" })
            )
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
        ),
        p({ class: "footer-line" }, "Coming Soon — October 2026")
    )
}

const ReleasesPage = () => {
    return div({ class: "releases-page" },
        a({
            href: "#/",
            class: "back-link",
            onclick: (e) => {
                e.preventDefault()
                currentPage.val = "home"
                window.history.pushState({ page: "home" }, "", "/")
            }
        }, "← back to home"),
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
        p({ class: "footer-line" }, "Coming Soon — October 2026")
    )
}

const WaitlistPage = () => {
    return div({ class: "waitlist-page" },
        a({
            href: "#/",
            class: "back-link",
            onclick: (e) => {
                e.preventDefault()
                currentPage.val = "home"
                window.history.pushState({ page: "home" }, "", "/")
            }
        }, "← back to home"),
        div({ class: "iframe-container" },
            div({},
                `Loading form...`
            )
        ),
        p({ class: "footer-line" }, "Coming Soon — October 2026")
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
        if (currentPage.val === "home") {
            setupParallax()
            return HomePage()
        } else if (currentPage.val === "waitlist") {
            setupParallax()
            loadWaitlistIframe()
            return WaitlistPage()
        } else if (currentPage.val === "releases") {
            setupParallax()
            return ReleasesPage()
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
    if (path === "/waitlist" || path === "/waitlist.html") {
        currentPage.val = "waitlist"
    } else if (path === "/releases") {
        currentPage.val = "releases"
    } else {
        currentPage.val = "home"
    }
}

const root = document.getElementById("app")
if (root) {
    initRoute()
    van.add(root, App())
}
