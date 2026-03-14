import { useEffect, useRef } from "react";

const features = [
  {
    num: "01",
    title: "Biscuit Tokens",
    desc: "Cryptographic bearer credentials. Capability attenuation \u2014 permissions only decrease.",
  },
  {
    num: "02",
    title: "Offline Verification",
    desc: "No network round-trips. Edge verification in under 1ms.",
  },
  {
    num: "03",
    title: "Protocol Agnostic",
    desc: "Visa TAP, Stripe ACP, Google AP2, Mastercard Agent Pay.",
  },
  {
    num: "04",
    title: "Merchant-First",
    desc: "Built for the party losing $125B/year to chargebacks.",
  },
  {
    num: "05",
    title: "Granular Policies",
    desc: "Spending caps, merchant lists, time windows, categories.",
  },
  {
    num: "06",
    title: "Any Framework",
    desc: "LangChain, CrewAI, AutoGen, OpenAI Agents SDK.",
  },
];

export function Features() {
  const headerRef = useRef<HTMLDivElement>(null);
  const gridRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const headerObserver = new IntersectionObserver(
      (entries) => {
        entries.forEach((e) => {
          if (e.isIntersecting) e.target.classList.add("in-view");
        });
      },
      { threshold: 0.1 }
    );

    if (headerRef.current) headerObserver.observe(headerRef.current);

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

    const cards = gridRef.current?.querySelectorAll(".seq-feat");
    cards?.forEach((el) => cardObserver.observe(el));

    return () => {
      headerObserver.disconnect();
      cardObserver.disconnect();
    };
  }, []);

  return (
    <section className="seq-feat-sec" id="features">
      <div className="seq-api-header seq-section-reveal" ref={headerRef}>
        <div className="seq-panel-tag" style={{ marginBottom: 14 }}>
          Infrastructure
        </div>
        <h2>
          Built for <span>agentic commerce</span>
        </h2>
      </div>

      <div className="seq-feat-grid" ref={gridRef}>
        {features.map((f) => (
          <div className="seq-feat" key={f.num}>
            <div className="seq-f-n">{f.num}</div>
            <div className="seq-f-t">{f.title}</div>
            <div className="seq-f-b">{f.desc}</div>
          </div>
        ))}
      </div>
    </section>
  );
}
