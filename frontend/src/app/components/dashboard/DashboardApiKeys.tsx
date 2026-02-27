import { useState, useEffect } from "react";

interface ApiKeyInfo {
    id: string;
    owner: string;
    prefix: string;
    is_active: boolean;
    created_at: string;
}

interface DashboardApiKeysProps {
    apiUrl: string;
    token: string;
}

export function DashboardApiKeys({ apiUrl, token }: DashboardApiKeysProps) {
    const [keys, setKeys] = useState<ApiKeyInfo[]>([]);
    const [loading, setLoading] = useState(true);
    const [newKey, setNewKey] = useState<string | null>(null);
    const [creating, setCreating] = useState(false);
    const [owner, setOwner] = useState("default");

    const headers = {
        Authorization: `Bearer ${token}`,
        "Content-Type": "application/json",
    };

    const fetchKeys = async () => {
        setLoading(true);
        try {
            const res = await fetch(`${apiUrl}/v1/admin/api-keys`, { headers });
            if (res.ok) {
                const data = await res.json();
                setKeys(data.keys || []);
            }
        } catch {
            // Keep current state
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchKeys();
    }, []);

    const createKey = async () => {
        setCreating(true);
        setNewKey(null);
        try {
            const res = await fetch(`${apiUrl}/v1/admin/api-keys?owner=${encodeURIComponent(owner)}`, {
                method: "POST",
                headers,
            });
            if (res.ok) {
                const data = await res.json();
                setNewKey(data.key || data.api_key);
                fetchKeys();
            }
        } catch {
            // Handle error
        } finally {
            setCreating(false);
        }
    };

    const revokeKey = async (keyId: string) => {
        if (!confirm("Revoke this API key? This cannot be undone.")) return;
        try {
            await fetch(`${apiUrl}/v1/admin/api-keys/${keyId}`, {
                method: "DELETE",
                headers,
            });
            fetchKeys();
        } catch {
            // Handle error
        }
    };

    const rotateKey = async (keyId: string) => {
        if (!confirm("Rotate this key? The old key will stop working immediately.")) return;
        try {
            const res = await fetch(`${apiUrl}/v1/admin/api-keys/${keyId}/rotate`, {
                method: "POST",
                headers,
            });
            if (res.ok) {
                const data = await res.json();
                setNewKey(data.new_key || data.key);
                fetchKeys();
            }
        } catch {
            // Handle error
        }
    };

    const formatDate = (iso: string) => {
        const d = new Date(iso);
        return d.toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" });
    };

    const copyToClipboard = (text: string) => {
        navigator.clipboard.writeText(text);
    };

    return (
        <>
            {/* Create Key */}
            <div className="nuc-card" style={{ marginBottom: "1rem" }}>
                <div className="nuc-chart-title">Generate New API Key</div>
                <div style={{ display: "flex", gap: "0.5rem", alignItems: "center", marginTop: "0.75rem" }}>
                    <input
                        className="nuc-input"
                        style={{ maxWidth: 200 }}
                        placeholder="Owner label"
                        value={owner}
                        onChange={(e) => setOwner(e.target.value)}
                    />
                    <button className="nuc-btn nuc-btn-primary" onClick={createKey} disabled={creating}>
                        {creating ? "Creating…" : "Generate Key"}
                    </button>
                </div>

                {newKey && (
                    <div style={{ marginTop: "0.75rem" }}>
                        <div style={{ fontFamily: "var(--nuc-font-mono)", fontSize: "0.65rem", color: "var(--nuc-text-dim)", marginBottom: "0.3rem" }}>
                            ⚠ Copy this key now — it won't be shown again
                        </div>
                        <div className="nuc-key-display" onClick={() => copyToClipboard(newKey)} title="Click to copy">
                            {newKey}
                        </div>
                    </div>
                )}
            </div>

            {/* Keys Table */}
            <div className="nuc-card">
                <div className="nuc-table-wrap">
                    <table className="nuc-table">
                        <thead>
                            <tr>
                                <th>Key ID</th>
                                <th>Prefix</th>
                                <th>Owner</th>
                                <th>Status</th>
                                <th>Created</th>
                                <th>Actions</th>
                            </tr>
                        </thead>
                        <tbody>
                            {loading ? (
                                <tr>
                                    <td colSpan={6} style={{ textAlign: "center", color: "var(--nuc-text-muted)", padding: "2rem" }}>
                                        Loading…
                                    </td>
                                </tr>
                            ) : keys.length === 0 ? (
                                <tr>
                                    <td colSpan={6} style={{ textAlign: "center", color: "var(--nuc-text-muted)", padding: "2rem" }}>
                                        No API keys found
                                    </td>
                                </tr>
                            ) : (
                                keys.map((k) => (
                                    <tr key={k.id}>
                                        <td className="mono">{k.id}</td>
                                        <td className="mono">{k.prefix}…</td>
                                        <td>{k.owner}</td>
                                        <td>
                                            <span className={`nuc-badge ${k.is_active ? "active" : "revoked"}`}>
                                                {k.is_active ? "● Active" : "● Revoked"}
                                            </span>
                                        </td>
                                        <td className="mono">{formatDate(k.created_at)}</td>
                                        <td>
                                            {k.is_active && (
                                                <div style={{ display: "flex", gap: "0.3rem" }}>
                                                    <button className="nuc-btn nuc-btn-sm" onClick={() => rotateKey(k.id)}>
                                                        ↻ Rotate
                                                    </button>
                                                    <button className="nuc-btn nuc-btn-sm nuc-btn-danger" onClick={() => revokeKey(k.id)}>
                                                        Revoke
                                                    </button>
                                                </div>
                                            )}
                                        </td>
                                    </tr>
                                ))
                            )}
                        </tbody>
                    </table>
                </div>
            </div>
        </>
    );
}
