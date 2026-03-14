import { useState, useEffect, useRef, useCallback } from "react";

interface ScriptStep {
    t: "c" | "o" | "d";
    v?: string;
    ms?: number;
}

const script: ScriptStep[] = [
    { t: "c", v: "agentauth init --merchant merch_9x7" },
    { t: "d", ms: 350 },
    {
        t: "o",
        v: '<span class="c-g">✓</span> <span class="c-w">AgentAuth initialized</span>\n  <span class="c-d">merchant_id:</span> <span class="c-s">merch_9x7</span>\n  <span class="c-d">api_key:</span>     <span class="c-s">sk_live_a3x...7k9</span>\n  <span class="c-d">endpoint:</span>   <span class="c-s">https://api.agentauth.in/v1</span>\n',
    },
    { t: "d", ms: 600 },
    {
        t: "c",
        v: 'agentauth consent create --user user_a3x \\\n  --intent "Buy flight NYC" --max-amount 500 --ttl 24h',
    },
    { t: "d", ms: 500 },
    {
        t: "o",
        v: '<span class="c-g">✓</span> <span class="c-w">Consent created</span>\n  <span class="c-d">consent_id:</span>  <span class="c-s">cns_8f2a...</span>\n  <span class="c-d">token:</span>       <span class="c-s">bsc_eyJhbGci...</span>\n  <span class="c-d">scope:</span>       <span class="c-a">purchase ≤ $500</span>\n  <span class="c-d">signing:</span>     <span class="c-s">ed25519</span>\n  <span class="c-d">attenuable:</span>  <span class="c-bl">true</span>\n',
    },
    { t: "d", ms: 800 },
    {
        t: "c",
        v: "agentauth authorize --token bsc_eyJ... \\\n  --action purchase --amount 347 --merchant merch_united",
    },
    { t: "d", ms: 300 },
    {
        t: "o",
        v: '<span class="c-g">✓</span> <span class="c-w">ALLOW</span>\n  <span class="c-d">auth_code:</span> <span class="c-s">auth_7k9f...</span>\n  <span class="c-d">amount:</span>    <span class="c-a">$347.00</span> <span class="c-d">(within $500 limit)</span>\n  <span class="c-d">latency:</span>   <span class="c-s">0.4ms</span>\n',
    },
    { t: "d", ms: 700 },
    { t: "c", v: "agentauth verify --code auth_7k9f... --amount 347" },
    { t: "d", ms: 200 },
    {
        t: "o",
        v: '<span class="c-g">✓</span> <span class="c-w">VALID</span>\n  <span class="c-d">receipt:</span>       <span class="c-s">rcp_x8m2...</span>\n  <span class="c-d">consent_proof:</span> <span class="c-s">cpr_4j7n...</span>\n  <span class="c-d">latency:</span>      <span class="c-s">0.2ms</span>\n\n  <span class="c-g">Receipt saved for chargeback defense.</span>\n',
    },
    { t: "d", ms: 600 },
    { t: "c", v: "agentauth dashboard --live" },
    { t: "d", ms: 400 },
    { t: "o", v: "DASH" },
];

const dashboardHtml = `<div style="font-family:'Space Mono',monospace;font-size:11px;line-height:1;color:#b0b0c0;white-space:normal">
<div style="display:flex;justify-content:space-between;align-items:center;padding:10px 16px;border:1px solid rgba(255,255,255,.06);border-radius:6px;margin-bottom:14px;background:rgba(255,255,255,.02)">
  <span style="color:#e8e6e1;font-weight:700;font-size:12px">AgentAuth Dashboard</span>
  <span><span style="color:#8080a0">merch_9x7</span>&nbsp;&nbsp;<span style="color:#e8e6e1">●</span> <span style="color:#b0b0c0">Live</span></span>
</div>

<div style="display:grid;grid-template-columns:repeat(4,1fr);gap:1px;background:rgba(255,255,255,.04);border-radius:6px;overflow:hidden;margin-bottom:14px">
  <div style="background:rgba(10,10,14,.95);padding:12px 14px"><div style="color:#8080a0;font-size:9px;letter-spacing:1px;margin-bottom:6px">DATE</div><div style="color:#e8e6e1;font-size:13px;font-weight:700">Feb 10</div></div>
  <div style="background:rgba(10,10,14,.95);padding:12px 14px"><div style="color:#8080a0;font-size:9px;letter-spacing:1px;margin-bottom:6px">AUTHORIZATIONS</div><div style="color:#e8e6e1;font-size:13px;font-weight:700">1,247</div></div>
  <div style="background:rgba(10,10,14,.95);padding:12px 14px"><div style="color:#8080a0;font-size:9px;letter-spacing:1px;margin-bottom:6px">APPROVED</div><div style="color:#e8e6e1;font-size:13px;font-weight:700">98.4%</div></div>
  <div style="background:rgba(10,10,14,.95);padding:12px 14px"><div style="color:#8080a0;font-size:9px;letter-spacing:1px;margin-bottom:6px">AVG LATENCY</div><div style="color:#e8e6e1;font-size:13px;font-weight:700">0.3ms</div></div>
</div>

<div style="padding:12px 14px;border:1px solid rgba(255,255,255,.04);border-radius:6px;margin-bottom:14px;background:rgba(255,255,255,.015)">
  <div style="color:#8080a0;font-size:9px;letter-spacing:1px;margin-bottom:8px">VOLUME (24H)</div>
  <div style="display:flex;align-items:center;gap:10px">
    <div style="flex:1;height:6px;background:rgba(255,255,255,.04);border-radius:3px;overflow:hidden">
      <div style="width:88%;height:100%;background:linear-gradient(90deg,#888,#e8e6e1);border-radius:3px"></div>
    </div>
    <span style="color:#e8e6e1;font-weight:700;font-size:12px;white-space:nowrap">$48,290</span>
  </div>
</div>

<div style="border:1px solid rgba(255,255,255,.04);border-radius:6px;overflow:hidden;margin-bottom:14px">
  <div style="padding:10px 14px;border-bottom:1px solid rgba(255,255,255,.04);background:rgba(255,255,255,.015)">
    <span style="color:#8080a0;font-size:9px;letter-spacing:1px">RECENT AUTHORIZATIONS</span>
  </div>
  <div style="display:grid;grid-template-columns:72px 50px 48px 1fr;gap:0;font-size:10px">
    <div style="padding:8px 14px;border-bottom:1px solid rgba(255,255,255,.03);color:#8080a0">17:08:43</div><div style="padding:8px 4px;border-bottom:1px solid rgba(255,255,255,.03);color:#e8e6e1;font-weight:700">ALLOW</div><div style="padding:8px 4px;border-bottom:1px solid rgba(255,255,255,.03);color:#c0c0c8;text-align:right">$347</div><div style="padding:8px 14px;border-bottom:1px solid rgba(255,255,255,.03);color:#8080a0">user_a3x → merch_united</div>
    <div style="padding:8px 14px;border-bottom:1px solid rgba(255,255,255,.03);color:#8080a0">17:08:21</div><div style="padding:8px 4px;border-bottom:1px solid rgba(255,255,255,.03);color:#e8e6e1;font-weight:700">ALLOW</div><div style="padding:8px 4px;border-bottom:1px solid rgba(255,255,255,.03);color:#c0c0c8;text-align:right">$29</div><div style="padding:8px 14px;border-bottom:1px solid rgba(255,255,255,.03);color:#8080a0">user_b7m → merch_amazon</div>
    <div style="padding:8px 14px;border-bottom:1px solid rgba(255,255,255,.03);color:#8080a0">17:07:58</div><div style="padding:8px 4px;border-bottom:1px solid rgba(255,255,255,.03);color:#666;font-weight:700">DENY</div><div style="padding:8px 4px;border-bottom:1px solid rgba(255,255,255,.03);color:#c0c0c8;text-align:right">$812</div><div style="padding:8px 14px;border-bottom:1px solid rgba(255,255,255,.03);color:#8080a0">user_c1p → over limit</div>
    <div style="padding:8px 14px;border-bottom:1px solid rgba(255,255,255,.03);color:#8080a0">17:07:44</div><div style="padding:8px 4px;border-bottom:1px solid rgba(255,255,255,.03);color:#e8e6e1;font-weight:700">ALLOW</div><div style="padding:8px 4px;border-bottom:1px solid rgba(255,255,255,.03);color:#c0c0c8;text-align:right">$67</div><div style="padding:8px 14px;border-bottom:1px solid rgba(255,255,255,.03);color:#8080a0">user_d9q → merch_shopify</div>
    <div style="padding:8px 14px;color:#8080a0">17:07:12</div><div style="padding:8px 4px;color:#e8e6e1;font-weight:700">ALLOW</div><div style="padding:8px 4px;color:#c0c0c8;text-align:right">$124</div><div style="padding:8px 14px;color:#8080a0">user_e4w → merch_stripe</div>
  </div>
</div>

<div style="display:grid;grid-template-columns:1fr 1fr;gap:1px;background:rgba(255,255,255,.04);border-radius:6px;overflow:hidden">
  <div style="background:rgba(10,10,14,.95);padding:12px 14px"><div style="color:#8080a0;font-size:9px;letter-spacing:1px;margin-bottom:6px">CHARGEBACKS DEFENDED</div><div style="color:#e8e6e1;font-size:13px;font-weight:700">23/23 <span style="color:#8080a0;font-weight:400;font-size:10px">(100%)</span></div></div>
  <div style="background:rgba(10,10,14,.95);padding:12px 14px"><div style="color:#8080a0;font-size:9px;letter-spacing:1px;margin-bottom:6px">MONEY SAVED</div><div style="color:#e8e6e1;font-size:13px;font-weight:700">$12,847</div></div>
</div>
</div>`;

export function TerminalDemo() {
    const bodyRef = useRef<HTMLDivElement>(null);
    const termRef = useRef<HTMLDivElement>(null);
    const [activeTab, setActiveTab] = useState<"cli" | "dash">("cli");
    const runningRef = useRef(false);
    const startedRef = useRef(false);

    const typeCommand = useCallback(
        (txt: string, cb: () => void) => {
            const body = bodyRef.current;
            if (!body) return;
            body.innerHTML += '<span class="c-p">❯</span> ';
            let ci = 0;
            const full = txt.split("\n").join("\n  ");

            function tc() {
                if (!body) return;
                if (ci >= full.length) {
                    body.innerHTML += "\n";
                    body.scrollTop = 9e9;
                    setTimeout(cb, 120);
                    return;
                }
                const ch = full[ci];
                body.innerHTML += `<span class="c-c">${ch === "<" ? "&lt;" : ch === ">" ? "&gt;" : ch}</span>`;
                ci++;
                body.scrollTop = 9e9;
                setTimeout(tc, 10 + Math.random() * 18);
            }
            tc();
        },
        []
    );

    const runScript = useCallback(() => {
        if (runningRef.current) return;
        runningRef.current = true;
        const body = bodyRef.current;
        if (!body) return;
        body.innerHTML = "";
        let i = 0;

        function nx() {
            if (i >= script.length) {
                runningRef.current = false;
                return;
            }
            const s = script[i];
            i++;
            if (s.t === "c" && s.v) {
                typeCommand(s.v, nx);
            } else if (s.t === "o") {
                if (!body) return;
                if (s.v === "DASH") {
                    body.innerHTML += dashboardHtml;
                } else if (s.v) {
                    body.innerHTML += s.v;
                }
                body.scrollTop = 9e9;
                nx();
            } else if (s.t === "d") {
                setTimeout(nx, s.ms ?? 300);
            }
        }
        nx();
    }, [typeCommand]);

    // Intersection observer for auto-start
    useEffect(() => {
        const termEl = termRef.current;
        if (!termEl) return;

        const obs = new IntersectionObserver(
            (es) => {
                if (es[0].isIntersecting && !startedRef.current) {
                    startedRef.current = true;
                    termEl.classList.add("in-view");
                    runScript();
                }
            },
            { threshold: 0.15 }
        );
        obs.observe(termEl);
        return () => obs.disconnect();
    }, [runScript]);

    const handleTabClick = (tab: "cli" | "dash") => {
        setActiveTab(tab);
        if (tab === "dash") {
            if (bodyRef.current) bodyRef.current.innerHTML = dashboardHtml;
        } else {
            runningRef.current = false;
            runScript();
        }
    };

    return (
        <section className="seq-term-sec" id="demo">
            <div className="seq-term-header seq-section-reveal" ref={(el) => {
                if (el) {
                    const obs = new IntersectionObserver((entries) => {
                        if (entries[0].isIntersecting) el.classList.add("in-view");
                    }, { threshold: 0.1 });
                    obs.observe(el);
                }
            }}>
                <div className="seq-panel-tag" style={{ marginBottom: 14, textAlign: "center" }}>
                    Live Demo
                </div>
                <h2>
                    Watch the API <span>in action</span>
                </h2>
            </div>

            <div className="seq-lt" ref={termRef}>
                <div className="seq-lt-bar">
                    <div className="seq-lt-d r" />
                    <div className="seq-lt-d y" />
                    <div className="seq-lt-d g" />
                    <div className="seq-lt-tabs">
                        <button
                            className={`seq-lt-tab ${activeTab === "cli" ? "active" : ""}`}
                            onClick={() => handleTabClick("cli")}
                        >
                            CLI
                        </button>
                        <button
                            className={`seq-lt-tab ${activeTab === "dash" ? "active" : ""}`}
                            onClick={() => handleTabClick("dash")}
                        >
                            Dashboard
                        </button>
                    </div>
                </div>
                <div className="seq-lt-body" ref={bodyRef} />
            </div>
        </section>
    );
}
