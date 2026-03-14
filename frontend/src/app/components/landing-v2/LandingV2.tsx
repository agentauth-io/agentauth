import { useState, useEffect, useRef, useCallback } from "react";

// ── Scroll reveal hook ──
function useReveal(threshold = 0.12) {
    const ref = useRef<HTMLDivElement>(null);
    useEffect(() => {
        const el = ref.current;
        if (!el) return;
        const obs = new IntersectionObserver(
            ([e]) => { if (e.isIntersecting) el.classList.add("visible"); },
            { threshold }
        );
        obs.observe(el);
        return () => obs.disconnect();
    }, [threshold]);
    return ref;
}

// ── Nav ──
function Nav() {
    return (
        <nav className="v2-nav">
            <a href="/v2" className="v2-nav-logo">
                <svg viewBox="0 0 24 28" fill="none">
                    <path d="M12 1L2 5.5v7c0 7.5 4.5 13.5 10 14.5 5.5-1 10-7 10-14.5v-7L12 1Z"
                        stroke="url(#navGrad)" strokeWidth="1.4" />
                    <path d="M8.5 14l2.5 2.5 5-5" stroke="url(#navGrad)" strokeWidth="1.4"
                        strokeLinecap="round" strokeLinejoin="round" />
                    <defs>
                        <linearGradient id="navGrad" x1="2" y1="1" x2="22" y2="27">
                            <stop stopColor="#3b82f6" />
                            <stop offset="1" stopColor="#8b5cf6" />
                        </linearGradient>
                    </defs>
                </svg>
                <b>AgentAuth</b>
                <span className="v2-badge-sm">BETA</span>
            </a>
            <div className="v2-nav-links">
                <a href="/docs">Docs</a>
                <a href="/demo">Demo</a>
                <a href="/">V1 Design</a>
                <a href="#waitlist" className="v2-nav-cta">Join Waitlist</a>
            </div>
        </nav>
    );
}

// ── Hero ──
function Hero() {
    const [copied, setCopied] = useState(false);

    const handleCopy = () => {
        navigator.clipboard.writeText("npm install @agentauth/sdk");
        setCopied(true);
        setTimeout(() => setCopied(false), 2000);
    };

    return (
        <section className="v2-hero">
            <span className="v2-hero-badge">
                <span className="v2-pulse" />
                Now in Private Beta
            </span>

            <h1>
                The <span className="v2-gradient-text">authorization layer</span> for AI agents
            </h1>

            <p>
                One API to prove every AI agent purchase was human-approved.
                Cryptographic delegation tokens. Sub-millisecond verification.
            </p>

            <div className="v2-hero-actions">
                <a className="v2-btn-primary" href="#waitlist">
                    Get Early Access
                </a>
                <a className="v2-btn-outline" href="/docs">
                    Read the Docs
                </a>
            </div>

            <div className="v2-hero-install">
                <div className="v2-install-bar" onClick={handleCopy}>
                    <span className="v2-dim">$</span>
                    <span>npm install @agentauth/sdk</span>
                    <span className="v2-copy-badge">{copied ? "COPIED!" : "COPY"}</span>
                </div>
            </div>

            {/* Auth flow visualization */}
            <div className="v2-flow-visual">
                <FlowCard step="01" label="Consent" value="$500 max" icon={<ShieldIcon />} />
                <div className="v2-flow-connector" />
                <FlowCard step="02" label="Token" value="bsc_eyJ..." icon={<KeyIcon />} />
                <div className="v2-flow-connector" />
                <FlowCard step="03" label="Delegate" value="$347" icon={<ChainIcon />} />
                <div className="v2-flow-connector" />
                <FlowCard step="04" label="Verified" value="0.4ms" icon={<CheckIcon />} />
            </div>
        </section>
    );
}

function FlowCard({ step, label, value, icon }: { step: string; label: string; value: string; icon: React.ReactNode }) {
    return (
        <div className="v2-flow-card">
            <div className="v2-flow-step">{step}</div>
            <div className="v2-flow-icon">{icon}</div>
            <div className="v2-flow-label">{label}</div>
            <div className="v2-flow-value">{value}</div>
        </div>
    );
}

// ── SVG Icons ──
function ShieldIcon() {
    return (
        <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#3b82f6" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
            <path d="M12 2L3 7v5c0 6.5 3.8 11.6 9 13 5.2-1.4 9-6.5 9-13V7l-9-5z" />
        </svg>
    );
}

function KeyIcon() {
    return (
        <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#8b5cf6" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
            <circle cx="8" cy="15" r="4" />
            <path d="M11.3 11.7L15 8l2 2" />
            <path d="M15 8l3-3" />
        </svg>
    );
}

function ChainIcon() {
    return (
        <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#f59e0b" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
            <path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71" />
            <path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71" />
        </svg>
    );
}

function CheckIcon() {
    return (
        <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#10b981" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
            <circle cx="12" cy="12" r="9" />
            <path d="M9 12l2 2 4-4" />
        </svg>
    );
}

// ── Social Proof ──
function SocialProof() {
    const ref = useReveal();
    return (
        <section className="v2-social v2-reveal" ref={ref}>
            <p>Built for teams building with</p>
            <div className="v2-logos">
                <span>LangChain</span>
                <span>CrewAI</span>
                <span>AutoGen</span>
                <span>OpenAI Agents</span>
                <span>Vercel AI SDK</span>
            </div>
        </section>
    );
}

// ── How It Works ──
function HowItWorks() {
    const ref = useReveal();
    const stepsRef = useRef<HTMLDivElement>(null);

    useEffect(() => {
        const el = stepsRef.current;
        if (!el) return;
        const obs = new IntersectionObserver(
            (entries) => {
                entries.forEach((e) => {
                    if (e.isIntersecting) {
                        const idx = Array.from(el.children).indexOf(e.target);
                        (e.target as HTMLElement).style.transitionDelay = `${idx * 0.12}s`;
                        e.target.classList.add("visible");
                    }
                });
            },
            { threshold: 0.15 }
        );
        el.querySelectorAll(".v2-step").forEach((s) => obs.observe(s));
        return () => obs.disconnect();
    }, []);

    const steps = [
        { title: "User Consent", desc: "Human defines what the agent can do. Amount, merchant, time window." },
        { title: "Token Minting", desc: "Biscuit token is minted with embedded cryptographic constraints." },
        { title: "Delegation", desc: "Permissions attenuate at each hop. $500 becomes $347." },
        { title: "Verification", desc: "Merchant verifies offline in <1ms. Receipt is court-admissible." },
    ];

    return (
        <section className="v2-how">
            <div className="v2-section-header v2-reveal" ref={ref}>
                <span className="v2-section-tag">How it works</span>
                <h2>Four steps to <span>cryptographic proof</span></h2>
            </div>
            <div className="v2-steps" ref={stepsRef}>
                {steps.map((s, i) => (
                    <div className="v2-step v2-reveal" key={i}>
                        <div className="v2-step-num">{i + 1}</div>
                        <div className="v2-step-title">{s.title}</div>
                        <div className="v2-step-desc">{s.desc}</div>
                    </div>
                ))}
            </div>
        </section>
    );
}

// ── Bento Features ──
function BentoFeatures() {
    const headerRef = useReveal();
    const gridRef = useRef<HTMLDivElement>(null);

    useEffect(() => {
        const el = gridRef.current;
        if (!el) return;
        const obs = new IntersectionObserver(
            (entries) => {
                entries.forEach((e) => {
                    if (e.isIntersecting) {
                        const idx = Array.from(el.children).indexOf(e.target);
                        (e.target as HTMLElement).style.transitionDelay = `${idx * 0.08}s`;
                        e.target.classList.add("visible");
                    }
                });
            },
            { threshold: 0.1 }
        );
        el.querySelectorAll(".v2-bento-card").forEach((c) => obs.observe(c));
        return () => obs.disconnect();
    }, []);

    return (
        <section className="v2-bento">
            <div className="v2-section-header v2-reveal" ref={headerRef}>
                <span className="v2-section-tag">Features</span>
                <h2>Built for <span>production</span></h2>
            </div>
            <div className="v2-bento-grid" ref={gridRef}>
                <div className="v2-bento-card wide v2-reveal">
                    <div className="v2-bento-glow" style={{ background: "var(--v2-violet)" }} />
                    <div className="v2-bento-num">01</div>
                    <div className="v2-bento-title">Biscuit Tokens</div>
                    <div className="v2-bento-desc">
                        Cryptographic bearer credentials with embedded constraints.
                        Capability attenuation — permissions can only decrease through delegation chains.
                    </div>
                </div>
                <div className="v2-bento-card v2-reveal">
                    <div className="v2-bento-glow" style={{ background: "var(--v2-emerald)" }} />
                    <div className="v2-bento-num">02</div>
                    <div className="v2-bento-stat emerald">&lt;1ms</div>
                    <div className="v2-bento-title">Offline Verification</div>
                    <div className="v2-bento-desc">Zero network round-trips. Edge verification.</div>
                </div>
                <div className="v2-bento-card v2-reveal">
                    <div className="v2-bento-glow" style={{ background: "var(--v2-blue)" }} />
                    <div className="v2-bento-num">03</div>
                    <div className="v2-bento-title">ED25519 Signed</div>
                    <div className="v2-bento-desc">
                        Every token is cryptographically signed. Tamper-proof by design.
                    </div>
                </div>
                <div className="v2-bento-card v2-reveal">
                    <div className="v2-bento-glow" style={{ background: "var(--v2-amber)" }} />
                    <div className="v2-bento-num">04</div>
                    <div className="v2-bento-title">Protocol Agnostic</div>
                    <div className="v2-bento-desc">
                        Visa TAP, Stripe ACP, Google AP2, Mastercard Agent Pay.
                    </div>
                </div>
                <div className="v2-bento-card wide v2-reveal">
                    <div className="v2-bento-glow" style={{ background: "var(--v2-violet)" }} />
                    <div className="v2-bento-num">05</div>
                    <div className="v2-bento-title">Delegation Chains</div>
                    <div className="v2-bento-desc">
                        Agent A delegates to Agent B. Permissions mathematically shrink at each hop.
                        $500 → $500 → $347. A payment agent can never exceed the original limit.
                    </div>
                </div>
                <div className="v2-bento-card v2-reveal">
                    <div className="v2-bento-glow" style={{ background: "var(--v2-emerald)" }} />
                    <div className="v2-bento-num">06</div>
                    <div className="v2-bento-title">Any Framework</div>
                    <div className="v2-bento-desc">
                        LangChain, CrewAI, AutoGen, OpenAI Agents SDK. Drop-in integration.
                    </div>
                </div>
            </div>
        </section>
    );
}

// ── Code Demo ──
function CodeDemo() {
    const ref = useReveal();

    return (
        <section className="v2-code-sec">
            <div className="v2-section-header v2-reveal" ref={ref}>
                <span className="v2-section-tag">Developer Experience</span>
                <h2>Four lines to <span>authorize</span></h2>
            </div>
            <div className="v2-code-split v2-reveal" ref={useReveal(0.08)}>
                <div className="v2-code-editor">
                    <div className="v2-code-bar">
                        <div className="v2-code-dot r" />
                        <div className="v2-code-dot y" />
                        <div className="v2-code-dot g" />
                        <span className="v2-code-bar-title">authorize.py</span>
                    </div>
                    <div className="v2-code-body" dangerouslySetInnerHTML={{ __html: codeHtml }} />
                </div>
                <div className="v2-code-output">
                    <div className="v2-code-bar">
                        <div className="v2-code-dot r" />
                        <div className="v2-code-dot y" />
                        <div className="v2-code-dot g" />
                        <span className="v2-code-bar-title">terminal</span>
                    </div>
                    <div className="v2-code-body" dangerouslySetInnerHTML={{ __html: outputHtml }} />
                </div>
            </div>
        </section>
    );
}

const codeHtml = `<span class="v2-ln"> 1</span><span class="v2-kw">import</span> <span class="v2-var">agentauth</span>
<span class="v2-ln"> 2</span>
<span class="v2-ln"> 3</span><span class="v2-cm"># Create consent with spending limit</span>
<span class="v2-ln"> 4</span><span class="v2-var">consent</span> <span class="v2-op">=</span> <span class="v2-var">agentauth</span><span class="v2-op">.</span><span class="v2-fn">Consent.create</span><span class="v2-op">(</span>
<span class="v2-ln"> 5</span>    <span class="v2-var">user</span><span class="v2-op">=</span><span class="v2-str">"user_a3x"</span><span class="v2-op">,</span>
<span class="v2-ln"> 6</span>    <span class="v2-var">intent</span><span class="v2-op">=</span><span class="v2-str">"Buy flight to NYC"</span><span class="v2-op">,</span>
<span class="v2-ln"> 7</span>    <span class="v2-var">max_amount</span><span class="v2-op">=</span><span class="v2-num">500</span><span class="v2-op">,</span>
<span class="v2-ln"> 8</span>    <span class="v2-var">ttl</span><span class="v2-op">=</span><span class="v2-str">"24h"</span>
<span class="v2-ln"> 9</span><span class="v2-op">)</span>
<span class="v2-ln">10</span>
<span class="v2-ln">11</span><span class="v2-cm"># Authorize agent transaction</span>
<span class="v2-ln">12</span><span class="v2-var">auth</span> <span class="v2-op">=</span> <span class="v2-var">agentauth</span><span class="v2-op">.</span><span class="v2-fn">authorize</span><span class="v2-op">(</span>
<span class="v2-ln">13</span>    <span class="v2-var">token</span><span class="v2-op">=</span><span class="v2-var">consent</span><span class="v2-op">.</span><span class="v2-var">token</span><span class="v2-op">,</span>
<span class="v2-ln">14</span>    <span class="v2-var">action</span><span class="v2-op">=</span><span class="v2-str">"purchase"</span><span class="v2-op">,</span>
<span class="v2-ln">15</span>    <span class="v2-var">amount</span><span class="v2-op">=</span><span class="v2-num">347</span><span class="v2-op">,</span>
<span class="v2-ln">16</span>    <span class="v2-var">merchant</span><span class="v2-op">=</span><span class="v2-str">"merch_united"</span>
<span class="v2-ln">17</span><span class="v2-op">)</span>
<span class="v2-ln">18</span>
<span class="v2-ln">19</span><span class="v2-fn">print</span><span class="v2-op">(</span><span class="v2-var">auth</span><span class="v2-op">.</span><span class="v2-var">decision</span><span class="v2-op">)</span>  <span class="v2-cm"># "ALLOW"</span>
<span class="v2-ln">20</span><span class="v2-fn">print</span><span class="v2-op">(</span><span class="v2-var">auth</span><span class="v2-op">.</span><span class="v2-var">latency</span><span class="v2-op">)</span>   <span class="v2-cm"># "0.4ms"</span>`;

const outputHtml = `
<span class="v2-ok">&#10003;</span> <span class="v2-val">Consent created</span>
  <span class="v2-lbl">consent_id:</span>  <span class="v2-val">cns_8f2a...</span>
  <span class="v2-lbl">token:</span>       <span class="v2-val">bsc_eyJhbGci...</span>
  <span class="v2-lbl">scope:</span>       <span class="v2-str">purchase &#8804; $500</span>
  <span class="v2-lbl">signing:</span>     <span class="v2-val">ed25519</span>
  <span class="v2-lbl">attenuable:</span>  <span class="v2-num">true</span>

<span class="v2-ok">&#10003;</span> <span class="v2-val">Authorization: ALLOW</span>
  <span class="v2-lbl">auth_code:</span>  <span class="v2-val">auth_7k9f...</span>
  <span class="v2-lbl">amount:</span>     <span class="v2-str">$347.00</span> <span class="v2-lbl">(within $500 limit)</span>
  <span class="v2-lbl">latency:</span>    <span class="v2-val">0.4ms</span>

<span class="v2-ok">&#10003;</span> <span class="v2-val">Receipt saved</span>
  <span class="v2-lbl">receipt:</span>       <span class="v2-val">rcp_x8m2...</span>
  <span class="v2-lbl">consent_proof:</span> <span class="v2-val">cpr_4j7n...</span>
  <span class="v2-lbl">defense:</span>       <span class="v2-ok">chargeback-proof</span>`;

// ── Stats ──
function Stats() {
    const ref = useReveal();
    const stats = [
        { num: "<1ms", label: "Verification" },
        { num: "0", label: "Network Calls" },
        { num: "100%", label: "Chargeback Defense" },
        { num: "6", label: "SDK Languages" },
    ];

    return (
        <section className="v2-stats v2-reveal" ref={ref}>
            <div className="v2-stats-grid">
                {stats.map((s) => (
                    <div className="v2-stat" key={s.label}>
                        <div className="v2-stat-num v2-gradient-text">{s.num}</div>
                        <div className="v2-stat-label">{s.label}</div>
                    </div>
                ))}
            </div>
        </section>
    );
}

// ── CTA ──
function CTA() {
    const ref = useReveal();
    const [email, setEmail] = useState("");
    const [status, setStatus] = useState<"idle" | "loading" | "success" | "error">("idle");
    const [message, setMessage] = useState("");

    const handleSubmit = useCallback(async (e: React.FormEvent) => {
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
    }, [email]);

    return (
        <section className="v2-cta" id="waitlist">
            <div className="v2-reveal" ref={ref}>
                <h2>
                    Ship agent commerce <span className="v2-gradient-text">today</span>
                </h2>
                <p>
                    Auth0 sold for $6.5B building authorization for humans.
                    We're building it for AI agents. One API. Cryptographic proof.
                </p>

                {status === "success" ? (
                    <div className="v2-cta-done">{message}</div>
                ) : (
                    <form className="v2-cta-form" onSubmit={handleSubmit}>
                        <input
                            type="email"
                            placeholder="you@company.com"
                            value={email}
                            onChange={(e) => setEmail(e.target.value)}
                            required
                            className="v2-cta-input"
                        />
                        <button type="submit" className="v2-btn-primary" disabled={status === "loading"}>
                            {status === "loading" ? "Joining..." : "Join Waitlist"}
                        </button>
                    </form>
                )}
                {status === "error" && <div className="v2-cta-err">{message}</div>}

                <a className="v2-btn-outline" href="/demo" style={{ marginTop: 16, display: "inline-block" }}>
                    Try the Interactive Demo
                </a>
            </div>
        </section>
    );
}

// ── Main Page ──
export function LandingV2() {
    return (
        <div className="v2">
            {/* Animated background */}
            <div className="v2-bg-mesh">
                <div className="v2-blob v2-blob-1" />
                <div className="v2-blob v2-blob-2" />
                <div className="v2-blob v2-blob-3" />
            </div>
            <div className="v2-grid-pattern" />

            {/* Content */}
            <div className="v2-content">
                <Nav />
                <Hero />
                <SocialProof />
                <HowItWorks />
                <BentoFeatures />
                <CodeDemo />
                <Stats />
                <CTA />
                <footer className="v2-footer">
                    <p>
                        &copy; 2026 AgentAuth &middot;{" "}
                        <a href="https://agentauth.in">agentauth.in</a> &middot;
                        Cryptographic authorization for AI agent commerce
                    </p>
                </footer>
            </div>
        </div>
    );
}
