import van from "vanjs-core"

const { div, h1, p, img, main, section, a, button } = van.tags

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
                    window.history.pushState({page: "waitlist"}, "", "/waitlist")
                }
            }, "join waitlist")
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
                window.history.pushState({page: "home"}, "", "/")
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
    } else {
        currentPage.val = "home"
    }
}

const root = document.getElementById("app")
if (root) {
    initRoute()
    van.add(root, App())
}
