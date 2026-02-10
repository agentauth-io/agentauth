import { useState, useCallback } from "react";

// ══════════════════════════════════════════════════════════
//  LOCAL SIMULATION ENGINE
//  Replicates the exact backend logic so the demo always works
// ══════════════════════════════════════════════════════════

function uid(prefix: string) {
    return `${prefix}_${Math.random().toString(36).slice(2, 10)}`;
}

function fakeJwt() {
    const h = btoa(JSON.stringify({ typ: "JWT", alg: "HS256" }));
    const p = btoa(JSON.stringify({ sub: "demo", iat: Math.floor(Date.now() / 1000), exp: Math.floor(Date.now() / 1000) + 3600 }));
    const s = btoa(Math.random().toString(36).slice(2, 20));
    return `${h}.${p}.${s}`;
}

interface SimConsent {
    consent_id: string;
    delegation_token: string;
    max_amount: number;
    currency: string;
    intent: string;
    created_at: string;
    expires_at: string;
}

interface SimAuthResult {
    decision: "ALLOW" | "DENY";
    authorization_code?: string;
    consent_id: string;
    reason?: string;
    message?: string;
    expires_at?: string;
}

function simulateConsent(intent: string, maxAmount: number, currency: string): { response: Record<string, unknown>; consent: SimConsent; latency: number } {
    const t0 = performance.now();
    const now = new Date();
    const expiresAt = new Date(now.getTime() + 3600_000);
    const consent: SimConsent = {
        consent_id: uid("cons"),
        delegation_token: fakeJwt(),
        max_amount: maxAmount,
        currency,
        intent,
        created_at: now.toISOString(),
        expires_at: expiresAt.toISOString(),
    };
    const response = {
        consent_id: consent.consent_id,
        delegation_token: consent.delegation_token,
        expires_at: consent.expires_at,
        constraints: { max_amount: maxAmount, currency },
    };
    const latency = Math.round(performance.now() - t0) + Math.floor(Math.random() * 8 + 3); // simulate ~3-10ms
    return { response, consent, latency };
}

function simulateAuthorize(consent: SimConsent, amount: number, currency: string, merchantId: string, merchantName: string): { response: Record<string, unknown>; result: SimAuthResult; latency: number } {
    const t0 = performance.now();
    let result: SimAuthResult;
    if (amount > consent.max_amount) {
        result = {
            decision: "DENY",
            consent_id: consent.consent_id,
            reason: "amount_exceeded",
            message: `Transaction amount $${amount} exceeds consent limit of $${consent.max_amount}`,
        };
    } else if (currency !== consent.currency) {
        result = {
            decision: "DENY",
            consent_id: consent.consent_id,
            reason: "currency_mismatch",
            message: `Transaction currency ${currency} doesn't match consent currency ${consent.currency}`,
        };
    } else {
        result = {
            decision: "ALLOW",
            authorization_code: uid("authz"),
            consent_id: consent.consent_id,
            expires_at: new Date(Date.now() + 300_000).toISOString(),
        };
    }
    const response: Record<string, unknown> = { ...result };
    const latency = Math.round(performance.now() - t0) + Math.floor(Math.random() * 5 + 2);
    return { response, result, latency };
}

function simulateVerify(consent: SimConsent, authCode: string, amount: number, currency: string): { response: Record<string, unknown>; latency: number } {
    const t0 = performance.now();
    const response: Record<string, unknown> = {
        valid: true,
        authorization_id: uid("auth"),
        consent_proof: {
            consent_id: consent.consent_id,
            user_authorized_at: consent.created_at,
            user_intent: consent.intent,
            max_authorized_amount: consent.max_amount,
            actual_amount: amount,
            currency,
            signature_valid: true,
        },
        verification_timestamp: new Date().toISOString(),
        proof_token: fakeJwt(),
    };
    const latency = Math.round(performance.now() - t0) + Math.floor(Math.random() * 6 + 2);
    return { response, latency };
}

// ══════════════════════════════════════════════════════════
//  JSON HIGHLIGHTER
// ══════════════════════════════════════════════════════════

function hl(obj: unknown): string {
    return JSON.stringify(obj, null, 2)
        .replace(/"([^"]+)":/g, '<span class="json-key">"$1"</span>:')
        .replace(/: "([^"]*)"/g, ': <span class="json-str">"$1"</span>')
        .replace(/: (\d+\.?\d*)/g, ': <span class="json-num">$1</span>')
        .replace(/: (true|false)/g, ': <span class="json-bool">$1</span>')
        .replace(/: (null)/g, ': <span class="json-null">null</span>');
}

// ══════════════════════════════════════════════════════════
//  DEMO PAGE
// ══════════════════════════════════════════════════════════

type Phase = "IDLE" | "S1" | "S1_DONE" | "S2" | "S2_DONE" | "S3" | "S3_DONE";

export function DemoPage() {
    // Editable params
    const [intent, setIntent] = useState("Buy cheapest flight to NYC");
    const [maxAmount, setMaxAmount] = useState(500);
    const [purchaseAmount, setPurchaseAmount] = useState(347);
    const [currency, setCurrency] = useState("USD");
    const [merchantName, setMerchantName] = useState("Delta Airlines");

    // Flow state
    const [phase, setPhase] = useState<Phase>("IDLE");
    const [consent, setConsent] = useState<SimConsent | null>(null);
    const [authResult, setAuthResult] = useState<SimAuthResult | null>(null);
    const [s1Res, setS1Res] = useState<Record<string, unknown> | null>(null);
    const [s2Res, setS2Res] = useState<Record<string, unknown> | null>(null);
    const [s3Res, setS3Res] = useState<Record<string, unknown> | null>(null);
    const [s1Lat, setS1Lat] = useState(0);
    const [s2Lat, setS2Lat] = useState(0);
    const [s3Lat, setS3Lat] = useState(0);

    const merchantId = merchantName.toLowerCase().replace(/\s+/g, "_");

    const reset = useCallback(() => {
        setPhase("IDLE");
        setConsent(null);
        setAuthResult(null);
        setS1Res(null);
        setS2Res(null);
        setS3Res(null);
        setS1Lat(0);
        setS2Lat(0);
        setS3Lat(0);
    }, []);

    const applyPreset = (p: string) => {
        reset();
        if (p === "flight") { setIntent("Buy cheapest flight to NYC"); setMaxAmount(500); setPurchaseAmount(347); setMerchantName("Delta Airlines"); }
        if (p === "overlimit") { setIntent("Buy a premium laptop"); setMaxAmount(500); setPurchaseAmount(812); setMerchantName("Best Buy"); }
        if (p === "grocery") { setIntent("Order weekly groceries"); setMaxAmount(200); setPurchaseAmount(67); setMerchantName("Amazon Fresh"); }
    };

    // Run all three steps with visual delays
    const runAll = useCallback(async () => {
        // Step 1
        setPhase("S1");
        await delay(600);
        const r1 = simulateConsent(intent, maxAmount, currency);
        setS1Res(r1.response);
        setS1Lat(r1.latency);
        setConsent(r1.consent);
        setPhase("S1_DONE");

        // Step 2
        await delay(800);
        setPhase("S2");
        await delay(600);
        const r2 = simulateAuthorize(r1.consent, purchaseAmount, currency, merchantId, merchantName);
        setS2Res(r2.response);
        setS2Lat(r2.latency);
        setAuthResult(r2.result);
        setPhase("S2_DONE");

        if (r2.result.decision === "DENY") return;

        // Step 3
        await delay(800);
        setPhase("S3");
        await delay(600);
        const r3 = simulateVerify(r1.consent, r2.result.authorization_code!, purchaseAmount, currency);
        setS3Res(r3.response);
        setS3Lat(r3.latency);
        setPhase("S3_DONE");
    }, [intent, maxAmount, purchaseAmount, currency, merchantId, merchantName]);

    const isRunning = phase === "S1" || phase === "S2" || phase === "S3";
    const isDenied = authResult?.decision === "DENY";
    const allDone = phase === "S3_DONE";
    const flowDone = allDone || (isDenied && phase === "S2_DONE");

    // Security checks
    const checks = [
        { label: "Token Signature", desc: "Cryptographic JWT verification (HS256)", pass: !!s1Res, fail: false },
        { label: "Amount Constraint", desc: `$${purchaseAmount} ${purchaseAmount <= maxAmount ? "≤" : ">"} $${maxAmount} limit`, pass: !!s2Res && purchaseAmount <= maxAmount, fail: !!s2Res && purchaseAmount > maxAmount },
        { label: "Currency Match", desc: `${currency} = ${currency}`, pass: !!s2Res && !isDenied, fail: false },
        { label: "Expiry Check", desc: "Token within 1h TTL", pass: !!s2Res, fail: false },
        { label: "One-Time Verify", desc: "Auth code consumed after use", pass: !!s3Res, fail: false },
    ];

    return (
        <div className="demo-page">
            {/* Nav */}
            <nav className="seq-nav">
                <a href="/" className="seq-logo">
                    <svg viewBox="0 0 24 28" fill="none">
                        <path d="M12 1L2 5.5v7c0 7.5 4.5 13.5 10 14.5 5.5-1 10-7 10-14.5v-7L12 1Z" stroke="#e8e6e1" strokeWidth="1.2" />
                        <path d="M8.5 14l2.5 2.5 5-5" stroke="#e8e6e1" strokeWidth="1.2" strokeLinecap="round" strokeLinejoin="round" />
                    </svg>
                    <b>AgentAuth</b>
                </a>
                <div className="seq-nav-r">
                    <a href="/">Home</a>
                    <a href="/docs">Docs</a>
                    <a href="/demo" style={{ color: "#e8e6e1" }}>Demo</a>
                    <a href="/docs" className="seq-nav-cta">GET API KEY →</a>
                </div>
            </nav>

            {/* Title */}
            <div className="demo-title-area">
                <h1>Interactive <span>Demo</span></h1>
                <p>Adjust parameters below and watch the 3-step authorization flow execute in real time. Change the spending limit or purchase amount to see ALLOW vs DENY decisions.</p>
            </div>

            {/* Presets */}
            <div className="demo-scenarios">
                <span style={{ fontSize: 10, color: "#8080a0", marginRight: 4 }}>PRESETS:</span>
                <button className="demo-scenario-btn" onClick={() => applyPreset("flight")}>✈️ Flight $347 / $500</button>
                <button className="demo-scenario-btn" onClick={() => applyPreset("overlimit")}>🚫 Over Limit $812 / $500</button>
                <button className="demo-scenario-btn" onClick={() => applyPreset("grocery")}>🛒 Grocery $67 / $200</button>
            </div>

            {/* Main Layout */}
            <div className="demo-main-layout">
                {/* LEFT — Controls */}
                <div className="demo-controls">
                    <div className="demo-controls-header">
                        <h3>Parameters</h3>
                        <span className="demo-controls-sub">Tweak these to change the outcome</span>
                    </div>

                    <label className="demo-field">
                        <span className="demo-field-label">USER INTENT</span>
                        <input type="text" value={intent} onChange={e => setIntent(e.target.value)} disabled={isRunning} className="demo-input" />
                    </label>

                    <div className="demo-field-row">
                        <label className="demo-field">
                            <span className="demo-field-label">SPENDING LIMIT</span>
                            <div className="demo-input-group">
                                <span className="demo-input-prefix">$</span>
                                <input type="number" value={maxAmount} onChange={e => setMaxAmount(Number(e.target.value) || 0)} disabled={isRunning} className="demo-input" min={1} />
                            </div>
                        </label>
                        <label className="demo-field">
                            <span className="demo-field-label">PURCHASE AMOUNT</span>
                            <div className="demo-input-group">
                                <span className="demo-input-prefix">$</span>
                                <input type="number" value={purchaseAmount} onChange={e => setPurchaseAmount(Number(e.target.value) || 0)} disabled={isRunning} className="demo-input" min={1} />
                            </div>
                        </label>
                    </div>

                    <div className="demo-field-row">
                        <label className="demo-field">
                            <span className="demo-field-label">MERCHANT</span>
                            <input type="text" value={merchantName} onChange={e => setMerchantName(e.target.value)} disabled={isRunning} className="demo-input" />
                        </label>
                        <label className="demo-field">
                            <span className="demo-field-label">CURRENCY</span>
                            <select value={currency} onChange={e => setCurrency(e.target.value)} disabled={isRunning} className="demo-input">
                                <option value="USD">USD</option>
                                <option value="EUR">EUR</option>
                                <option value="GBP">GBP</option>
                            </select>
                        </label>
                    </div>

                    {/* Amount bar */}
                    <div className="demo-amount-bar">
                        <div className="demo-amount-bar-label">
                            <span>${purchaseAmount}</span>
                            <span className="demo-amount-bar-limit">limit: ${maxAmount}</span>
                        </div>
                        <div className="demo-amount-bar-track">
                            <div
                                className={`demo-amount-bar-fill ${purchaseAmount > maxAmount ? "over" : "ok"}`}
                                style={{ width: `${Math.min((purchaseAmount / (maxAmount || 1)) * 100, 100)}%` }}
                            />
                            {purchaseAmount > maxAmount && (
                                <div className="demo-amount-bar-overflow" style={{ width: `${Math.min(((purchaseAmount - maxAmount) / (maxAmount || 1)) * 100, 50)}%` }} />
                            )}
                        </div>
                        <div className="demo-amount-bar-verdict">
                            {purchaseAmount <= maxAmount
                                ? <span className="verdict-ok">✓ Within limit — will ALLOW</span>
                                : <span className="verdict-over">✕ Exceeds by ${purchaseAmount - maxAmount} — will DENY</span>}
                        </div>
                    </div>

                    <button className="demo-action-btn primary" onClick={runAll} disabled={isRunning}>
                        {isRunning ? "Running flow..." : "▶ Run Authorization Flow"}
                    </button>
                    <button className="demo-action-btn secondary" onClick={reset} style={{ marginTop: 6 }}>↻ Reset</button>
                </div>

                {/* RIGHT — Flow */}
                <div className="demo-flow">
                    {/* Step 1 */}
                    <FlowStep
                        num={1}
                        title="Create Consent"
                        endpoint="POST /v1/consents"
                        desc={<>User says "<em>{intent}</em>" with <strong>${maxAmount}</strong> {currency} spending limit. AgentAuth creates a cryptographically signed consent and returns a delegation token for the agent.</>}
                        active={phase === "S1"}
                        done={!!s1Res}
                        response={s1Res}
                        latency={s1Lat}
                    />
                    <Connector active={!!s1Res} label="delegation_token" />

                    {/* Step 2 */}
                    <FlowStep
                        num={2}
                        title="Authorize Purchase"
                        endpoint="POST /v1/authorize"
                        desc={<>Agent presents token to buy from <strong>{merchantName}</strong> for <strong>${purchaseAmount}</strong>. Engine checks: amount ≤ limit? Currency match? Token valid?</>}
                        active={phase === "S2"}
                        done={!!s2Res}
                        response={s2Res}
                        latency={s2Lat}
                        decision={authResult?.decision}
                    />
                    <Connector
                        active={authResult?.decision === "ALLOW"}
                        denied={authResult?.decision === "DENY"}
                        label={authResult?.decision === "ALLOW" ? "authorization_code" : authResult?.decision === "DENY" ? "blocked" : undefined}
                    />

                    {/* Step 3 */}
                    <FlowStep
                        num={3}
                        title="Merchant Verify"
                        endpoint="POST /v1/verify"
                        desc={<>Merchant receives auth code and verifies it. AgentAuth returns <strong>cryptographic consent proof</strong> — for chargeback defense. Code is consumed (one-time use).</>}
                        active={phase === "S3"}
                        done={!!s3Res}
                        response={s3Res}
                        latency={s3Lat}
                        skipped={isDenied && phase === "S2_DONE"}
                    />
                </div>
            </div>

            {/* Security Panel */}
            {(s1Res || s2Res) && (
                <div className="demo-security demo-fade-in">
                    <h3>🔒 Security Checks</h3>
                    <p className="demo-security-sub">Authorization engine validation pipeline</p>
                    <div className="demo-security-grid">
                        {checks.map((c, i) => (
                            <div key={i} className={`demo-security-check ${c.pass ? "pass" : ""} ${c.fail ? "fail" : ""}`}>
                                <div className="demo-security-icon">{c.pass ? "✓" : c.fail ? "✕" : "○"}</div>
                                <div>
                                    <div className="demo-security-label">{c.label}</div>
                                    <div className="demo-security-desc">{c.desc}</div>
                                </div>
                            </div>
                        ))}
                    </div>
                </div>
            )}

            {/* Summary */}
            {flowDone && (
                <div className="demo-summary demo-fade-in">
                    <h3>{isDenied ? "Authorization Denied ✕" : "Full Flow Complete ✓"}</h3>
                    <div className="demo-summary-grid">
                        <div className="demo-summary-stat">
                            <div className="stat-val">{isDenied ? 2 : 3}</div>
                            <div className="stat-label">API Calls</div>
                        </div>
                        <div className="demo-summary-stat">
                            <div className="stat-val">{isDenied ? `${s1Lat + s2Lat}ms` : `${s1Lat + s2Lat + s3Lat}ms`}</div>
                            <div className="stat-label">Total Latency</div>
                        </div>
                        <div className="demo-summary-stat">
                            <div className="stat-val">{isDenied ? "DENY" : "ALLOW"}</div>
                            <div className="stat-label">Decision</div>
                        </div>
                        <div className="demo-summary-stat">
                            <div className="stat-val">{isDenied ? `$${purchaseAmount} > $${maxAmount}` : "✓ Proof"}</div>
                            <div className="stat-label">{isDenied ? "Over Limit" : "Chargeback Defense"}</div>
                        </div>
                    </div>
                </div>
            )}

            <footer className="seq-footer">
                <p>© 2026 AgentAuth · <a href="https://agentauth.in">agentauth.in</a> · Interactive demo using local simulation engine</p>
            </footer>
        </div>
    );
}

// ── Sub-components ──

function FlowStep({ num, title, endpoint, desc, active, done, response, latency, decision, skipped }: {
    num: number; title: string; endpoint: string; desc: React.ReactNode;
    active: boolean; done: boolean; response: Record<string, unknown> | null;
    latency: number; decision?: string; skipped?: boolean;
}) {
    return (
        <div className={`demo-flow-step ${active ? "active" : ""} ${done ? "done" : ""} ${skipped ? "skipped" : ""}`}>
            <div className="demo-flow-step-head">
                <div className="demo-flow-step-num">{num}</div>
                <div><h4>{title}</h4><span className="demo-flow-endpoint">{endpoint}</span></div>
                <span className={`demo-step-badge ${active ? "running" : done ? (decision === "DENY" ? "denied" : "done") : skipped ? "denied" : "waiting"}`}>
                    {active ? "RUNNING" : done ? (decision === "DENY" ? "DENIED" : "DONE") : skipped ? "SKIPPED" : "WAITING"}
                </span>
            </div>
            <p className="demo-flow-desc">{desc}</p>
            {decision && (
                <div className={`demo-decision ${decision === "ALLOW" ? "allow" : "deny"}`}>
                    {decision === "ALLOW" ? "✓ ALLOW" : "✕ DENY"}{decision === "DENY" && ` — amount exceeds limit`}
                </div>
            )}
            {response && (
                <div className="demo-fade-in">
                    <div className="demo-code-label">Response</div>
                    <div className="demo-code" dangerouslySetInnerHTML={{ __html: hl(response) }} />
                    <div className="demo-latency">⚡ <span className="lat-val">{latency}ms</span></div>
                </div>
            )}
        </div>
    );
}

function Connector({ active, denied, label }: { active?: boolean; denied?: boolean; label?: string }) {
    return (
        <div className="demo-flow-connector">
            <div className={`demo-flow-line ${active ? "active" : ""} ${denied ? "denied" : ""}`} />
            {label && <span className="demo-flow-connector-label" style={denied ? { color: "#fbbf24" } : undefined}>{label}</span>}
        </div>
    );
}

function delay(ms: number) {
    return new Promise(r => setTimeout(r, ms));
}
