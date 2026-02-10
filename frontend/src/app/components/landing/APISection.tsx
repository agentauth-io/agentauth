import { useEffect, useRef } from "react";

const endpoints = [
    { method: "POST", cls: "post", path: "/v1/consents", desc: "Create signed consent with constraints" },
    { method: "POST", cls: "post", path: "/v1/authorize", desc: "Verify delegation token against transaction" },
    { method: "POST", cls: "post", path: "/v1/verify", desc: "Merchant verification with receipt" },
    { method: "GET", cls: "get", path: "/v1/consents/:id", desc: "Retrieve consent for audit trail" },
    { method: "GET", cls: "get", path: "/v1/dashboard", desc: "Real-time metrics & approval rates" },
    { method: "DELETE", cls: "del", path: "/v1/consents/:id", desc: "Revoke consent, invalidate tokens" },
];

const sdks = [
    { lang: "py", cmd: "pip install agentauth" },
    { lang: "ts", cmd: "npm i @agentauth/sdk" },
    { lang: "rs", cmd: "cargo add agentauth" },
];

export function APISection() {
    const gridRef = useRef<HTMLDivElement>(null);

    useEffect(() => {
        const observer = new IntersectionObserver(
            (entries) => {
                entries.forEach((e) => {
                    if (e.isIntersecting) {
                        e.target.classList.add("in-view");
                        const parent = e.target.parentElement;
                        if (parent) {
                            const idx = Array.from(parent.children).indexOf(e.target);
                            (e.target as HTMLElement).style.transitionDelay = `${idx * 0.06}s`;
                        }
                    }
                });
            },
            { threshold: 0.15 }
        );

        const cards = gridRef.current?.querySelectorAll(".seq-api-c");
        cards?.forEach((el) => observer.observe(el));

        return () => observer.disconnect();
    }, []);

    return (
        <section className="seq-api-sec" id="api">
            <div className="seq-api-header">
                <div className="seq-panel-tag" style={{ marginBottom: 14 }}>
                    API Reference
                </div>
                <h2>
                    RESTful endpoints <span>for every step</span>
                </h2>
            </div>

            <div className="seq-api-grid" ref={gridRef}>
                {endpoints.map((ep) => (
                    <div className="seq-api-c" key={ep.path + ep.method}>
                        <div className={`seq-ac-m ${ep.cls}`}>{ep.method}</div>
                        <div className="seq-ac-e">{ep.path}</div>
                        <div className="seq-ac-d">{ep.desc}</div>
                    </div>
                ))}
            </div>

            <div className="seq-sdk-row">
                {sdks.map((s) => (
                    <div className="seq-sdk" key={s.lang}>
                        <span className={`seq-dot ${s.lang}`} />
                        {s.cmd}
                    </div>
                ))}
            </div>
        </section>
    );
}
