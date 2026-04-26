import van from "vanjs-core"

const { div, h2, p, main, span, button, svg, path, rect, nav } = van.tags

// State
const user = van.state(JSON.parse(localStorage.getItem("rta_user") || "null"))
const keyVisible = van.state(false)

if (!user.val) { window.location.href = "/" }

const logout = () => {
    localStorage.removeItem("rta_user")
    window.location.href = "/"
}

// Icons
const Icon = (d) => svg({ width: "18", height: "18", viewBox: "0 0 24 24", fill: "none", stroke: "currentColor", "stroke-width": "2", "stroke-linecap": "round", "stroke-linejoin": "round" }, path({ d }))

const Dashboard = () => {
    const { user: userData, api_key } = user.val

    const metrics = [
        { label: "Total Requests", value: "42", trend: "+12.4%", color: "var(--accent-emerald)" },
        { label: "Token Usage", value: "1,402", trend: "+2.1%", color: "var(--accent-blue)" },
        { label: "Avg Latency", value: "142ms", trend: "-14ms", color: "var(--status-warning)" },
        { label: "System Uptime", value: "99.9%", trend: "Stable", color: "var(--accent-emerald)" }
    ]

    const graphBars = [30, 45, 25, 60, 80, 45, 90, 70, 40, 55, 30, 65, 50, 40, 75, 85, 40, 60]

    const activities = [
        { time: "14:30:01", event: "CLI_INIT", status: "success", color: "var(--accent-emerald)" },
        { time: "14:28:45", event: "PROJECT_PUSH", status: "success", color: "var(--accent-emerald)" },
        { time: "14:22:12", event: "API_AUTH_FAILURE", status: "error", color: "var(--status-error)" },
        { time: "14:20:05", event: "LOG_STREAM_CONNECT", status: "active", color: "var(--accent-blue)" },
        { time: "14:15:33", event: "VULN_SCAN_COMPLETE", status: "success", color: "var(--accent-emerald)" }
    ]

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
            div({ class: "content-grid" },
                // Metrics
                metrics.map(m => div({ class: "card" },
                    div({ class: "card-header" },
                        span({ class: "card-title" }, m.label),
                        Icon("M22 12h-4l-3 9L9 3l-3 9H2")
                    ),
                    div({ class: "metric-value" }, m.value),
                    div({ class: "metric-trend", style: `color: ${m.color}` }, m.trend)
                )),

                // Activity Viz
                div({ class: "viz-section" },
                    div({ class: "viz-title" }, "Request Flow Activity"),
                    div({ class: "bar-container" },
                        graphBars.map(h => div({ class: "data-bar", style: `height: ${h}%` }))
                    )
                ),

                // API Key
                div({ class: "card api-well" },
                    span({ class: "card-title" }, "System Authentication"),
                    p({ style: "font-size: 0.8125rem; color: var(--text-muted); margin-top: 0.5rem;" }, "Primary root key for CLI operations."),
                    span({ class: "mono-key" }, () => keyVisible.val ? (api_key || "No key defined") : "••••••••••••••••••••••••••••••••"),
                    div({ style: "display: flex; gap: 0.75rem;" },
                        button({ class: "btn-ghost", onclick: () => keyVisible.val = !keyVisible.val }, "Toggle Visibility"),
                        button({ class: "btn-ghost", onclick: () => api_key && navigator.clipboard.writeText(api_key) }, "Copy Secret")
                    )
                ),

                // Recent Events
                div({ class: "card activity-section" },
                    span({ class: "card-title" }, "System Event Log"),
                    div({ style: "margin-top: 1rem;" },
                        activities.map(a => div({ class: "activity-row" },
                            div({ class: "status-indicator", style: `background: ${a.color};` }),
                            span({ style: "color: var(--text-primary); font-family: var(--font-mono);" }, a.event),
                            span({ style: "color: var(--text-muted); font-size: 0.75rem;" }, a.time)
                        ))
                    )
                )
            )
        )
    )
}

van.add(document.getElementById("dash-app"), Dashboard())
