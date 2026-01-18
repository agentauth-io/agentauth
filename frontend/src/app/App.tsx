import { useState, useEffect } from "react";
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
import { supabase } from "../lib/supabase";

const PLAN_DETAILS: Record<string, { name: string; price: number }> = {
  free: { name: "Free", price: 0 },
  pro: { name: "Pro", price: 49 },
  enterprise: { name: "Enterprise", price: 199 },
};

const isAdminAuthenticated = (): boolean => {
  const token = localStorage.getItem("admin_token");
  const expires = localStorage.getItem("admin_expires");
  if (!token || !expires) return false;
  try { return new Date(expires) > new Date(); }
  catch { return false; }
};

// Process OAuth tokens ONCE on initial page load (before React renders)
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
        window.history.replaceState(null, "", "/#portal");
        window.location.reload(); // Force reload to pick up new session
      }).catch(e => {
        console.error("OAuth processing error:", e);
        sessionStorage.removeItem("oauth_done");
      });
    }
    return true; // Still processing
  }
  return false;
};

// Run once on module load
const isProcessingOAuth = processOAuthOnLoad();

export default function App() {
  const [selectedPlan, setSelectedPlan] = useState<string | null>(null);
  const [currentPage, setCurrentPage] = useState<"home" | "nucleus" | "demo" | "portal" | "docs" | "yc" | "contact">("home");
  const [isAuthenticated, setIsAuthenticated] = useState(false);

  useEffect(() => {
    // Clear the oauth flag on normal page loads
    if (!window.location.hash.includes("access_token")) {
      sessionStorage.removeItem("oauth_done");
    }

    const handleHashChange = () => {
      const hash = window.location.hash;
      if (hash.startsWith("#portal")) {
        setCurrentPage("portal");
      } else if (hash === "#nucleus") {
        setCurrentPage("nucleus");
        setIsAuthenticated(isAdminAuthenticated());
      } else if (hash === "#demo") {
        setCurrentPage("demo");
      } else if (hash === "#docs") {
        setCurrentPage("docs");
      } else if (hash === "#yc") {
        setCurrentPage("yc");
      } else if (hash === "#contact") {
        setCurrentPage("contact");
      } else {
        setCurrentPage("home");
      }
    };

    handleHashChange();
    window.addEventListener("hashchange", handleHashChange);
    return () => window.removeEventListener("hashchange", handleHashChange);
  }, []);

  const handleSelectPlan = (planId: string) => setSelectedPlan(planId);
  const handleCloseModal = () => setSelectedPlan(null);
  const handlePaymentSuccess = (p: string) => { console.log(`Payment for ${PLAN_DETAILS[p]?.name}`); setSelectedPlan(null); };
  const handleAdminAuth = (a: boolean) => setIsAuthenticated(a);

  // Show loading while processing OAuth
  if (isProcessingOAuth) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-[#0A0A0F] via-[#12121A] to-[#0A0A0F]">
        <div className="text-center">
          <div className="w-8 h-8 border-2 border-purple-500 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
          <p className="text-gray-400">Signing you in...</p>
        </div>
      </div>
    );
  }

  if (currentPage === "nucleus") {
    if (isAuthenticated) {
      return <Dashboard onLogout={() => { localStorage.removeItem("admin_token"); localStorage.removeItem("admin_expires"); setIsAuthenticated(false); history.replaceState(null, "", "/"); }} />;
    }
    return <AdminLogin onAuthenticated={handleAdminAuth} onBack={() => { history.replaceState(null, "", "/"); setCurrentPage("home"); }} />;
  }

  if (currentPage === "portal") {
    return <DeveloperPortal onClose={() => { history.replaceState(null, "", "/"); setCurrentPage("home"); }} />;
  }

  if (currentPage === "demo") {
    return <DemoStore onBack={() => { history.replaceState(null, "", "/"); setCurrentPage("home"); }} />;
  }

  if (currentPage === "docs") {
    return <Docs onBack={() => { history.replaceState(null, "", "/"); setCurrentPage("home"); }} />;
  }

  if (currentPage === "yc") {
    return <YCDemo onBack={() => { history.replaceState(null, "", "/"); setCurrentPage("home"); }} />;
  }

  if (currentPage === "contact") {
    return <Contact onBack={() => { history.replaceState(null, "", "/"); setCurrentPage("home"); }} />;
  }

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
        <CheckoutModal isOpen={true} onClose={handleCloseModal} planId={selectedPlan} planName={PLAN_DETAILS[selectedPlan]?.name || ""} planPrice={PLAN_DETAILS[selectedPlan]?.price || 0} onPaymentSuccess={handlePaymentSuccess} />
      )}
    </div>
  );
}
