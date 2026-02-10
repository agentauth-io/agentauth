import { useState } from "react";

export function Hero() {
  const [copied, setCopied] = useState(false);

  const handleCopy = () => {
    navigator.clipboard.writeText("npm install @agentauth/sdk");
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <>
      {/* Navigation */}
      <nav className="seq-nav">
        <a href="/" className="seq-logo">
          <svg viewBox="0 0 24 28" fill="none">
            <path
              d="M12 1L2 5.5v7c0 7.5 4.5 13.5 10 14.5 5.5-1 10-7 10-14.5v-7L12 1Z"
              stroke="#e8e6e1"
              strokeWidth="1.2"
            />
            <path
              d="M8.5 14l2.5 2.5 5-5"
              stroke="#e8e6e1"
              strokeWidth="1.2"
              strokeLinecap="round"
              strokeLinejoin="round"
            />
          </svg>
          <b>AgentAuth</b>
          <small>API</small>
        </a>
        <div className="seq-nav-r">
          <a href="/docs">Docs</a>
          <a href="/demo">Demo</a>
          <a href="#waitlist" className="seq-nav-cta">
            Join Waitlist →
          </a>
        </div>
      </nav>

      {/* Hero */}
      <section className="seq-hero">
        <div className="seq-hero-tag">
          Cryptographic Authorization Infrastructure
        </div>
        <h1>Authorization API for AI Agent Commerce</h1>
        <p>
          One API to prove every AI agent purchase was human-approved. Delegation
          tokens that make chargebacks mathematically impossible.
        </p>
        <div className="seq-hero-actions">
          <a className="seq-btn seq-btn-g" href="#waitlist">
            Join Waitlist
          </a>
          <a className="seq-btn seq-btn-o" href="#sequence">
            See How It Works ↓
          </a>
        </div>
        <div className="seq-hero-install">
          <div className="seq-ibar" onClick={handleCopy}>
            <span className="pr">$</span>
            <span className="cm">npm install @agentauth/sdk</span>
            <span className="cp">{copied ? "COPIED!" : "COPY"}</span>
          </div>
        </div>
        <div className="seq-scroll-cue">
          <span>Scroll</span>
          <div className="arrow" />
        </div>
      </section>
    </>
  );
}
