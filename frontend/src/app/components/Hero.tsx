import { useState, useEffect, useRef } from "react";

export function Hero() {
  const [copied, setCopied] = useState(false);
  const [isMenuOpen, setIsMenuOpen] = useState(false);
  const heroContentRef = useRef<HTMLDivElement>(null);
  const scrollCueRef = useRef<HTMLDivElement>(null);
  const navRef = useRef<HTMLElement>(null);
  const progressRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    let ticking = false;
    function update() {
      ticking = false;
      const y = window.scrollY;
      const vh = window.innerHeight;
      const docH = document.documentElement.scrollHeight - vh;

      // Hero content parallax
      if (heroContentRef.current) {
        const progress = Math.min(1, y / (vh * 0.6));
        const opacity = Math.max(0, 1 - progress * 1.4);
        const translateY = y * 0.3;
        const scale = 1 - progress * 0.06;
        heroContentRef.current.style.opacity = String(opacity);
        heroContentRef.current.style.transform = `translateY(-${translateY}px) scale(${scale})`;
      }

      // Scroll cue fades out fast
      if (scrollCueRef.current) {
        scrollCueRef.current.style.opacity = String(Math.max(0, 1 - y / 120));
      }

      // Nav becomes more opaque as you scroll
      if (navRef.current) {
        const alpha = Math.min(0.95, 0.6 + (y / (vh * 0.4)) * 0.35);
        navRef.current.style.background = `rgba(5, 5, 8, ${alpha})`;
      }

      // Global scroll progress bar
      if (progressRef.current && docH > 0) {
        const pct = Math.min(100, (y / docH) * 100);
        progressRef.current.style.width = `${pct}%`;
      }
    }

    function onScroll() {
      if (!ticking) { requestAnimationFrame(update); ticking = true; }
    }
    window.addEventListener("scroll", onScroll, { passive: true });
    update();
    return () => window.removeEventListener("scroll", onScroll);
  }, []);

  const handleCopy = () => {
    navigator.clipboard.writeText("npm install @agentauth/sdk");
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <>
      {/* Navigation */}
      <nav className="seq-nav" ref={navRef}>
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

        {/* Desktop Nav */}
        <div className="seq-nav-r">
          <a href="/docs">Docs</a>
          <a href="/demo">Demo</a>
          <a href="#waitlist" className="seq-nav-cta">
            Join Waitlist →
          </a>
        </div>

        {/* Mobile Hamburger */}
        <button
          className="seq-mobile-toggle"
          onClick={() => setIsMenuOpen(!isMenuOpen)}
          aria-label="Toggle menu"
        >
          <div className={`ham-line ${isMenuOpen ? 'open' : ''}`} />
          <div className={`ham-line ${isMenuOpen ? 'open' : ''}`} />
        </button>

        {/* Mobile Menu Overlay */}
        <div className={`seq-mobile-menu ${isMenuOpen ? 'open' : ''}`}>
          <a href="/docs" onClick={() => setIsMenuOpen(false)}>Docs</a>
          <a href="/demo" onClick={() => setIsMenuOpen(false)}>Demo</a>
          <a href="#waitlist" className="seq-nav-cta" onClick={() => setIsMenuOpen(false)}>
            Join Waitlist →
          </a>
        </div>

        {/* Scroll progress bar */}
        <div className="seq-scroll-progress" ref={progressRef} />
      </nav>

      {/* Hero */}
      <section className="seq-hero">
        <div className="seq-hero-content" ref={heroContentRef}>
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
        </div>
        <div className="seq-scroll-cue" ref={scrollCueRef}>
          <span>Scroll</span>
          <div className="arrow" />
        </div>
      </section>
    </>
  );
}
