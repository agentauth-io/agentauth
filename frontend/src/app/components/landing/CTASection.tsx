import { useState } from "react";

export function CTASection() {
    const [email, setEmail] = useState("");
    const [status, setStatus] = useState<"idle" | "loading" | "success" | "error">("idle");
    const [message, setMessage] = useState("");

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!email.includes("@")) return;
        setStatus("loading");

        try {
            const res = await fetch("/.netlify/functions/waitlist", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ email }),
            });
            const data = await res.json();
            if (data.success) {
                setStatus("success");
                setMessage(data.message || "You're on the list!");
                setEmail("");
            } else {
                setStatus("error");
                setMessage(data.error || "Something went wrong.");
            }
        } catch {
            setStatus("error");
            setMessage("Network error. Please try again.");
        }
    };

    return (
        <section className="seq-cta-sec" id="waitlist">
            <h2>
                The auth layer <span>for agents</span>
            </h2>
            <p>
                Auth0 was $6.5B for human auth. AgentAuth does it for AI agents. One
                API. Cryptographic proof.
            </p>

            {status === "success" ? (
                <div className="seq-waitlist-done">
                    <span>✅</span> {message}
                </div>
            ) : (
                <form className="seq-waitlist-form" onSubmit={handleSubmit}>
                    <input
                        type="email"
                        placeholder="you@company.com"
                        value={email}
                        onChange={(e) => setEmail(e.target.value)}
                        required
                        className="seq-waitlist-input"
                    />
                    <button
                        type="submit"
                        className="seq-btn seq-btn-g"
                        disabled={status === "loading"}
                    >
                        {status === "loading" ? "Joining..." : "Join Waitlist"}
                    </button>
                </form>
            )}
            {status === "error" && (
                <div className="seq-waitlist-err">{message}</div>
            )}
            <a className="seq-btn seq-btn-o" href="/demo" style={{ marginTop: 12 }}>
                Try the Interactive Demo →
            </a>
        </section>
    );
}
