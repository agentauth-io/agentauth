import { useState, useEffect } from "react";
import { BrowserRouter, Routes, Route, useNavigate } from "react-router-dom";
import { Hero } from "./components/Hero";
import { Features } from "./components/Features";
import { UseCases } from "./components/UseCases";
import { HowItWorks } from "./components/HowItWorks";
import { Testimonials } from "./components/Testimonials";
import { FAQ } from "./components/FAQ";
import { Pricing } from "./components/Pricing";
import { CheckoutModal } from "./components/CheckoutModal";
import { LaunchSection } from "./components/LaunchSection";
import { Dashboard } from "./components/Dashboard";
import { AdminLogin } from "./components/AdminLogin";
import { DemoStore } from "./components/DemoStore";
import { DeveloperPortal } from "./components/DeveloperPortal";
import { Docs } from "./components/Docs";
import { YCDemo } from "./components/YCDemo";
import { Contact } from "./components/Contact";
import { ResetPasswordPage } from "./components/auth/ResetPasswordPage";
import { SetPasswordPage } from "./components/auth/SetPasswordPage";
import { supabase } from "../lib/supabase";

const PLAN_DETAILS: Record<string, { name: string; price: number }> = {
  community: { name: "Community", price: 0 },
  startup: { name: "Startup", price: 49 },
  pro: { name: "Pro", price: 199 },
  enterprise: { name: "Enterprise", price: 999 },
};

const isAdminAuthenticated = (): boolean => {
  const token = localStorage.getItem("admin_token");
  const expires = localStorage.getItem("admin_expires");
  if (!token || !expires) return false;
  try { return new Date(expires) > new Date(); }
  catch { return false; }
};

// Process OAuth tokens on page load
const processOAuthOnLoad = () => {
  const hash = window.location.hash;
  if (hash.includes("access_token") && !sessionStorage.getItem("oauth_done")) {
    sessionStorage.setItem("oauth_done", "processing");
    const params = new URLSearchParams(hash.substring(1));
    const accessToken = params.get("access_token");
    const refreshToken = params.get("refresh_token");

    if (accessToken) {
      supabase.auth.setSession({
        access_token: accessToken,
        refresh_token: refreshToken || ""
      }).then(({ error }) => {
        if (error) console.error("setSession error:", error);
        sessionStorage.setItem("oauth_done", "true");
        window.history.replaceState(null, "", "/portal");
        window.location.reload();
      }).catch(e => {
        console.error("OAuth processing error:", e);
        sessionStorage.removeItem("oauth_done");
      });
    }
    return true;
  }
  return false;
};

const isProcessingOAuth = processOAuthOnLoad();

// Home page component
function HomePage() {
  const [selectedPlan, setSelectedPlan] = useState<string | null>(null);
  const handleSelectPlan = (planId: string) => setSelectedPlan(planId);
  const handleCloseModal = () => setSelectedPlan(null);
  const handlePaymentSuccess = (p: string) => { console.log(`Payment for ${PLAN_DETAILS[p]?.name}`); setSelectedPlan(null); };

  return (
    <div className="min-h-screen bg-gradient-to-br from-[#0A0A0F] via-[#12121A] to-[#0A0A0F]">
      <Hero />
      <Features />
      <UseCases />
      <HowItWorks />
      <Testimonials />
      <Pricing onSelectPlan={handleSelectPlan} />
      <FAQ />
      <LaunchSection />
      {selectedPlan && (
        <CheckoutModal
          isOpen={true}
          onClose={handleCloseModal}
          planId={selectedPlan}
          planName={PLAN_DETAILS[selectedPlan]?.name || ""}
          price={PLAN_DETAILS[selectedPlan]?.price || 0}
        />
      )}

    </div>
  );
}

// Wrapper components with navigation
function DemoPage() {
  const navigate = useNavigate();
  return <DemoStore onBack={() => navigate("/")} />;
}

function DocsPage() {
  const navigate = useNavigate();
  return <Docs onBack={() => navigate("/")} />;
}

function ContactPage() {
  const navigate = useNavigate();
  return <Contact onBack={() => navigate("/")} />;
}

function PortalPage() {
  const navigate = useNavigate();
  return <DeveloperPortal onClose={() => navigate("/")} />;
}

function YCPage() {
  const navigate = useNavigate();
  return <YCDemo onBack={() => navigate("/")} />;
}

function NucleusPage() {
  const navigate = useNavigate();
  const [isAuthenticated, setIsAuthenticated] = useState(isAdminAuthenticated());

  const handleAdminAuth = (a: boolean) => setIsAuthenticated(a);

  if (isAuthenticated) {
    return <Dashboard />;
  }
  return <AdminLogin onAuthenticated={handleAdminAuth} onBack={() => navigate("/")} />;
}

// Loading component
function LoadingScreen() {
  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-[#0A0A0F] via-[#12121A] to-[#0A0A0F]">
      <div className="text-center">
        <div className="w-8 h-8 border-2 border-purple-500 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
        <p className="text-gray-400">Signing you in...</p>
      </div>
    </div>
  );
}

export default function App() {
  if (isProcessingOAuth) {
    return <LoadingScreen />;
  }

  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<HomePage />} />
        <Route path="/demo" element={<DemoPage />} />
        <Route path="/docs" element={<DocsPage />} />
        <Route path="/contact" element={<ContactPage />} />
        <Route path="/portal" element={<PortalPage />} />
        <Route path="/reset-password" element={<ResetPasswordPage />} />
        <Route path="/set-password" element={<SetPasswordPage />} />
        <Route path="/yc" element={<YCPage />} />
        <Route path="/nucleus" element={<NucleusPage />} />
        {/* Fallback to home for any unknown routes */}
        <Route path="*" element={<HomePage />} />
      </Routes>
    </BrowserRouter>
  );
}
