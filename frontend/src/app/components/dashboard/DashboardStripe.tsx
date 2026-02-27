import { useState, useEffect, useCallback } from "react";

interface StripeTransaction {
    id: string;
    amount: number;
    currency: string;
    status: "authorized" | "denied" | "pending";
    merchant: string;
    created_at: string;
    description: string;
}

interface StripeStats {
    total_authorizations: number;
    transaction_volume: number;
    approval_rate: number;
    avg_response_time: number;
    transactions: StripeTransaction[];
}

type Period = "24h" | "7d" | "30d" | "90d";

// Local dev: Vite stripeProxy plugin at /api/stripe-transactions
// Production: Netlify function at /.netlify/functions/get-stripe-transactions
const STRIPE_API =
    import.meta.env.VITE_STRIPE_API_URL ||
    (import.meta.env.DEV
        ? "/api/stripe-transactions"
        : "/.netlify/functions/get-stripe-transactions");

interface DashboardStripeProps {
    token: string;
}

export function DashboardStripe({ token }: DashboardStripeProps) {
    const [stats, setStats] = useState<StripeStats | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [period, setPeriod] = useState<Period>("30d");
    const [limit, setLimit] = useState(50);

    const fetchStripeData = useCallback(async () => {
        setLoading(true);
        setError(null);
        try {
            const res = await fetch(`${STRIPE_API}?period=${period}&limit=${limit}`, {
                headers: {
                    Authorization: `Bearer ${token}`,
                },
            });
            if (!res.ok) {
                throw new Error(`HTTP ${res.status}: ${res.statusText}`);
            }
            const data: StripeStats = await res.json();
            setStats(data);
        } catch (err) {
            setError(err instanceof Error ? err.message : "Failed to load Stripe data");
        } finally {
            setLoading(false);
        }
    }, [token, period, limit]);

    useEffect(() => {
        fetchStripeData();
    }, [fetchStripeData]);

    const formatCurrency = (amount: number, currency: string) => {
        return new Intl.NumberFormat("en-US", {
            style: "currency",
            currency: currency || "USD",
        }).format(amount);
    };

    const formatDate = (iso: string) => {
        const d = new Date(iso);
        return d.toLocaleDateString("en-US", {
            month: "short",
            day: "numeric",
            hour: "2-digit",
            minute: "2-digit",
        });
    };

    const statusBadge = (status: string) => {
        const cls =
            status === "authorized" ? "active" : status === "denied" ? "revoked" : "expired";
        const icon =
            status === "authorized" ? "✓" : status === "denied" ? "✕" : "◌";
        return (
            <span className={`nuc-badge ${cls}`}>
                {icon} {status.toUpperCase()}
            </span>
        );
    };

    const periods: { label: string; value: Period }[] = [
        { label: "24h", value: "24h" },
        { label: "7 days", value: "7d" },
        { label: "30 days", value: "30d" },
        { label: "90 days", value: "90d" },
    ];

    return (
        <>
            {/* Period selector + Refresh */}
            <div style={{ display: "flex", gap: "0.5rem", marginBottom: "1.25rem", alignItems: "center", flexWrap: "wrap" }}>
                {periods.map((p) => (
                    <button
                        key={p.value}
                        className={`nuc-btn nuc-btn-sm ${period === p.value ? "nuc-btn-primary" : ""}`}
                        onClick={() => setPeriod(p.value)}
                    >
                        {p.label}
                    </button>
                ))}
                <div style={{ flex: 1 }} />
                <select
                    className="nuc-input"
                    style={{ width: "auto", maxWidth: 120, fontSize: "0.72rem", padding: "0.3rem 0.5rem" }}
                    value={limit}
                    onChange={(e) => setLimit(parseInt(e.target.value))}
                >
                    <option value={20}>20 rows</option>
                    <option value={50}>50 rows</option>
                    <option value={100}>100 rows</option>
                </select>
                <button className="nuc-btn nuc-btn-sm" onClick={fetchStripeData}>
                    ↻ Refresh
                </button>
            </div>

            {/* Error state */}
            {error && (
                <div className="nuc-card" style={{ marginBottom: "1rem", borderColor: "var(--nuc-red-dim)" }}>
                    <div style={{ color: "var(--nuc-red)", fontFamily: "var(--nuc-font-mono)", fontSize: "0.75rem" }}>
                        ⚠ {error}
                    </div>
                    <div style={{ color: "var(--nuc-text-muted)", fontSize: "0.7rem", marginTop: "0.5rem" }}>
                        Ensure the Stripe sandbox key is configured and the Netlify function is deployed.
                    </div>
                </div>
            )}

            {/* Loading state */}
            {loading && !stats && (
                <div className="nuc-card" style={{ textAlign: "center", padding: "3rem", color: "var(--nuc-text-dim)" }}>
                    <div style={{ fontFamily: "var(--nuc-font-mono)", fontSize: "0.8rem" }}>
                        Fetching Stripe sandbox data…
                    </div>
                </div>
            )}

            {/* Stats Cards */}
            {stats && (
                <>
                    <div className="nuc-stats-grid">
                        <div className="nuc-stat-card">
                            <div className="nuc-stat-label">Payment Intents</div>
                            <div className="nuc-stat-value">{stats.total_authorizations}</div>
                            <div className="nuc-stat-change" style={{ color: "var(--nuc-text-muted)" }}>
                                Stripe Sandbox · {period}
                            </div>
                        </div>
                        <div className="nuc-stat-card">
                            <div className="nuc-stat-label">Total Volume</div>
                            <div className="nuc-stat-value">
                                {formatCurrency(stats.transaction_volume, "USD")}
                            </div>
                            <div className="nuc-stat-change up">Successful payments</div>
                        </div>
                        <div className="nuc-stat-card">
                            <div className="nuc-stat-label">Approval Rate</div>
                            <div className="nuc-stat-value">{stats.approval_rate}%</div>
                            <div className={`nuc-stat-change ${stats.approval_rate >= 90 ? "up" : "down"}`}>
                                {stats.approval_rate >= 90 ? "↑ Healthy" : "↓ Review needed"}
                            </div>
                        </div>
                        <div className="nuc-stat-card">
                            <div className="nuc-stat-label">Avg Response</div>
                            <div className="nuc-stat-value">{stats.avg_response_time}ms</div>
                            <div className="nuc-stat-change" style={{ color: "var(--nuc-text-muted)" }}>
                                Platform latency
                            </div>
                        </div>
                    </div>

                    {/* Source badge */}
                    <div style={{ display: "flex", alignItems: "center", gap: "0.5rem", marginBottom: "1rem" }}>
                        <span className="nuc-badge active" style={{ background: "rgba(99,91,255,0.15)", color: "#635bff" }}>
                            ◆ Stripe Test Mode
                        </span>
                        <span style={{ fontFamily: "var(--nuc-font-mono)", fontSize: "0.62rem", color: "var(--nuc-text-muted)" }}>
                            {stats.transactions.length} payment intent{stats.transactions.length !== 1 ? "s" : ""} from Stripe sandbox
                        </span>
                    </div>

                    {/* Transactions Table */}
                    <div className="nuc-card">
                        <div className="nuc-table-wrap">
                            <table className="nuc-table">
                                <thead>
                                    <tr>
                                        <th>Payment Intent</th>
                                        <th>Description</th>
                                        <th>Amount</th>
                                        <th>Status</th>
                                        <th>Merchant</th>
                                        <th>Created</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {stats.transactions.length === 0 ? (
                                        <tr>
                                            <td
                                                colSpan={6}
                                                style={{ textAlign: "center", color: "var(--nuc-text-muted)", padding: "2.5rem" }}
                                            >
                                                <div style={{ fontSize: "0.85rem", marginBottom: "0.5rem" }}>No payment intents found</div>
                                                <div style={{ fontFamily: "var(--nuc-font-mono)", fontSize: "0.65rem" }}>
                                                    Create test transactions using the Stripe CLI or AgentAuth demo
                                                </div>
                                            </td>
                                        </tr>
                                    ) : (
                                        stats.transactions.map((tx) => (
                                            <tr key={tx.id}>
                                                <td className="mono" style={{ maxWidth: 220 }}>
                                                    <span
                                                        style={{ cursor: "pointer" }}
                                                        title={tx.id}
                                                        onClick={() => {
                                                            navigator.clipboard.writeText(tx.id);
                                                        }}
                                                    >
                                                        {tx.id.length > 28 ? `${tx.id.slice(0, 14)}…${tx.id.slice(-10)}` : tx.id}
                                                    </span>
                                                </td>
                                                <td>{tx.description}</td>
                                                <td className="mono">{formatCurrency(tx.amount, tx.currency)}</td>
                                                <td>{statusBadge(tx.status)}</td>
                                                <td>{tx.merchant}</td>
                                                <td className="mono">{formatDate(tx.created_at)}</td>
                                            </tr>
                                        ))
                                    )}
                                </tbody>
                            </table>
                        </div>
                    </div>

                    {/* Stripe dashboard link */}
                    <div
                        style={{
                            marginTop: "1rem",
                            display: "flex",
                            gap: "0.75rem",
                            alignItems: "center",
                            justifyContent: "flex-end",
                        }}
                    >
                        <a
                            href="https://dashboard.stripe.com/test/payments"
                            target="_blank"
                            rel="noopener noreferrer"
                            className="nuc-btn nuc-btn-sm"
                            style={{ textDecoration: "none", color: "#635bff" }}
                        >
                            Open Stripe Dashboard ↗
                        </a>
                    </div>
                </>
            )}
        </>
    );
}
