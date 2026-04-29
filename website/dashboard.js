import van from "vanjs-core"

const { div, h2, p, main, span, button, svg, path, nav } = van.tags

const API_BASE_URL = import.meta.env.VITE_BACKEND_URL || "http://localhost:8000"

// State
const user = van.state(JSON.parse(localStorage.getItem("rta_user") || "null"))
const keyVisible = van.state(false)
const dashData = van.state(null)
const error = van.state(null)
const isLoading = van.state(true)

if (!user.val) { window.location.href = "/" }

const logout = () => {
    localStorage.removeItem("rta_user")
    window.location.href = "/"
}

const Icon = (d) => svg({ width: "18", height: "18", viewBox: "0 0 24 24", fill: "none", stroke: "currentColor", "stroke-width": "2", "stroke-linecap": "round", "stroke-linejoin": "round" }, path({ d }))

const fetchDashboard = async () => {
    try {
        const res = await fetch(`${API_BASE_URL}/v1/dashboard`, {
            headers: {
                "X-API-KEY": user.val.api_key,
                "ngrok-skip-browser-warning": "true"
            }
        })
        if (!res.ok) {
            if (res.status === 401) logout()
            throw new Error("Failed to load dashboard data")
        }
        dashData.val = await res.json()
    } catch (e) {
        error.val = e.message
    } finally {
        isLoading.val = false
    }
}

fetchDashboard()

const Dashboard = () => {
    return div({ class: "app-shell" },
        // Sidebar
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

        // Main
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
                    // Welcome
                    div({ style: "grid-column: 1 / -1; margin-bottom: 1rem;" },
                        h2({ style: "color: var(--text-primary); font-size: 1.5rem; letter-spacing: -0.02em;" }, `Welcome, ${d.username || "Developer"}`),
                        p({ style: "color: var(--text-muted); font-size: 0.875rem;" }, `Member since ${new Date(d.member_since).toLocaleDateString()}`)
                    ),

                    // Metrics
                    ...metrics.map(m => div({ class: "card" },
                        div({ class: "card-header" },
                            span({ class: "card-title" }, m.label),
                            Icon("M22 12h-4l-3 9L9 3l-3 9H2")
                        ),
                        div({ class: "metric-value" }, m.value)
                    )),

                    // API Key
                    div({ class: "card api-well", style: "grid-column: 1 / -1;" },
                        span({ class: "card-title" }, "System Authentication"),
                        p({ style: "font-size: 0.8125rem; color: var(--text-muted); margin-top: 0.5rem;" }, `Primary root key for CLI operations. (Hint: ${d.api_key_hint})`),
                        span({ class: "mono-key" }, () => keyVisible.val ? (user.val.api_key || "No key defined") : "••••••••••••••••••••••••••••••••"),
                        div({ style: "display: flex; gap: 0.75rem;" },
                            button({ class: "btn-ghost", onclick: () => keyVisible.val = !keyVisible.val }, "Toggle Visibility"),
                            button({ class: "btn-ghost", onclick: () => user.val.api_key && navigator.clipboard.writeText(user.val.api_key) }, "Copy Secret")
                        )
                    ),

                    // Recent Events
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
    )
}

van.add(document.getElementById("dash-app"), Dashboard())
