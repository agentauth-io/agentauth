import { BrowserRouter, Routes, Route, useNavigate } from "react-router-dom";
import { Hero } from "./components/Hero";
import { Stats } from "./components/Stats";
import { Features } from "./components/Features";
import { TrustLogos } from "./components/TrustLogos";
import { HowItWorks } from "./components/HowItWorks";
import { Pricing } from "./components/Pricing";
import { FAQ } from "./components/FAQ";
import { Contact } from "./components/Contact";

// Simple Home page - Landing only
function HomePage() {
  return (
    <div className="min-h-screen bg-[#0f0f1a]">
      <Hero />
      <TrustLogos />
      <Stats />
      <Features />
      <HowItWorks />
      <Pricing />
      <FAQ />
      <Footer />
    </div>
  );
}

// Contact page
function ContactPage() {
  const navigate = useNavigate();
  return <Contact onBack={() => navigate("/")} />;
}

// Demo redirect - goes to live API docs
function DemoPage() {
  window.location.href = "https://characteristic-inessa-agentauth-0a540dd6.koyeb.app/docs";
  return (
    <div className="min-h-screen flex items-center justify-center bg-black">
      <div className="text-center">
        <div className="w-8 h-8 border-2 border-white border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
        <p className="text-gray-400">Redirecting to API Demo...</p>
      </div>
    </div>
  );
}

// Docs redirect - goes to documentation
function DocsPage() {
  window.location.href = "https://characteristic-inessa-agentauth-0a540dd6.koyeb.app/docs";
  return (
    <div className="min-h-screen flex items-center justify-center bg-black">
      <div className="text-center">
        <div className="w-8 h-8 border-2 border-white border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
        <p className="text-gray-400">Redirecting to Docs...</p>
      </div>
    </div>
  );
}

// Simple Footer
function Footer() {
  return (
    <footer className="relative bg-[#0a0a0f] border-t border-white/5 py-16 px-6">
      <div className="max-w-6xl mx-auto">
        <div className="flex flex-col md:flex-row justify-between items-start gap-12 mb-12">
          {/* Logo & Description */}
          <div className="max-w-sm">
            <div className="flex items-center gap-3 mb-4">
              <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-purple-500 to-blue-600 flex items-center justify-center">
                <span className="text-white font-bold text-lg">A</span>
              </div>
              <span className="text-white font-semibold text-xl">AgentAuth</span>
            </div>
            <p className="text-gray-500 text-sm leading-relaxed">
              The authorization layer for AI agent payments. Let autonomous systems transact safely.
            </p>
          </div>

          {/* Links */}
          <div className="flex gap-16">
            <div>
              <h4 className="text-white font-medium mb-4 text-sm">Product</h4>
              <div className="flex flex-col gap-3">
                <a href="/docs" className="text-gray-500 hover:text-white transition-colors text-sm">Documentation</a>
                <a href="/demo" className="text-gray-500 hover:text-white transition-colors text-sm">Live Demo</a>
                <a href="#pricing" className="text-gray-500 hover:text-white transition-colors text-sm">Pricing</a>
              </div>
            </div>
            <div>
              <h4 className="text-white font-medium mb-4 text-sm">Company</h4>
              <div className="flex flex-col gap-3">
                <a href="/contact" className="text-gray-500 hover:text-white transition-colors text-sm">Contact</a>
                <a href="https://github.com/agentauth-io/agentauth" target="_blank" rel="noopener noreferrer" className="text-gray-500 hover:text-white transition-colors text-sm">GitHub</a>
                <a href="mailto:hello@agentauth.in" className="text-gray-500 hover:text-white transition-colors text-sm">Email</a>
              </div>
            </div>
          </div>
        </div>

        {/* Bottom bar */}
        <div className="pt-8 border-t border-white/5 flex flex-col md:flex-row justify-between items-center gap-4">
          <p className="text-gray-600 text-sm">
            © 2026 AgentAuth. All rights reserved.
          </p>
          <div className="flex items-center gap-6">
            <a href="#" className="text-gray-600 hover:text-gray-400 transition-colors text-sm">Privacy</a>
            <a href="#" className="text-gray-600 hover:text-gray-400 transition-colors text-sm">Terms</a>
          </div>
        </div>
      </div>
    </footer>
  );
}

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<HomePage />} />
        <Route path="/demo" element={<DemoPage />} />
        <Route path="/docs" element={<DocsPage />} />
        <Route path="/contact" element={<ContactPage />} />
        {/* All other routes go to home */}
        <Route path="*" element={<HomePage />} />
      </Routes>
    </BrowserRouter>
  );
}
