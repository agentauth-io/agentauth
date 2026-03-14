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
    const sectionRef = useRef<HTMLDivElement>(null);
    const headerRef = useRef<HTMLDivElement>(null);
    const gridRef = useRef<HTMLDivElement>(null);
    const sdkRef = useRef<HTMLDivElement>(null);

    useEffect(() => {
        const observer = new IntersectionObserver(
            (entries) => {
                entries.forEach((e) => {
                    if (e.isIntersecting) {
                        e.target.classList.add("in-view");
                    }
                });
            },
            { threshold: 0.1 }
        );

        // Observe header
        if (headerRef.current) observer.observe(headerRef.current);
        if (sdkRef.current) observer.observe(sdkRef.current);

        // Observe cards with stagger
        const cardObserver = new IntersectionObserver(
            (entries) => {
                entries.forEach((e) => {
                    if (e.isIntersecting) {
                        const parent = e.target.parentElement;
                        if (parent) {
                            const idx = Array.from(parent.children).indexOf(e.target);
                            (e.target as HTMLElement).style.transitionDelay = `${idx * 0.08}s`;
                        }
                        e.target.classList.add("in-view");
                    }
                });
            },
            { threshold: 0.1 }
        );

        const cards = gridRef.current?.querySelectorAll(".seq-api-c");
        cards?.forEach((el) => cardObserver.observe(el));

        return () => {
            observer.disconnect();
            cardObserver.disconnect();
        };
    }, []);

    return (
        <section className="seq-api-sec" id="api" ref={sectionRef}>
            <div className="seq-api-header seq-section-reveal" ref={headerRef}>
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

            <div className="seq-sdk-row seq-section-reveal" ref={sdkRef}>
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
