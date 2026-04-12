import van from "vanjs-core"

const { div, h1, p, img, main, section, a, button } = van.tags

const App = () => {
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
                href: "https://docs.google.com/forms/d/e/1FAIpQLSfnm1xCMBLUks3NIFWDfcyjvc6zIzC5gkQkevuXnTSGUnPQOQ/viewform",
                target: "_blank",
                rel: "noopener noreferrer"
            }, "join waitlist")
        ),
        p({ class: "footer-line" }, "Coming Soon — October 2026")
    )
}

const root = document.getElementById("app")
if (root) {
    van.add(root, App())
}
