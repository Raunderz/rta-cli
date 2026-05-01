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

const Icon = (d, size = "16") => svg({ width: size, height: size, viewBox: "0 0 24 24", fill: "none", stroke: "currentColor", "stroke-width": "2", "stroke-linecap": "round", "stroke-linejoin": "round" }, path({ d }))

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
    class: () => selectedOS.val === os ? "btn-ghost active" : "btn-ghost",
    onclick: () => selectedOS.val = os
}, label)

const SupportBot = () => {
    const chatOpen = van.state(false)
    const chatMessages = van.state([{ role: "assistant", content: "Hello! I'm the Rta assistant. How can I help you today?" }])
    const chatInput = van.state("")
    const isTyping = van.state(false)

    const sendChatMessage = async () => {
        if (!chatInput.val.trim() || isTyping.val) return
        
        const userMsg = chatInput.val
        chatMessages.val = [...chatMessages.val, { role: "user", content: userMsg }]
        chatInput.val = ""
        isTyping.val = true

        try {
            const res = await fetch(`${API_BASE_URL}/v1/chat`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "X-API-KEY": user.val.api_key,
                    "ngrok-skip-browser-warning": "true"
                },
                body: JSON.stringify({
                    messages: [
                        { role: "system", content: "You are the Rta Support Bot. Rta is a professional code editor and CLI. Be concise and technical." },
                        ...chatMessages.val
                    ],
                    model: "auto",
                    provider: "auto"
                })
            })
            const data = await res.json()
            if (!res.ok) throw new Error(data.detail || "Chat failed")
            
            const assistantMsg = data.choices[0].message.content
            chatMessages.val = [...chatMessages.val, { role: "assistant", content: assistantMsg }]
        } catch (e) {
            chatMessages.val = [...chatMessages.val, { role: "assistant", content: "Error: " + e.message }]
        } finally {
            isTyping.val = false
        }
    }

    return div({ class: "chatbot-container" },
        () => chatOpen.val ? div({ class: "chat-window" },
            div({ class: "chat-header" },
                span({ style: "font-weight: 600; font-size: 13px;" }, "Support"),
                button({ class: "btn-ghost", onclick: () => chatOpen.val = false, style: "padding: 2px; border:none;" }, Icon("M18 6L6 18M6 6l12 12"))
            ),
            div({ class: "chat-messages" },
                chatMessages.val.map(m => div({ class: `chat-msg ${m.role}` }, m.content)),
                () => isTyping.val ? div({ style: "font-size: 11px; color: var(--text-muted); padding: 0.5rem;" }, "Thinking...") : ""
            ),
            div({ class: "chat-input-area" },
                input({ 
                    class: "chat-input",
                    placeholder: "Ask a question...", 
                    value: chatInput,
                    oninput: (e) => chatInput.val = e.target.value,
                    onkeydown: (e) => e.key === "Enter" && sendChatMessage()
                }),
                button({ class: "btn-ghost active", onclick: sendChatMessage, style: "border: none; padding: 0 12px;" }, Icon("M22 2L11 13M22 2l-7 20-4-9-9-4 20-7z"))
            )
        ) : "",
        button({ class: "chat-trigger", onclick: () => chatOpen.val = !chatOpen.val }, Icon("M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z", "20"))
    )
}

const Dashboard = () => {
    return div({ style: "position: relative; height: 100vh; width: 100vw;" },
        div({ class: "app-shell" },
            nav({ class: "sidebar" },
                a({ href: "/", class: "sidebar-logo" }, "rta"),
                div({ class: "nav-group" },
                    div({ class: "nav-label" }, "Overview"),
                    div({ class: "nav-item active" }, Icon("M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"), "Dashboard"),
                    div({ class: "nav-item" }, Icon("M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"), "Projects")
                ),
                div({ class: "nav-group" },
                    div({ class: "nav-label" }, "Settings"),
                    div({ class: "nav-item" }, Icon("M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"), "Profile"),
                    div({ class: "nav-item" }, Icon("M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"), "Alerts")
                ),
                div({ style: "margin-top: auto;" },
                    div({ class: "nav-item", onclick: logout }, Icon("M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"), "Logout")
                )
            ),

            main({ class: "main-canvas" },
                () => {
                    if (isLoading.val) return div({ style: "color: var(--text-muted); font-size: 14px;" }, "Loading...")
                    if (error.val) return div({ style: "color: #EF4444;" }, "Error: " + error.val)
                    const d = dashData.val
                    if (!d) return div()

                    const metrics = [
                        { label: "Daily Calls", value: `${d.usage.calls_today} / ${d.usage.calls_limit_day}`, icon: "M22 12h-4l-3 9L9 3l-3 9H2" },
                        { label: "Tokens Used", value: d.usage.tokens_used_month.toLocaleString(), icon: "M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" },
                        { label: "Current Tier", value: d.tier.toUpperCase(), icon: "M12 11c0 3.517-1.009 6.799-2.753 9.571m-3.44-2.04l.054-.09A10.003 10.003 0 0012 21" }
                    ]

                    const activities = (d.recent_calls || []).map(c => ({
                        time: new Date(c.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
                        event: c.model_used || "AI Request",
                        provider: c.provider
                    }))

                    return div({ class: "content-grid" },
                        div({ style: "grid-column: 1 / -1; margin-bottom: 32px;" },
                            h2({ style: "font-size: 24px; margin: 0;" }, `Welcome back, ${d.username}`),
                            p({ style: "color: var(--text-muted); margin-top: 4px; font-size: 14px;" }, `Member since ${new Date(d.member_since).toLocaleDateString()}`)
                        ),
                        ...metrics.map(m => div({ class: "card" },
                            div({ class: "card-header" },
                                span({ class: "card-title" }, m.label),
                                Icon(m.icon)
                            ),
                            div({ class: "metric-value" }, m.value)
                        )),
                        div({ class: "card api-well" },
                            span({ class: "card-title" }, "API Key"),
                            span({ class: "mono-key" }, () => keyVisible.val ? (user.val.api_key || "UNSET") : "••••••••••••••••••••••••••••••••"),
                            div({ style: "display: flex; gap: 8px;" },
                                button({ class: "btn-ghost", onclick: () => keyVisible.val = !keyVisible.val }, "Reveal"),
                                button({ class: "btn-ghost", onclick: () => user.val.api_key && navigator.clipboard.writeText(user.val.api_key) }, "Copy")
                            )
                        ),
                        div({ class: "card", style: "grid-column: span 3;" },
                            span({ class: "card-title" }, "Recent Activity"),
                            div({ style: "margin-top: 16px;" },
                                activities.length > 0 ? activities.map(a => div({ class: "activity-row" },
                                    div({ class: "status-indicator", style: "background: #10B981;" }),
                                    div({ style: "display: flex; flex-direction: column;" },
                                        span({ style: "font-weight: 500;" }, a.event),
                                        span({ style: "font-size: 11px; color: var(--text-muted);" }, a.provider)
                                    ),
                                    span({ style: "color: var(--text-muted); font-size: 11px; font-family: var(--font-mono);" }, a.time)
                                )) : p({ style: "color: var(--text-muted); font-size: 13px;" }, "No recent activity.")
                            )
                        ),
                        div({ class: "card", style: "grid-column: span 3;" },
                            span({ class: "card-title" }, "Releases"),
                            div({ style: "display: flex; gap: 8px; margin: 20px 0;" },
                                OSButton("linux", "Linux"),
                                OSButton("windows", "Windows")
                            ),
                            a({
                                href: selectedOS.val === "linux" ? "/rta" : "/rta.exe",
                                class: "download-btn",
                                download: selectedOS.val === "linux" ? "rta" : "rta.exe"
                            }, `Download for ${selectedOS.val.toUpperCase()}`, Icon("M12 15V3m0 12l-4-4m4 4l4-4"))
                        )
                    )
                }
            )
        ),
        SupportBot()
    )
}

van.add(document.getElementById("dash-app"), Dashboard())
