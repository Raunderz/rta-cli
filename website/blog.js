import van from "vanjs-core"
import { marked } from "marked"

const { div, h2, h3, p, span, a, section, main, style } = van.tags

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

export const BlogPage = () => {
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
            slug: "cli-agent-architecture",
            title: "Building the RTA CLI Agent",
            date: "May 6, 2026",
            readTime: "6 min read",
            excerpt: "How we implemented project auto-discovery, context persistence, and parallel tool execution.",
            tags: ["CLI", "Python", "Architecture"],
            commit: "1cc10cb"
        },
        {
            slug: "desktop-ide",
            title: "Theia-based Desktop Editor",
            date: "May 5, 2026",
            readTime: "7 min read",
            excerpt: "Replacing our initial architecture with Eclipse Theia for a robust desktop experience.",
            tags: ["Desktop", "Theia", "Electron"],
            commit: "8e1e1e8"
        },
        {
            slug: "mobile-react-native",
            title: "React Native Mobile Architecture",
            date: "May 4, 2026",
            readTime: "5 min read",
            excerpt: "Optimizing the mobile app with Expo, Fabric, and isomorphic-git.",
            tags: ["Mobile", "React Native"],
            commit: "72330da"
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
                readTime: "4 min read",
                body: `
# Why We Built Rta

Rta is being built to address the difficulty of mobile-based development workflows, especially those relying on tools like Termux. While powerful, such tools often require manual setup, dependency management, and technical knowledge that can be a barrier for many users.

## Instant-Use Environment

Rta aims to simplify this experience by providing an instant-use environment for:
* Quick code edits
* Emergency bug fixes
* Viewing and understanding repositories on the go
* Lightweight development tasks without setup overhead

## Core Integration

It combines a lightweight code editor, Git integration, and AI assistance into a single mobile application. It is designed for developers who need fast access to code and intelligent support without setting up a full development environment. We want to bridge the gap between heavy desktop IDEs and completely unoptimized mobile experiences.
`
            },
            "cli-agent-architecture": {
                readTime: "6 min read",
                body: `
# Rta CLI Agent Architecture

The CLI component is the foundation of Rta. We designed it to be highly context-aware without requiring backend modifications.

## Core Intelligence

We implemented project auto-discovery by scanning the workspace on startup. The CLI detects:
- **Language/Framework**: Reading \`pyproject.toml\`, \`package.json\`, \`Cargo.toml\`, etc.
- **Test Frameworks**: Identifying \`pytest\`, \`vitest\`, \`cargo test\`.
- **Linter Configs**: Checking for \`.eslintrc\`, \`ruff.toml\`.

This allows the agent to automatically deduce the correct commands when a user says "run tests" or "lint the project".

## Parallel Tool Execution

To speed up operations, we implemented a dependency graph for tool execution. If multiple tool calls are independent (e.g., \`get_files_info\` and \`list_directory\`), they execute concurrently. Dependent tools (e.g., \`grep_search\` followed by \`edit_file\`) execute sequentially.

## Safety & UX

We added a \`question\` tool that allows the agent to pause and ask the user for clarification. Destructive actions (like \`delete_file\`) trigger an interactive confirmation prompt unless the \`--force\` flag is provided. Before executing \`git commit\`, we run a secret detection scan against patterns like \`API_KEY\` or \`ghp_*\` to prevent credential leaks.
`
            },
            "desktop-ide": {
                readTime: "7 min read",
                body: `
# Theia-based Desktop Editor

Our initial approach used Brackets, but we pivoted to **Eclipse Theia** to leverage its modern IDE framework capabilities. Theia provides a robust foundation using the Monaco Editor and a modular extension system.

## Extension Strategy

We kept customization purely additive. New code lives in the \`rta-extension/\` package, while existing Theia files remain untouched. 

- **AI Chat Panel**: Implemented as a custom Theia widget on the right sidebar. It uses \`react-markdown\` to render responses and Monaco for code block syntax highlighting.
- **RTA API Bridge**: A Node.js backend service (\`RtaApiService\`) connects Theia to the local CLI/API endpoint, handling message streaming and workspace context.
- **Tool Executor**: We ported CLI tools (like \`edit_file\`, \`grep_search\`) into Node.js built-ins and Theia's \`FileService\` API.

## Architecture

The desktop application runs in an Electron shell. The backend handles the tool execution locally, intercepting agent tool calls and modifying files directly through the editor's API, ensuring the UI remains in sync with disk changes.
`
            },
            "mobile-react-native": {
                readTime: "5 min read",
                body: `
# React Native Mobile Architecture

To maintain a fast and responsive mobile experience, we built the mobile app using Expo and React Native.

## Performance Optimization

We enabled React Native's **New Architecture (Fabric)**. This provides a synchronous UI thread, which is critical for smooth code editor interactions and real-time AI streaming updates. 

For large repositories, we implemented \`@shopify/flash-list\` in the file explorer and Git logs, ensuring we maintain 60 FPS scrolling even with thousands of files. We opted for **Zustand** over Redux for lightweight state management to keep the JS bundle small.

## Git & Filesystem Integration

Mobile development requires a robust local file system. We integrated \`isomorphic-git\` for a full JavaScript Git client implementation, paired with \`expo-file-system\` to manage local repository storage directly on the device.

We briefly evaluated LynxJS and VanJS for extreme startup speeds, but stuck with React Native for its mature ecosystem, particularly regarding Editor components and FS bridges.
`
            }
        }

        const content = contentMap[article.slug] || { readTime: "5 min read", body: "Full article coming soon..." }
        
        // Render markdown to HTML string
        const htmlContent = marked(content.body)

        const mdContainer = div({ class: "markdown-body description", style: "font-size: 18px; line-height: 1.8; color: var(--text-primary);" })
        mdContainer.innerHTML = htmlContent

        const markdownStyles = style(`
            .markdown-body h1 { font-size: 2.5rem; margin-top: 2rem; margin-bottom: 1rem; font-weight: 700; color: var(--text-primary); }
            .markdown-body h2 { font-size: 1.8rem; margin-top: 2rem; margin-bottom: 1rem; border-bottom: 1px solid var(--dark-border); padding-bottom: 0.5rem; color: var(--text-primary); }
            .markdown-body h3 { font-size: 1.4rem; margin-top: 1.5rem; margin-bottom: 1rem; color: var(--text-primary); }
            .markdown-body p { margin-bottom: 1.2rem; color: var(--text-secondary); font-size: 1.1rem; line-height: 1.7; }
            .markdown-body ul { margin-bottom: 1.5rem; padding-left: 2rem; list-style-type: disc; color: var(--text-secondary); }
            .markdown-body li { margin-bottom: 0.5rem; }
            .markdown-body code { background: rgba(255, 255, 255, 0.1); padding: 0.2rem 0.4rem; border-radius: 4px; font-family: var(--font-mono); font-size: 0.9em; }
            .markdown-body pre { background: #0d0d0d; padding: 1.5rem; border-radius: 8px; border: 1px solid var(--dark-border); overflow-x: auto; margin-bottom: 1.5rem; }
            .markdown-body pre code { background: none; padding: 0; color: #ff6b6b; }
            .markdown-body strong { font-weight: 600; color: var(--text-primary); }
        `)

        return div({ style: "max-width: 800px; margin: 0 auto; text-align: left;" },
            markdownStyles,
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
            mdContainer
        )
    }

    const el = section({ class: "container", style: "padding-top: 160px; padding-bottom: 80px;" },
        () => selectedArticle.val ? ArticleView(selectedArticle.val) : div({},
            div({ class: "section-header" },
                h2({ class: "section-title" }, "Technical Blog"),
                p({ class: "description section-description" }, "Deep dives into Rta architecture.")
            ),
            div({ style: "display: flex; flex-direction: column; gap: 2rem; max-width: 800px; margin: 0 auto;" },
                articles.map(article => ArticleCard(article))
            )
        )
    )
    reveal(el, true)
    return main({}, el)
}
