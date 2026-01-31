import { useState, useEffect } from "react";
import { BrowserRouter, Routes, Route, useNavigate, useSearchParams } from "react-router-dom";
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
import { DemoStoreEnhanced } from "./components/DemoStoreEnhanced";
import { DeveloperPortal } from "./components/DeveloperPortal";
import { Docs } from "./components/Docs";
import { YCDemo } from "./components/YCDemo";
import { Contact } from "./components/Contact";
import { ResetPasswordPage } from "./components/auth/ResetPasswordPage";
import { SetPasswordPage } from "./components/auth/SetPasswordPage";
import { AuthCallbackPage } from "./components/auth/AuthCallbackPage";
import { supabase, checkBetaAccess } from "../lib/supabase";
import { LandingA } from "./pages/LandingA";
import { LandingB } from "./pages/LandingB";

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

// Process OAuth tokens on page load (skip password recovery - that goes to SetPasswordPage)
const processOAuthOnLoad = () => {
  const hash = window.location.hash;
  const pathname = window.location.pathname;

  // Skip OAuth processing for password recovery links
  // These should be handled by SetPasswordPage, not auto-sign-in
  if (hash.includes("type=recovery") || pathname === "/set-password") {
    return false;
  }

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
  const handlePaymentSuccess = (_p: string) => { setSelectedPlan(null); };

  return (
    <div className="min-h-screen bg-black">
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
  return <DemoStoreEnhanced onBack={() => navigate("/")} />;
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
  // Redirect portal users to the full nucleus dashboard
  useEffect(() => {
    navigate("/nucleus", { replace: true });
  }, [navigate]);
  return (
    <div className="min-h-screen flex items-center justify-center bg-[#0a0a0a]">
      <div className="text-center">
        <div className="w-8 h-8 border-2 border-white border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
        <p className="text-gray-400">Redirecting to Dashboard...</p>
      </div>
    </div>
  );
}

function YCPage() {
  const navigate = useNavigate();
  return <YCDemo onBack={() => navigate("/")} />;
}

function NucleusPage() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [isAdminMode, setIsAdminMode] = useState(false);
  const [user, setUser] = useState<any>(null);
  const [isLoading, setIsLoading] = useState(true);
  const checkoutSuccess = searchParams.get("checkout") === "success";

  useEffect(() => {
    const initAuth = async () => {
      // Check for admin token first (password-based access)
      if (isAdminAuthenticated()) {
        setIsAuthenticated(true);
        setIsAdminMode(true);
        setIsLoading(false);
        return;
      }

      // Check for Supabase user session
      try {
        const { data: { session } } = await supabase.auth.getSession();
        if (session?.user) {
          setUser(session.user);
          setIsAuthenticated(true);
          setIsAdminMode(false);
        }
      } catch (err) {
        console.error("Auth check error:", err);
      }
      setIsLoading(false);
    };

    initAuth();

    // Listen for auth state changes
    const { data: { subscription } } = supabase.auth.onAuthStateChange((_event, session) => {
      if (session?.user) {
        setUser(session.user);
        setIsAuthenticated(true);
        setIsAdminMode(false);
      } else if (!isAdminAuthenticated()) {
        setUser(null);
        setIsAuthenticated(false);
      }
    });

    return () => subscription.unsubscribe();
  }, []);

  const handleAdminAuth = (a: boolean) => {
    setIsAuthenticated(a);
    setIsAdminMode(true);
  };

  const handleLogout = async () => {
    if (isAdminMode) {
      localStorage.removeItem("admin_token");
      localStorage.removeItem("admin_expires");
    } else {
      await supabase.auth.signOut();
    }
    setIsAuthenticated(false);
    setIsAdminMode(false);
    setUser(null);
    navigate("/");
  };

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-[#0A0A0F] via-[#12121A] to-[#0A0A0F]">
        <div className="text-center">
          <div className="w-8 h-8 border-2 border-purple-500 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
          <p className="text-gray-400">Loading...</p>
        </div>
      </div>
    );
  }

  if (isAuthenticated) {
    return <Dashboard user={user} isAdminMode={isAdminMode} onLogout={handleLogout} checkoutSuccess={checkoutSuccess} />;
  }
  return <AdminLogin onAuthenticated={handleAdminAuth} onBack={() => navigate("/")} showUserLogin={true} />;
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
        <Route path="/variant-a" element={<LandingA />} />
        <Route path="/variant-b" element={<LandingB />} />
        <Route path="/demo" element={<DemoPage />} />
        <Route path="/docs" element={<DocsPage />} />
        <Route path="/contact" element={<ContactPage />} />
        <Route path="/portal" element={<PortalPage />} />
        <Route path="/reset-password" element={<ResetPasswordPage />} />
        <Route path="/set-password" element={<SetPasswordPage />} />
        <Route path="/auth/callback" element={<AuthCallbackPage />} />
        <Route path="/yc" element={<YCPage />} />
        <Route path="/nucleus" element={<NucleusPage />} />
        {/* Fallback to home for any unknown routes */}
        <Route path="*" element={<HomePage />} />
      </Routes>
    </BrowserRouter>
  );
}
