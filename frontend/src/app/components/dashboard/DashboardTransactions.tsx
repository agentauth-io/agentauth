import { useState, useEffect } from "react";

interface Transaction {
    id: string;
    user_id: string;
    developer_id: string;
    intent: string | null;
    max_amount: number;
    currency: string;
    is_active: boolean;
    created_at: string | null;
    expires_at: string | null;
}

interface DashboardTransactionsProps {
    apiUrl: string;
    token: string;
    apiKey: string;
}

export function DashboardTransactions({ apiUrl, token, apiKey }: DashboardTransactionsProps) {
    const [transactions, setTransactions] = useState<Transaction[]>([]);
    const [total, setTotal] = useState(0);
    const [offset, setOffset] = useState(0);
    const [loading, setLoading] = useState(true);
    const limit = 20;

    const fetchTransactions = async (off: number) => {
        setLoading(true);
        try {
            const res = await fetch(`${apiUrl}/v1/dashboard/transactions?limit=${limit}&offset=${off}`, {
                headers: {
                    Authorization: `Bearer ${token}`,
                    "X-API-Key": apiKey,
                },
            });
            if (res.ok) {
                const data = await res.json();
                setTransactions(data.transactions || []);
                setTotal(data.total || 0);
            }
        } catch {
            // Keep existing state
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchTransactions(offset);
    }, [offset]);

    const formatDate = (iso: string | null) => {
        if (!iso) return "—";
        const d = new Date(iso);
        return d.toLocaleDateString("en-US", { month: "short", day: "numeric", hour: "2-digit", minute: "2-digit" });
    };

    const totalPages = Math.ceil(total / limit);
    const currentPage = Math.floor(offset / limit) + 1;

    return (
        <>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "1rem" }}>
                <div style={{ fontFamily: "var(--nuc-font-mono)", fontSize: "0.7rem", color: "var(--nuc-text-dim)" }}>
                    {total} total consent{total !== 1 ? "s" : ""}
                </div>
                <button className="nuc-btn nuc-btn-sm" onClick={() => fetchTransactions(offset)}>
                    ↻ Refresh
                </button>
            </div>

            <div className="nuc-card">
                <div className="nuc-table-wrap">
                    <table className="nuc-table">
                        <thead>
                            <tr>
                                <th>Consent ID</th>
                                <th>Intent</th>
                                <th>Amount</th>
                                <th>Status</th>
                                <th>Created</th>
                                <th>Expires</th>
                            </tr>
                        </thead>
                        <tbody>
                            {loading && transactions.length === 0 ? (
                                <tr>
                                    <td colSpan={6} style={{ textAlign: "center", color: "var(--nuc-text-muted)", padding: "2rem" }}>
                                        Loading…
                                    </td>
                                </tr>
                            ) : transactions.length === 0 ? (
                                <tr>
                                    <td colSpan={6} style={{ textAlign: "center", color: "var(--nuc-text-muted)", padding: "2rem" }}>
                                        No transactions yet
                                    </td>
                                </tr>
                            ) : (
                                transactions.map((tx) => (
                                    <tr key={tx.id}>
                                        <td className="mono" style={{ maxWidth: 180, overflow: "hidden", textOverflow: "ellipsis" }}>
                                            {tx.id}
                                        </td>
                                        <td>{tx.intent || "—"}</td>
                                        <td className="mono">
                                            {tx.currency} {tx.max_amount.toFixed(2)}
                                        </td>
                                        <td>
                                            <span className={`nuc-badge ${tx.is_active ? "active" : "expired"}`}>
                                                {tx.is_active ? "● Active" : "○ Expired"}
                                            </span>
                                        </td>
                                        <td className="mono">{formatDate(tx.created_at)}</td>
                                        <td className="mono">{formatDate(tx.expires_at)}</td>
                                    </tr>
                                ))
                            )}
                        </tbody>
                    </table>
                </div>

                {/* Pagination */}
                {totalPages > 1 && (
                    <div style={{ display: "flex", justifyContent: "center", gap: "0.5rem", padding: "1rem 0 0", alignItems: "center" }}>
                        <button
                            className="nuc-btn nuc-btn-sm"
                            disabled={offset === 0}
                            onClick={() => setOffset(Math.max(0, offset - limit))}
                        >
                            ← Prev
                        </button>
                        <span style={{ fontFamily: "var(--nuc-font-mono)", fontSize: "0.7rem", color: "var(--nuc-text-dim)" }}>
                            Page {currentPage} of {totalPages}
                        </span>
                        <button
                            className="nuc-btn nuc-btn-sm"
                            disabled={offset + limit >= total}
                            onClick={() => setOffset(offset + limit)}
                        >
                            Next →
                        </button>
                    </div>
                )}
            </div>
        </>
    );
}
