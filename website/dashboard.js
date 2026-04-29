import van from "vanjs-core"

const { div, h2, p, main, span, button, svg, path, nav, a, input } = van.tags

const API_BASE_URL = import.meta.env.VITE_BACKEND_URL || "http://localhost:8000"

// Handle OAuth Hash
const hashParams = new URLSearchParams(window.location.hash.substring(1))
if (hashParams.has("access_token")) {
    const oauthUser = {
        access_token: hashParams.get("access_token"),
        refresh_token: hashParams.get("refresh_token"),
        api_key: hashParams.get("api_key") || null
    }
    const existing = JSON.parse(localStorage.getItem("rta_user") || "{}")
    const finalUser = { ...existing, ...oauthUser }
    if (!finalUser.api_key && existing.api_key) finalUser.api_key = existing.api_key
    
    localStorage.setItem("rta_user", JSON.stringify(finalUser))
    window.location.hash = ""
}

const user = van.state(JSON.parse(localStorage.getItem("rta_user") || "null"))
const keyVisible = van.state(false)
const selectedOS = van.state("linux")
const dashData = van.state(null)
const error = van.state(null)
const isLoading = van.state(true)

if (!user.val) { window.location.href = "/" }

const logout = () => {
    localStorage.removeItem("rta_user")
    window.location.href = "/"
}

const Icon = (d, size = "18") => svg({ width: size, height: size, viewBox: "0 0 24 24", fill: "none", stroke: "currentColor", "stroke-width": "2", "stroke-linecap": "round", "stroke-linejoin": "round" }, path({ d }))

const fetchDashboard = async () => {
    try {
        const headers = { "ngrok-skip-browser-warning": "true" }
        if (user.val.api_key) {
            headers["X-API-KEY"] = user.val.api_key
        } else if (user.val.access_token) {
            headers["Authorization"] = `Bearer ${user.val.access_token}`
        }

        const res = await fetch(`${API_BASE_URL}/v1/dashboard`, { headers })
        if (!res.ok) {
            if (res.status === 401) logout()
            throw new Error("Failed to load dashboard data")
        }
        dashData.val = await res.json()
        
        if (dashData.val.api_key && !user.val.api_key) {
            user.val = { ...user.val, api_key: dashData.val.api_key }
            localStorage.setItem("rta_user", JSON.stringify(user.val))
        }
    } catch (e) {
        error.val = e.message
    } finally {
        isLoading.val = false
    }
}

fetchDashboard()

const OSButton = (os, label) => button({
    class: selectedOS.val === os ? "btn-ghost active" : "btn-ghost",
    onclick: () => selectedOS.val = os
}, label)

const SupportBot = () => {
    const chatOpen = van.state(false)
    const chatMessages = van.state([{ role: "assistant", content: "Hello! I'm the Rta assistant. How can I help you build with Rta today?" }])
    const chatInput = van.state("")
    const isTyping = van.state(false)

    const sendChatMessage = async () => {
        if (!chatInput.val.trim() || isTyping.val) return
        
        const userMsg = chatInput.val
        chatMessages.val = [...chatMessages.val, { role: "user", content: userMsg }]
        chatInput.val = ""
        isTyping.val = true

        try {
            const res = await fetch(`${API_BASE_URL}/v1/proxy`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "X-API-KEY": user.val.api_key,
                },
                body: JSON.stringify({
                    provider: "gemini",
                    model: "gemini-1.5-flash",
                    messages: [
                        { role: "system", content: "You are the Rta Support Bot. Rta is a mobile-first, AI-assisted code editor for Android and a powerful CLI for Linux/Win. Installation: 'sudo mv rta /usr/local/bin/' on Linux. Usage: 'rta login', then 'rta chat'. Rta is built for speed and surgical precision. Be concise, helpful, and technical." },
                        ...chatMessages.val
                    ]
                })
            })
            const data = await res.json()
            if (data.error) throw new Error(data.error)
            chatMessages.val = [...chatMessages.val, { role: "assistant", content: data.content }]
        } catch (e) {
            chatMessages.val = [...chatMessages.val, { role: "assistant", content: "Error: " + e.message }]
        } finally {
            isTyping.val = false
        }
    }

    return div({ class: "chatbot-container" },
        () => chatOpen.val ? div({ class: "chat-window" },
            div({ class: "chat-header" },
                span({ style: "color: var(--accent-purple); font-weight: 700; font-size: 0.9rem;" }, "Rta Support"),
                button({ class: "btn-ghost", onclick: () => chatOpen.val = false, style: "padding: 4px; border:none;" }, "✕")
            ),
            div({ class: "chat-messages" },
                chatMessages.val.map(m => div({ class: `chat-msg ${m.role}` }, m.content)),
                () => isTyping.val ? div({ style: "font-size: 0.75rem; color: var(--text-muted); padding: 0.5rem;" }, "Rta is thinking...") : ""
            ),
            div({ class: "chat-input-area" },
                input({ 
                    class: "chat-input",
                    placeholder: "Ask anything...", 
                    value: chatInput,
                    oninput: (e) => chatInput.val = e.target.value,
                    onkeydown: (e) => e.key === "Enter" && sendChatMessage()
                }),
                button({ class: "btn-ghost", onclick: sendChatMessage, style: "background: var(--accent-purple); color: white; border: none; border-radius: 4px; padding: 0 1rem;" }, "Send")
            )
        ) : "",
        button({ 
            class: () => chatOpen.val ? "chat-trigger open" : "chat-trigger", 
            onclick: () => chatOpen.val = !chatOpen.val
        }, Icon("M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z", "24"))
    )
}

const Dashboard = () => {
    return div({ style: "position: relative; height: 100vh; width: 100vw;" },
        div({ class: "app-shell" },
            nav({ class: "sidebar" },
                div({ class: "sidebar-logo" }, "rta"),
                div({ class: "nav-group" },
                    div({ class: "nav-label" }, "Management"),
                    div({ class: "nav-item active" }, Icon("M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"), "Dashboard"),
                    div({ class: "nav-item" }, Icon("M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"), "Projects"),
                    div({ class: "nav-item" }, Icon("M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"), "Security")
                ),
                div({ class: "nav-group" },
                    div({ class: "nav-label" }, "Account"),
                    div({ class: "nav-item" }, Icon("M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"), "Profile"),
                    div({ class: "nav-item" }, Icon("M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"), "Alerts")
                ),
                div({ style: "margin-top: auto;" },
                    div({ class: "nav-item", onclick: logout }, Icon("M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"), "Sign Out")
                )
            ),

            main({ class: "main-canvas" },
                () => {
                    if (isLoading.val) return div({ style: "padding: 2rem; color: var(--text-primary);" }, "Loading dashboard...")
                    if (error.val) return div({ style: "padding: 2rem; color: var(--status-error);" }, error.val)
                    const d = dashData.val
                    if (!d) return div()

                    const metrics = [
                        { label: "Today's Calls", value: `${d.usage.calls_today} / ${d.usage.calls_limit_day}`, color: "var(--accent-emerald)" },
                        { label: "Monthly Tokens", value: `${d.usage.tokens_used_month.toLocaleString()} / ${d.usage.tokens_limit_month.toLocaleString()}`, color: "var(--accent-blue)" },
                        { label: "Subscription Tier", value: d.tier.toUpperCase(), color: "var(--status-warning)" }
                    ]

                    const activities = (d.recent_calls || []).map(c => ({
                        time: new Date(c.created_at).toLocaleTimeString(),
                        event: `${c.model_used || "Unknown Model"} via ${c.provider}`,
                        status: "success",
                        color: "var(--accent-emerald)"
                    }))

                    if (activities.length === 0) {
                        activities.push({
                            time: "Now",
                            event: "No recent AI requests logged.",
                            status: "active",
                            color: "var(--accent-blue)"
                        })
                    }

                    return div({ class: "content-grid" },
                        div({ style: "grid-column: 1 / -1; margin-bottom: 1rem;" },
                            h2({ style: "color: var(--text-primary); font-size: 1.5rem; letter-spacing: -0.02em;" }, `Welcome, ${d.username || "Developer"}`),
                            p({ style: "color: var(--text-muted); font-size: 0.875rem;" }, `Member since ${new Date(d.member_since).toLocaleDateString()}`)
                        ),
                        ...metrics.map(m => div({ class: "card" },
                            div({ class: "card-header" },
                                span({ class: "card-title" }, m.label),
                                Icon("M22 12h-4l-3 9L9 3l-3 9H2")
                            ),
                            div({ class: "metric-value" }, m.value)
                        )),
                        div({ class: "card api-well", style: "grid-column: 1 / -1;" },
                            span({ class: "card-title" }, "System Authentication"),
                            p({ style: "font-size: 0.8125rem; color: var(--text-muted); margin-top: 0.5rem;" }, `Primary root key for CLI operations. (Hint: ${d.api_key_hint})`),
                            span({ class: "mono-key" }, () => keyVisible.val ? (user.val.api_key || "No key defined") : "••••••••••••••••••••••••••••••••"),
                            div({ style: "display: flex; gap: 0.75rem;" },
                                button({ class: "btn-ghost", onclick: () => keyVisible.val = !keyVisible.val }, "Toggle Visibility"),
                                button({ class: "btn-ghost", onclick: () => user.val.api_key && navigator.clipboard.writeText(user.val.api_key) }, "Copy Secret")
                            )
                        ),
                        div({ class: "card", style: "grid-column: 1 / -1; border: 1px solid var(--accent-purple);" },
                            div({ class: "card-header" },
                                span({ class: "card-title", style: "color: var(--accent-purple);" }, "CLI Downloads"),
                                Icon("M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4")
                            ),
                            div({ style: "display: flex; gap: 0.75rem; margin-top: 1rem;" },
                                OSButton("linux", "Linux"),
                                OSButton("macos", "macOS"),
                                OSButton("windows", "Windows")
                            ),
                            div({ style: "margin-top: 1rem;" },
                                () => selectedOS.val === "linux" ? a({
                                    href: "/rta",
                                    class: "download-btn",
                                    download: "rta"
                                }, "Download for Linux (x64)") : 
                                selectedOS.val === "windows" ? a({
                                    href: "/rta.exe",
                                    class: "download-btn",
                                    download: "rta.exe"
                                }, "Download for Windows (.exe)") : 
                                a({
                                    href: "#",
                                    class: "download-btn",
                                    style: "opacity: 0.6; cursor: not-allowed; background: #444; box-shadow: none;",
                                    onclick: (e) => { e.preventDefault(); alert("macOS binary coming soon!") }
                                }, "macOS — Coming Soon"),
                                p({ style: "color: var(--text-muted); font-size: 0.8125rem; margin-top: 0.5rem;" }, () => `v0.2.0 stable release for ${selectedOS.val}.`)
                            )
                        ),
                        div({ class: "card activity-section", style: "grid-column: 1 / -1;" },
                            span({ class: "card-title" }, "Recent AI Requests"),
                            div({ style: "margin-top: 1rem;" },
                                activities.map(a => div({ class: "activity-row" },
                                    div({ class: "status-indicator", style: `background: ${a.color};` }),
                                    span({ style: "color: var(--text-primary); font-family: var(--font-mono);" }, a.event),
                                    span({ style: "color: var(--text-muted); font-size: 0.75rem; margin-left: auto;" }, a.time)
                                ))
                            )
                        )
                    )
                }
            )
        ),
        SupportBot()
    )
}

van.add(document.getElementById("dash-app"), Dashboard())
