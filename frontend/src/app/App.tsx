import { BrowserRouter, Routes, Route, useNavigate } from "react-router-dom";
import { Hero } from "./components/Hero";
import { Features } from "./components/Features";
import { HowItWorks } from "./components/HowItWorks";
import { Pricing } from "./components/Pricing";
import { FAQ } from "./components/FAQ";
import { Contact } from "./components/Contact";

// Simple Home page - Landing only
function HomePage() {
  return (
    <div className="min-h-screen bg-black">
      <Hero />
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
    <footer className="bg-black border-t border-[#1d1d1f] py-12 px-6">
      <div className="max-w-6xl mx-auto">
        <div className="flex flex-col md:flex-row justify-between items-center gap-8">
          {/* Logo */}
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-lg bg-white flex items-center justify-center">
              <span className="text-black font-semibold text-sm">A</span>
            </div>
            <span className="text-white font-medium">AgentAuth</span>
          </div>

          {/* Links */}
          <div className="flex items-center gap-8">
            <a href="/docs" className="text-[#86868b] hover:text-white transition-colors text-sm">
              Docs
            </a>
            <a href="/demo" className="text-[#86868b] hover:text-white transition-colors text-sm">
              Demo
            </a>
            <a href="/contact" className="text-[#86868b] hover:text-white transition-colors text-sm">
              Contact
            </a>
            <a 
              href="https://github.com/agentauth-io/agentauth" 
              target="_blank" 
              rel="noopener noreferrer"
              className="text-[#86868b] hover:text-white transition-colors text-sm"
            >
              GitHub
            </a>
          </div>

          {/* Copyright */}
          <p className="text-[#6e6e73] text-sm">
            © 2026 AgentAuth. All rights reserved.
          </p>
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
