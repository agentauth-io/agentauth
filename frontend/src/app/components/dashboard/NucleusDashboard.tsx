import { useState, useEffect } from "react";
import "../../../styles/nucleus.css";
import { DashboardLogin } from "./DashboardLogin";
import { DashboardOverview } from "./DashboardOverview";
import { DashboardTransactions } from "./DashboardTransactions";
import { DashboardApiKeys } from "./DashboardApiKeys";
import { DashboardModules } from "./DashboardModules";
import { DashboardStripe } from "./DashboardStripe";

type Tab = "overview" | "transactions" | "api-keys" | "stripe" | "modules";

const API_URL = import.meta.env.VITE_API_URL || "https://agentauth-api-agentauth.koyeb.app";
const STORED_API_KEY = import.meta.env.VITE_API_KEY || "";

const NAV_ITEMS: { id: Tab; icon: string; label: string }[] = [
    { id: "overview", icon: "◎", label: "Overview" },
    { id: "transactions", icon: "⇌", label: "Transactions" },
    { id: "api-keys", icon: "⚿", label: "API Keys" },
    { id: "stripe", icon: "◆", label: "Stripe" },
    { id: "modules", icon: "⬡", label: "Modules" },
];

export function NucleusDashboard() {
    const [token, setToken] = useState<string | null>(() => sessionStorage.getItem("nuc_token"));
    const [tab, setTab] = useState<Tab>("overview");
    const [apiKey, setApiKey] = useState(STORED_API_KEY);
    const [showKeyInput, setShowKeyInput] = useState(false);

    // Verify stored token on mount
    useEffect(() => {
        if (!token) return;
        (async () => {
            try {
                const res = await fetch(`${API_URL}/v1/admin/verify`, {
                    headers: { Authorization: `Bearer ${token}` },
                });
                if (!res.ok) {
                    sessionStorage.removeItem("nuc_token");
                    setToken(null);
                }
            } catch {
                // Allow offline
            }
        })();
    }, []);

    const handleLogout = () => {
        // Try to revoke server-side
        if (token) {
            fetch(`${API_URL}/v1/admin/logout`, {
                method: "POST",
                headers: { Authorization: `Bearer ${token}` },
            }).catch(() => { });
        }
        sessionStorage.removeItem("nuc_token");
        setToken(null);
    };

    if (!token) {
        return <DashboardLogin apiUrl={API_URL} onLogin={setToken} />;
    }

    const TAB_TITLES: Record<Tab, string> = {
        overview: "Dashboard Overview",
        transactions: "Transactions",
        "api-keys": "API Key Management",
        stripe: "Stripe Sandbox",
        modules: "System Modules",
    };

    return (
        <div className="nuc-shell">
            {/* Sidebar */}
            <aside className="nuc-sidebar">
                <div className="nuc-sidebar-brand">
                    <div className="nuc-logo">⊘</div>
                    <div>
                        <h1>Nucleus</h1>
                        <span>Admin Console</span>
                    </div>
                </div>

                <nav className="nuc-nav">
                    {NAV_ITEMS.map((item) => (
                        <button
                            key={item.id}
                            className={`nuc-nav-item ${tab === item.id ? "active" : ""}`}
                            onClick={() => setTab(item.id)}
                        >
                            <span className="nav-icon">{item.icon}</span>
                            {item.label}
                        </button>
                    ))}

                    <div className="nuc-nav-spacer" />

                    {/* API Key Configuration */}
                    <button
                        className="nuc-nav-item"
                        onClick={() => setShowKeyInput(!showKeyInput)}
                    >
                        <span className="nav-icon">⚙</span>
                        Configure
                    </button>

                    <button className="nuc-nav-item" onClick={handleLogout} style={{ color: "var(--nuc-red)" }}>
                        <span className="nav-icon">↪</span>
                        Sign Out
                    </button>
                </nav>

                <div className="nuc-sidebar-footer">
                    <span className="nuc-env-badge">● Production</span>
                </div>
            </aside>

            {/* Main Content */}
            <main className="nuc-main">
                <div className="nuc-header">
                    <h2>{TAB_TITLES[tab]}</h2>
                    <div className="nuc-header-actions">
                        {showKeyInput && (
                            <input
                                className="nuc-input"
                                style={{ maxWidth: 280, fontSize: "0.72rem" }}
                                placeholder="API Key (for dashboard data)"
                                value={apiKey}
                                onChange={(e) => setApiKey(e.target.value)}
                            />
                        )}
                        <div style={{ fontFamily: "var(--nuc-font-mono)", fontSize: "0.6rem", color: "var(--nuc-text-muted)" }}>
                            {new Date().toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" })}
                        </div>
                    </div>
                </div>

                {tab === "overview" && (
                    <DashboardOverview apiUrl={API_URL} token={token} apiKey={apiKey} />
                )}
                {tab === "transactions" && (
                    <DashboardTransactions apiUrl={API_URL} token={token} apiKey={apiKey} />
                )}
                {tab === "api-keys" && (
                    <DashboardApiKeys apiUrl={API_URL} token={token} />
                )}
                {tab === "stripe" && (
                    <DashboardStripe token={token} />
                )}
                {tab === "modules" && (
                    <DashboardModules apiUrl={API_URL} token={token} apiKey={apiKey} />
                )}
            </main>
        </div>
    );
}
