import { useState, FormEvent } from "react";
import "../../../styles/nucleus.css";

interface DashboardLoginProps {
    onLogin: (token: string) => void;
    apiUrl: string;
}

export function DashboardLogin({ onLogin, apiUrl }: DashboardLoginProps) {
    const [password, setPassword] = useState("");
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState("");

    const handleSubmit = async (e: FormEvent) => {
        e.preventDefault();
        setLoading(true);
        setError("");

        try {
            const res = await fetch(`${apiUrl}/v1/admin/login`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ password }),
            });

            if (!res.ok) {
                const data = await res.json().catch(() => ({ detail: "Login failed" }));
                throw new Error(data.detail || "Invalid credentials");
            }

            const data = await res.json();
            sessionStorage.setItem("nuc_token", data.token);
            onLogin(data.token);
        } catch (err: unknown) {
            setError(err instanceof Error ? err.message : "Connection failed");
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="nuc-login-screen">
            <div className="nuc-login-card">
                <div className="nuc-login-logo">⊘</div>
                <div className="nuc-login-title">Nucleus</div>
                <div className="nuc-login-sub">AgentAuth Admin Dashboard</div>

                <form className="nuc-login-form" onSubmit={handleSubmit}>
                    {error && <div className="nuc-login-error">{error}</div>}

                    <input
                        className="nuc-input"
                        type="password"
                        placeholder="Admin password"
                        value={password}
                        onChange={(e) => setPassword(e.target.value)}
                        autoFocus
                        disabled={loading}
                    />

                    <button
                        className="nuc-btn nuc-btn-primary"
                        type="submit"
                        disabled={loading || !password}
                        style={{ opacity: loading ? 0.6 : 1 }}
                    >
                        {loading ? "Authenticating…" : "Sign In →"}
                    </button>
                </form>

                <div style={{ marginTop: "2rem", color: "var(--nuc-text-muted)", fontSize: "0.7rem", fontFamily: "var(--nuc-font-mono)" }}>
                    Secured by AgentAuth · v1.0
                </div>
            </div>
        </div>
    );
}
