import { useEffect, useRef, useState } from "react";

const TOTAL_FRAMES = 300;
const CANVAS_W = 1000;
const CANVAS_H = 1000;
const TAU = Math.PI * 2;

// ── Shield path points (normalized) ──
function shieldPts(s: number): [number, number][] {
    return [
        [0, -s], [s * 0.55, -s * 0.85], [s * 0.88, -s * 0.35], [s * 0.8, s * 0.2],
        [s * 0.5, s * 0.7], [0, s * 1.05], [-s * 0.5, s * 0.7], [-s * 0.8, s * 0.2],
        [-s * 0.88, -s * 0.35], [-s * 0.55, -s * 0.85],
    ];
}

function drawShield(
    ctx: CanvasRenderingContext2D, cx: number, cy: number, s: number,
    progress: number, strokeColor: string, fillColor: string | null
) {
    const pts = shieldPts(s);
    const totalPts = pts.length;
    const drawn = progress * totalPts;
    ctx.beginPath();
    for (let i = 0; i < totalPts; i++) {
        const frac = Math.min(1, Math.max(0, drawn - i));
        if (frac <= 0) break;
        const p0 = pts[i], p1 = pts[(i + 1) % totalPts];
        if (i === 0) {
            ctx.moveTo(cx + p0[0], cy + p0[1]);
        }
        const nx = cx + p0[0] + (p1[0] - p0[0]) * frac;
        const ny = cy + p0[1] + (p1[1] - p0[1]) * frac;
        ctx.lineTo(nx, ny);
    }
    if (progress >= 1) ctx.closePath();
    if (fillColor) { ctx.fillStyle = fillColor; ctx.fill(); }
    ctx.strokeStyle = strokeColor;
    ctx.stroke();
}

// ── Hexagon ──
function drawHex(
    ctx: CanvasRenderingContext2D, cx: number, cy: number, r: number,
    rot: number, progress: number, stroke: string, fill: string | null
) {
    ctx.save();
    ctx.translate(cx, cy);
    ctx.rotate(rot);
    const edges = 6, drawn = progress * edges;
    ctx.beginPath();
    for (let i = 0; i < edges; i++) {
        const frac = Math.min(1, Math.max(0, drawn - i));
        if (frac <= 0) break;
        const a0 = (TAU / edges) * i - TAU / 12;
        const a1 = (TAU / edges) * (i + 1) - TAU / 12;
        const x0 = r * Math.cos(a0), y0 = r * Math.sin(a0);
        const x1 = r * Math.cos(a1), y1 = r * Math.sin(a1);
        if (i === 0) ctx.moveTo(x0, y0);
        ctx.lineTo(x0 + (x1 - x0) * frac, y0 + (y1 - y0) * frac);
    }
    if (progress >= 1) { ctx.closePath(); if (fill) { ctx.fillStyle = fill; ctx.fill(); } }
    ctx.strokeStyle = stroke;
    ctx.stroke();
    ctx.restore();
}

// ── Particles ──
interface Particle {
    bx: number; by: number; speed: number; size: number; bright: number; phase: number;
}
const PARTICLES: Particle[] = [];
for (let i = 0; i < 150; i++) {
    const a = Math.random() * TAU, r = 0.3 + Math.random() * 0.7;
    PARTICLES.push({
        bx: Math.cos(a) * r, by: Math.sin(a) * r,
        speed: 0.3 + Math.random() * 0.7,
        size: 0.5 + Math.random() * 2,
        bright: 0.2 + Math.random() * 0.8,
        phase: Math.random() * TAU,
    });
}

function ease(t: number) { return t < 0.5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2; }
function cl(v: number, lo: number, hi: number) { return Math.max(lo, Math.min(hi, v)); }
function lerp(a: number, b: number, t: number) { return a + (b - a) * t; }

// ── Main frame renderer ──
function renderFrame(ctx: CanvasRenderingContext2D, frameIndex: number, w: number, h: number) {
    const t = frameIndex / TOTAL_FRAMES;
    const cx = w / 2, cy = h / 2;
    const sz = w * 0.35;

    ctx.fillStyle = "#08080a";
    ctx.fillRect(0, 0, w, h);

    // Radial glow
    const glowR = w * 0.5;
    const grd = ctx.createRadialGradient(cx, cy, 0, cx, cy, glowR);
    grd.addColorStop(0, "rgba(255,255,255,.025)");
    grd.addColorStop(0.4, "rgba(255,255,255,.01)");
    grd.addColorStop(1, "transparent");
    ctx.fillStyle = grd;
    ctx.fillRect(0, 0, w, h);

    // Grid dots
    ctx.fillStyle = "rgba(255,255,255,.012)";
    const sp = 60;
    for (let gx = sp; gx < w; gx += sp) {
        for (let gy = sp; gy < h; gy += sp) {
            const dist = Math.sqrt((gx - cx) ** 2 + (gy - cy) ** 2) / sz;
            if (dist < 2.5) { ctx.beginPath(); ctx.arc(gx, gy, 0.5, 0, TAU); ctx.fill(); }
        }
    }

    // ═══ PHASE 1: Shield + Lock (0 → 0.2) ═══
    if (t < 0.35) {
        const p = cl(t / 0.2, 0, 1);
        const shieldP = ease(cl(p / 0.6, 0, 1));
        ctx.lineWidth = 1.5;
        drawShield(ctx, cx, cy, sz * 0.6, shieldP,
            `rgba(255,255,255,${0.35 * Math.min(1, p * 2)})`,
            shieldP >= 1 ? "rgba(255,255,255,.01)" : null
        );

        const lockP = ease(cl((p - 0.3) / 0.4, 0, 1));
        if (lockP > 0.01) {
            const ls = sz * 0.12 * lockP;
            ctx.strokeStyle = `rgba(255,255,255,${0.5 * lockP})`; ctx.lineWidth = 1.5;
            ctx.beginPath(); ctx.arc(cx, cy - ls * 0.4, ls * 0.45, Math.PI, 0); ctx.stroke();
            ctx.strokeStyle = `rgba(255,255,255,${0.4 * lockP})`; ctx.lineWidth = 1;
            ctx.beginPath(); ctx.roundRect(cx - ls * 0.55, cy - ls * 0.1, ls * 1.1, ls * 0.85, 4); ctx.stroke();
            const khP = ease(cl((p - 0.6) / 0.3, 0, 1));
            if (khP > 0.01) {
                ctx.fillStyle = `rgba(255,255,255,${0.25 * khP})`;
                ctx.beginPath(); ctx.arc(cx, cy + ls * 0.15, ls * 0.1 * khP, 0, TAU); ctx.fill();
            }
        }

        if (p > 0.6) {
            const tp = ease(cl((p - 0.6) / 0.3, 0, 1));
            const tags = ["$500 MAX", "24H TTL", "PURCHASE", "USD"];
            tags.forEach((tg, i) => {
                const delay = i * 0.08;
                const tagP = ease(cl((tp - delay) / 0.4, 0, 1));
                if (tagP < 0.01) return;
                const tx = cx + sz * 0.55, ty = cy - sz * 0.25 + i * 28;
                ctx.globalAlpha = tagP;
                ctx.strokeStyle = "rgba(255,255,255,.12)"; ctx.lineWidth = 0.5;
                ctx.beginPath(); ctx.roundRect(tx - 38, ty - 10, 76, 20, 4); ctx.stroke();
                ctx.font = '500 9px "Space Mono",monospace'; ctx.textAlign = "center";
                ctx.fillStyle = "rgba(255,255,255,.4)"; ctx.fillText(tg, tx, ty + 3);
                ctx.globalAlpha = 1;
            });
        }
    }

    // ═══ PHASE 2: Token Minting (0.2 → 0.4) ═══
    if (t > 0.15 && t < 0.55) {
        const p = cl((t - 0.2) / 0.2, 0, 1);
        const fadeOut = cl(1 - (t - 0.42) / 0.08, 0, 1);
        const v = ease(p) * fadeOut;
        if (v > 0.005) {
            const hexR = sz * 0.5;
            ctx.lineWidth = 1.5;
            drawHex(ctx, cx, cy, hexR * v, t * -0.2, ease(cl(p / 0.5, 0, 1)),
                `rgba(255,255,255,${0.4 * v})`, p > 0.7 ? `rgba(255,255,255,${0.015 * v})` : null
            );
            if (p > 0.3) {
                const ip = ease(cl((p - 0.3) / 0.3, 0, 1));
                ctx.lineWidth = 0.5;
                drawHex(ctx, cx, cy, hexR * 0.45 * v, t * 0.15, ip,
                    `rgba(255,255,255,${0.12 * ip * fadeOut})`, null
                );
            }
            if (p > 0.2) {
                const op = cl((p - 0.2) / 0.5, 0, 1);
                for (let i = 0; i < 16; i++) {
                    const a = (TAU / 16) * i + t * TAU * 2;
                    const r2 = hexR * v * 1.12;
                    const px2 = cx + Math.cos(a) * r2, py2 = cy + Math.sin(a) * r2;
                    ctx.fillStyle = `rgba(255,255,255,${0.06 * op * fadeOut * (Math.sin(a * 2) * 0.5 + 0.5)})`;
                    ctx.beginPath(); ctx.arc(px2, py2, 1, 0, TAU); ctx.fill();
                }
            }
            if (p > 0.4) {
                const lp = ease(cl((p - 0.4) / 0.3, 0, 1)) * fadeOut;
                ctx.textAlign = "center";
                ctx.font = '700 13px "Space Mono",monospace';
                ctx.fillStyle = `rgba(255,255,255,${0.55 * lp})`;
                ctx.fillText("BISCUIT TOKEN", cx, cy - 8);
                ctx.font = '400 10px "Space Mono",monospace';
                ctx.fillStyle = `rgba(255,255,255,${0.3 * lp})`;
                ctx.fillText("scope: purchase ≤ $500", cx, cy + 12);
                ctx.fillText("sign: ed25519 · attenuable", cx, cy + 28);
            }
        }
    }

    // ═══ PHASE 3: Delegation Chain (0.4 → 0.67) ═══
    if (t > 0.35 && t < 0.75) {
        const p = cl((t - 0.4) / 0.27, 0, 1);
        const fadeOut = cl(1 - (t - 0.7) / 0.05, 0, 1);

        const nodes = [
            { bx: -0.45, by: -0.25, l: "USER", s: "$500" },
            { bx: -0.1, by: 0.15, l: "AGENT A", s: "$500" },
            { bx: 0.25, by: -0.1, l: "AGENT B", s: "$347" },
            { bx: 0.5, by: 0.18, l: "MERCHANT", s: "✓" },
        ];

        nodes.forEach((n, i) => {
            const nd = i * 0.12;
            const np = ease(cl((p - nd) / 0.18, 0, 1)) * fadeOut;
            if (np < 0.005) return;
            const nx2 = cx + n.bx * sz * 1.3, ny2 = cy + n.by * sz;

            if (i < nodes.length - 1) {
                const next = nodes[i + 1];
                const lp2 = ease(cl((p - nd - 0.06) / 0.18, 0, 1)) * fadeOut;
                if (lp2 > 0.005) {
                    const nx3 = cx + next.bx * sz * 1.3, ny3 = cy + next.by * sz;
                    const ex = lerp(nx2, nx3, lp2), ey = lerp(ny2, ny3, lp2);
                    ctx.setLineDash([4, 6]);
                    ctx.strokeStyle = `rgba(255,255,255,${0.1 * lp2})`; ctx.lineWidth = 0.8;
                    ctx.beginPath(); ctx.moveTo(nx2, ny2); ctx.lineTo(ex, ey); ctx.stroke();
                    ctx.setLineDash([]);

                    const fp = cl((p - nd - 0.1) / 0.5, 0, 1);
                    if (fp > 0.005) {
                        for (let j = 0; j < 3; j++) {
                            const pt2 = (fp * 3 + j * 0.33) % 1;
                            const ppx = lerp(nx2, nx3, pt2), ppy = lerp(ny2, ny3, pt2);
                            const fade = Math.sin(pt2 * Math.PI);
                            ctx.fillStyle = `rgba(255,255,255,${0.2 * fade * lp2})`;
                            ctx.beginPath(); ctx.arc(ppx, ppy, 1.5, 0, TAU); ctx.fill();
                        }
                    }
                }
            }

            const nr = 18 * np;
            ctx.strokeStyle = `rgba(255,255,255,${0.3 * np})`; ctx.lineWidth = 1;
            ctx.beginPath(); ctx.arc(nx2, ny2, nr, 0, TAU); ctx.stroke();
            ctx.fillStyle = `rgba(255,255,255,${0.7 * np})`;
            ctx.beginPath(); ctx.arc(nx2, ny2, 2.5 * np, 0, TAU); ctx.fill();
            ctx.font = `700 ${Math.round(10 * np)}px "Space Mono",monospace`;
            ctx.textAlign = "center";
            ctx.fillStyle = `rgba(255,255,255,${0.45 * np})`;
            ctx.fillText(n.s, nx2, ny2 - nr - 8);
            ctx.font = `400 ${Math.round(8 * np)}px "Space Mono",monospace`;
            ctx.fillStyle = `rgba(255,255,255,${0.3 * np})`;
            ctx.fillText(n.l, nx2, ny2 + nr + 12);
        });

        if (p > 0.6) {
            const abP = ease(cl((p - 0.6) / 0.25, 0, 1)) * fadeOut;
            const bw = sz * 1.1, bx = cx - bw / 2, by = cy + sz * 0.45;
            ctx.fillStyle = `rgba(255,255,255,${0.02 * abP})`; ctx.fillRect(bx, by, bw * abP, 3);
            ctx.fillStyle = `rgba(255,255,255,${0.08 * abP})`; ctx.fillRect(bx, by, bw * 0.694 * abP, 3);
            ctx.font = '400 9px "Space Mono",monospace'; ctx.textAlign = "center";
            ctx.fillStyle = `rgba(255,255,255,${0.25 * abP})`;
            ctx.fillText("$500 → $500 → $347   ATTENUATION →", cx, by + 18);
        }
    }

    // ═══ PHASE 4: Shield Verification (0.67 → 0.87) ═══
    if (t > 0.6) {
        const p = cl((t - 0.67) / 0.2, 0, 1);
        const v4 = ease(p);
        if (v4 > 0.005) {
            const ss2 = sz * 0.65;
            ctx.lineWidth = 2;
            drawShield(ctx, cx, cy, ss2 * Math.min(1, v4 * 1.2), ease(cl(p / 0.4, 0, 1)),
                `rgba(255,255,255,${0.4 * v4})`,
                p > 0.5 ? `rgba(255,255,255,${0.015 * ease((p - 0.5) * 2)})` : null
            );

            const ckP = ease(cl((p - 0.4) / 0.25, 0, 1));
            if (ckP > 0.01) {
                const cs = ss2 * 0.3;
                ctx.strokeStyle = `rgba(255,255,255,${0.7 * ckP})`; ctx.lineWidth = 3;
                ctx.lineCap = "round"; ctx.lineJoin = "round";
                ctx.beginPath();
                if (ckP < 0.4) {
                    const f = ckP / 0.4;
                    ctx.moveTo(cx - cs * 0.45, cy + cs * 0.05);
                    ctx.lineTo(lerp(cx - cs * 0.45, cx - cs * 0.05, f), lerp(cy + cs * 0.05, cy + cs * 0.45, f));
                } else {
                    const f = (ckP - 0.4) / 0.6;
                    ctx.moveTo(cx - cs * 0.45, cy + cs * 0.05);
                    ctx.lineTo(cx - cs * 0.05, cy + cs * 0.45);
                    ctx.lineTo(lerp(cx - cs * 0.05, cx + cs * 0.5, f), lerp(cy + cs * 0.45, cy - cs * 0.3, f));
                }
                ctx.stroke(); ctx.lineCap = "butt"; ctx.lineJoin = "miter";
            }

            if (p > 0.6) {
                const lp = ease(cl((p - 0.6) / 0.2, 0, 1));
                ctx.font = '800 16px "Syne",sans-serif'; ctx.textAlign = "center";
                ctx.fillStyle = `rgba(255,255,255,${0.6 * lp})`;
                ctx.fillText("V E R I F I E D", cx, cy + ss2 * 1.05 + 32);
                ctx.font = '400 10px "Space Mono",monospace';
                ctx.fillStyle = `rgba(255,255,255,${0.3 * lp})`;
                ctx.fillText("receipt on file · court-admissible", cx, cy + ss2 * 1.05 + 54);
            }

            if (p > 0.5) {
                const puP = (p - 0.5) / 0.5;
                for (let i = 0; i < 2; i++) {
                    const pp = ((puP * 2 + i * 0.5) % 1);
                    const prs = ss2 * (1 + pp * 0.4);
                    ctx.lineWidth = 0.5;
                    drawShield(ctx, cx, cy, prs, 1, `rgba(255,255,255,${0.025 * (1 - pp)})`, null);
                }
            }
        }
    }

    // ═══ Ambient particles ═══
    for (let i = 0; i < PARTICLES.length; i += 2) {
        const pt = PARTICLES[i];
        const angle = t * TAU * pt.speed + pt.phase;
        const dist = sz * (0.6 + pt.by * 0.8);
        const px = cx + Math.cos(angle) * dist * (0.8 + pt.bx * 0.4);
        const py = cy + Math.sin(angle) * dist * (0.6 + pt.bx * 0.3);
        const wander = Math.sin(t * 10 + pt.phase) * sz * 0.04;
        const fpx = px + wander, fpy = py + Math.cos(t * 8 + pt.phase) * sz * 0.02;
        const d = Math.sqrt((fpx - cx) ** 2 + (fpy - cy) ** 2) / (sz * 1.5);
        const alpha = pt.bright * 0.04 * (1 - d);
        if (alpha < 0.003 || fpx < 0 || fpx > w || fpy < 0 || fpy > h) continue;
        ctx.fillStyle = `rgba(255,255,255,${alpha})`;
        ctx.beginPath(); ctx.arc(fpx, fpy, pt.size * 0.5, 0, TAU); ctx.fill();
    }
}

// ── Text Panel Data ──
interface PanelData {
    start: number; end: number; top: string;
    align: "left" | "right" | "center";
    tagClass?: string; tag: string; title: string; titleSpan: string;
    desc: string;
    code?: string;
    stats?: { num: string; label: string }[];
}

const panels: PanelData[] = [
    {
        start: 0.02, end: 0.17, top: "5vh", align: "left", tagClass: "blue",
        tag: "01 — User Consent",
        title: "The user defines ", titleSpan: "what the agent can do",
        desc: "\"Buy me a flight under $500.\" AgentAuth captures this intent as a cryptographically signed consent — scoped by amount, merchant, time, and action.",
        code: `<span class="mth">POST</span> <span class="url">/v1/consents</span><br><br>{ <span class="w">"intent"</span>: <span class="g">"Buy flight NYC"</span>,<br>&nbsp;&nbsp;<span class="w">"max_amount"</span>: <span class="a">500</span>,<br>&nbsp;&nbsp;<span class="w">"currency"</span>: <span class="g">"USD"</span>,<br>&nbsp;&nbsp;<span class="w">"expires_in"</span>: <span class="a">86400</span> }`,
    },
    {
        start: 0.20, end: 0.37, top: "120vh", align: "right",
        tag: "02 — Token Minting",
        title: "A Biscuit token ", titleSpan: "is minted",
        desc: "Cryptographic bearer credential with embedded constraints. Biscuit tokens support capability attenuation — permissions can only decrease through delegation chains. ED25519 signed.",
        code: `<span class="d">// delegation_token</span><br>{ <span class="w">"token"</span>: <span class="g">"bsc_eyJ..."</span>,<br>&nbsp;&nbsp;<span class="w">"type"</span>: <span class="g">"biscuit_v2"</span>,<br>&nbsp;&nbsp;<span class="w">"signing"</span>: <span class="g">"ed25519"</span>,<br>&nbsp;&nbsp;<span class="w">"attenuable"</span>: <span class="b">true</span>,<br>&nbsp;&nbsp;<span class="w">"scope"</span>: <span class="g">"purchase ≤ $500"</span> }`,
    },
    {
        start: 0.40, end: 0.58, top: "240vh", align: "left", tagClass: "amber",
        tag: "03 — Delegation Chain",
        title: "Permissions ", titleSpan: "attenuate at each hop",
        desc: "Agent A delegates to Agent B. At each hop, the token's scope mathematically shrinks. $500 → $347. A payment agent can never exceed the original spending limit.",
        code: `<span class="mth">POST</span> <span class="url">/v1/authorize</span><br><br>{ <span class="w">"action"</span>: <span class="g">"purchase"</span>,<br>&nbsp;&nbsp;<span class="w">"amount"</span>: <span class="a">347</span>,<br>&nbsp;&nbsp;<span class="w">"merchant_id"</span>: <span class="g">"merch_united"</span> }<br><br><span class="d">→</span> { <span class="w">"decision"</span>: <span class="g">"ALLOW"</span>, <span class="w">"latency"</span>: <span class="g">"0.4ms"</span> }`,
    },
    {
        start: 0.62, end: 0.80, top: "370vh", align: "right",
        tag: "04 — Merchant Verification",
        title: "Cryptographic proof ", titleSpan: "on file",
        desc: "Merchant verifies offline in under 1ms. Zero network round-trips. The receipt is court-admissible evidence. Chargebacks become mathematically impossible.",
        code: `<span class="mth">POST</span> <span class="url">/v1/verify</span><br><br>{ <span class="w">"auth_code"</span>: <span class="g">"auth_7k9..."</span> }<br><br><span class="d">→</span> { <span class="w">"valid"</span>: <span class="b">true</span>,<br>&nbsp;&nbsp;&nbsp;&nbsp;<span class="w">"receipt"</span>: <span class="g">"rcp_x8m..."</span> }`,
        stats: [
            { num: "<1ms", label: "Verify" },
            { num: "0", label: "API Calls" },
            { num: "100%", label: "Defense" },
        ],
    },
    {
        start: 0.84, end: 0.97, top: "500vh", align: "center",
        tag: "The Complete Authorization Flow",
        title: "Consent → Token → Delegation → Proof", titleSpan: "",
        desc: "Four API calls. One delegation chain. Irrefutable cryptographic evidence that the human authorized every AI agent purchase. Auth0 sold for $6.5B building this for humans. We're building it for agents.",
    },
];

interface SequenceSectionProps {
    onProgress: (pct: number) => void;
    onReady: () => void;
}

export function SequenceSection({ onProgress, onReady }: SequenceSectionProps) {
    const sectionRef = useRef<HTMLDivElement>(null);
    const canvasRef = useRef<HTMLCanvasElement>(null);
    const [visiblePanels, setVisiblePanels] = useState<Set<number>>(new Set());
    const currentFrameRef = useRef(-1);

    useEffect(() => {
        const canvas = canvasRef.current;
        const section = sectionRef.current;
        if (!canvas || !section) return;
        const ctx = canvas.getContext("2d");
        if (!ctx) return;

        onProgress(100);
        onReady();

        function resize() {
            if (!canvas) return;
            const dpr = Math.min(devicePixelRatio || 1, 2);
            canvas.width = innerWidth * dpr;
            canvas.height = innerHeight * dpr;
            canvas.style.width = innerWidth + "px";
            canvas.style.height = innerHeight + "px";
            ctx!.setTransform(dpr, 0, 0, dpr, 0, 0);
            currentFrameRef.current = -1;
            update();
        }

        function update() {
            ticking = false;
            if (!section || !canvas) return;
            const rect = section.getBoundingClientRect();
            const sH = section.scrollHeight - innerHeight;
            const scrolled = -rect.top;
            const frac = Math.max(0, Math.min(1, scrolled / sH));
            const idx = Math.min(TOTAL_FRAMES - 1, Math.floor(frac * TOTAL_FRAMES));

            if (idx !== currentFrameRef.current) {
                currentFrameRef.current = idx;
                renderFrame(ctx, idx, innerWidth, innerHeight);
            }

            // Update visible panels
            const newVisible = new Set<number>();
            panels.forEach((panel, i) => {
                if (frac >= panel.start && frac <= panel.end) newVisible.add(i);
            });
            setVisiblePanels(newVisible);
        }

        resize();
        window.addEventListener("resize", resize);

        let ticking = false;
        function onScroll() {
            if (!ticking) { requestAnimationFrame(update); ticking = true; }
        }
        window.addEventListener("scroll", onScroll, { passive: true });
        update();

        return () => {
            window.removeEventListener("resize", resize);
            window.removeEventListener("scroll", onScroll);
        };
    }, [onProgress, onReady]);

    return (
        <section className="seq-sequence-section" id="sequence" ref={sectionRef}>
            <div className="seq-canvas-wrap">
                <canvas ref={canvasRef} />
            </div>
            <div className="seq-text-panels">
                {panels.map((panel, i) => (
                    <div
                        key={i}
                        className={`seq-text-panel ${panel.align === "right" ? "right" : panel.align === "center" ? "center" : ""} ${visiblePanels.has(i) ? "visible" : ""}`}
                        style={{ top: panel.top }}
                    >
                        <div className="panel-inner">
                            <div className={`seq-panel-tag ${panel.tagClass || ""}`}>{panel.tag}</div>
                            <div className="seq-panel-title">
                                {panel.title}
                                {panel.titleSpan && <span>{panel.titleSpan}</span>}
                            </div>
                            <div className="seq-panel-desc">{panel.desc}</div>
                            {panel.code && (
                                <div
                                    className="seq-panel-code"
                                    dangerouslySetInnerHTML={{ __html: panel.code }}
                                />
                            )}
                            {panel.stats && (
                                <div className="seq-stat-row">
                                    {panel.stats.map((s) => (
                                        <div key={s.label}>
                                            <div className="seq-stat-num">{s.num}</div>
                                            <div className="seq-stat-label">{s.label}</div>
                                        </div>
                                    ))}
                                </div>
                            )}
                        </div>
                    </div>
                ))}
            </div>
        </section>
    );
}
