import van from "vanjs-core"

const { div, h1, p, img, main, section } = van.tags

const App = () => {
    return main({ id: "app" },
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
        p({ class: "footer-line" }, "Coming Soon — October 2026")
    )
}

van.add(document.getElementById("app"), App())
