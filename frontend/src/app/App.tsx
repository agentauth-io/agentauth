import { BrowserRouter, Routes, Route, useNavigate } from "react-router-dom";
import { useState, useCallback } from "react";
import { Hero } from "./components/Hero";
import { Features } from "./components/Features";
import { Contact } from "./components/Contact";
import { Docs } from "./components/Docs";
import { GrainOverlay } from "./components/landing/GrainOverlay";
import { Loader } from "./components/landing/Loader";
import { SequenceSection } from "./components/landing/SequenceSection";
import { APISection } from "./components/landing/APISection";
import { TerminalDemo } from "./components/landing/TerminalDemo";
import { CTASection } from "./components/landing/CTASection";
import { DemoPage } from "./components/DemoPage";

// Landing page — sequence design
function HomePage() {
  const [progress, setProgress] = useState(0);
  const [loaded, setLoaded] = useState(false);

  const handleProgress = useCallback((pct: number) => setProgress(pct), []);
  const handleReady = useCallback(() => { }, []);
  const handleLoaderComplete = useCallback(() => setLoaded(true), []);

  return (
    <div style={{ background: "#08080a", minHeight: "100vh" }}>
      <GrainOverlay />
      {!loaded && <Loader progress={progress} onComplete={handleLoaderComplete} />}
      <Hero />
      <SequenceSection onProgress={handleProgress} onReady={handleReady} />
      <APISection />
      <Features />
      <TerminalDemo />
      <CTASection />
      <SequenceFooter />
    </div>
  );
}

// Contact page
function ContactPage() {
  const navigate = useNavigate();
  return <Contact onBack={() => navigate("/")} />;
}

// Docs page
function DocsPage() {
  const navigate = useNavigate();
  return <Docs onBack={() => navigate("/")} />;
}

// Footer matching sequence design
function SequenceFooter() {
  return (
    <footer className="seq-footer">
      <p>
        © 2026 AgentAuth ·{" "}
        <a href="https://agentauth.in">agentauth.in</a> · Cryptographic
        authorization for AI agent commerce
      </p>
    </footer>
  );
}

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<HomePage />} />
        <Route path="/docs" element={<DocsPage />} />
        <Route path="/contact" element={<ContactPage />} />
        <Route path="/demo" element={<DemoPage />} />
        {/* All other routes go to home */}
        <Route path="*" element={<HomePage />} />
      </Routes>
    </BrowserRouter>
  );
}
