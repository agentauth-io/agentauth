import { useState, useEffect } from "react";
import { motion, AnimatePresence } from "motion/react";
import {
    LayoutDashboard,
    BarChart3,
    Shield,
    Clock,
    Users,
    FileText,
    Key,
    BookOpen,
    CreditCard,
    Settings,
    Zap,
    Plus,
    RefreshCw,
    LogOut,
    Check,
    X,
    Bell,
    Bot,
    Webhook,
    CheckCircle,
} from "lucide-react";
import type { NavSection, DashboardStats, Toast } from "./dashboard/types";
import { NavItem, pageTitles } from "./dashboard/shared";
import {
    DashboardOverview,
    AnalyticsPage,
    TransactionsPage,
    ConsentsPage,
    AgentsPage,
    AuditLogsPage,
    ApiKeysPage,
    WebhooksPage,
    TeamPage,
    BillingPage,
    SettingsPage,
} from "./dashboard";

// Main Dashboard Component
interface DashboardProps {
    checkoutSuccess?: boolean;
    onDismissCheckout?: () => void;
}

export function Dashboard({ checkoutSuccess, onDismissCheckout }: DashboardProps = {}) {
    const [activeNav, setActiveNav] = useState<NavSection>(checkoutSuccess ? "billing" : "dashboard");
    const [stats, setStats] = useState<DashboardStats | null>(null);
    const [isLoading, setIsLoading] = useState(true);
    const [showWelcome, setShowWelcome] = useState(checkoutSuccess || false);
    const [period, setPeriod] = useState("7d");
    const [chartData] = useState([65, 80, 45, 90, 70, 55, 40]);
    const [toast, setToast] = useState<Toast | null>(null);

    // Show toast notification
    const showToast = (message: string, type: "success" | "error" | "info" = "info") => {
        setToast({ message, type });
        setTimeout(() => setToast(null), 3000);
    };

    // Clipboard helper
    const copyToClipboard = (text: string) => {
        navigator.clipboard.writeText(text).then(
            () => showToast("Copied to clipboard!", "success"),
            () => showToast("Failed to copy", "error")
        );
    };

    // Handle export
    const handleExport = (type: string) => {
        showToast(`Exporting ${type}... Download will start shortly.`, "info");
    };

    const fetchData = async () => {
        try {
            setIsLoading(true);
            const apiBase = window.location.hostname === "localhost" ? "http://localhost:8000" : window.location.origin;
            const response = await fetch(`${apiBase}/.netlify/functions/get-stripe-transactions?period=${period}&limit=20`);
            if (response.ok) {
                const data = await response.json();
                setStats(data);
            }
        } catch (error) {
            console.error("Failed to fetch dashboard data:", error);
        } finally {
            setIsLoading(false);
        }
    };

    useEffect(() => {
        fetchData();
    }, [period]);

    const handleLogout = () => {
        localStorage.removeItem("admin_token");
        localStorage.removeItem("admin_expires");
        window.location.href = "/";
    };

    return (
        <div className="flex min-h-screen bg-[#0a0a0a] text-white font-['Inter',sans-serif]">
            {/* Sidebar */}
            <aside className="w-60 bg-[#111] border-r border-[#222] flex flex-col">
                {/* Logo */}
                <div className="flex items-center gap-2.5 px-5 py-5 border-b border-[#222]">
                    <img src="/agentauth-icon-dark.svg" alt="AgentAuth" className="w-7 h-7" />
                    <span className="text-base font-semibold">
                        Agent<span className="text-gray-500">Auth</span>
                    </span>
                </div>

                {/* Navigation */}
                <nav className="flex-1 py-5">
                    <div className="mb-6">
                        <div className="px-5 mb-2 text-[10px] uppercase tracking-wider text-gray-600">
                            Overview
                        </div>
                        <NavItem icon={LayoutDashboard} label="Dashboard" active={activeNav === "dashboard"} onClick={() => setActiveNav("dashboard")} />
                        <NavItem icon={BarChart3} label="Analytics" active={activeNav === "analytics"} onClick={() => setActiveNav("analytics")} />
                    </div>

                    <div className="mb-6">
                        <div className="px-5 mb-2 text-[10px] uppercase tracking-wider text-gray-600">
                            Authorization
                        </div>
                        <NavItem icon={Shield} label="Transactions" active={activeNav === "transactions"} onClick={() => setActiveNav("transactions")} />
                        <NavItem icon={Clock} label="Consents" active={activeNav === "consents"} onClick={() => setActiveNav("consents")} />
                        <NavItem icon={Bot} label="Agents" active={activeNav === "agents"} onClick={() => setActiveNav("agents")} />
                        <NavItem icon={FileText} label="Audit Logs" active={activeNav === "logs"} onClick={() => setActiveNav("logs")} />
                    </div>

                    <div className="mb-6">
                        <div className="px-5 mb-2 text-[10px] uppercase tracking-wider text-gray-600">
                            Developers
                        </div>
                        <NavItem icon={Key} label="API Keys" active={activeNav === "apikeys"} onClick={() => setActiveNav("apikeys")} />
                        <NavItem icon={Webhook} label="Webhooks" active={activeNav === "webhooks"} onClick={() => setActiveNav("webhooks")} />
                        <NavItem icon={BookOpen} label="Documentation" onClick={() => window.location.href = "/docs"} />
                    </div>

                    <div className="mb-6">
                        <div className="px-5 mb-2 text-[10px] uppercase tracking-wider text-gray-600">
                            Settings
                        </div>
                        <NavItem icon={Users} label="Team" active={activeNav === "team"} onClick={() => setActiveNav("team")} />
                        <NavItem icon={CreditCard} label="Billing" active={activeNav === "billing"} onClick={() => setActiveNav("billing")} />
                        <NavItem icon={Settings} label="Settings" active={activeNav === "settings"} onClick={() => setActiveNav("settings")} />
                    </div>
                </nav>

                {/* Plan Badge */}
                <div className="p-5 border-t border-[#222]">
                    <div className="flex items-center gap-2 bg-white/5 p-3 rounded-lg">
                        <Zap className="w-4 h-4 text-emerald-500" />
                        <div>
                            <div className="text-sm font-medium text-emerald-500">Pro Plan</div>
                            <div className="text-xs text-gray-500">
                                {stats?.total_authorizations || 0} / 50,000 MAA
                            </div>
                        </div>
                    </div>
                </div>
            </aside>

            {/* Main Content */}
            <main className="flex-1 overflow-y-auto relative">
                {/* Toast Notification */}
                <AnimatePresence>
                    {toast && (
                        <motion.div
                            initial={{ opacity: 0, y: -20 }}
                            animate={{ opacity: 1, y: 0 }}
                            exit={{ opacity: 0, y: -20 }}
                            className={`fixed top-4 right-4 z-50 px-4 py-3 rounded-lg shadow-lg border text-sm flex items-center gap-2 ${
                                toast.type === "success" ? "bg-emerald-500/10 border-emerald-500/30 text-emerald-400" :
                                toast.type === "error" ? "bg-red-500/10 border-red-500/30 text-red-400" :
                                "bg-cyan-500/10 border-cyan-500/30 text-cyan-400"
                            }`}
                        >
                            {toast.type === "success" ? <Check className="w-4 h-4" /> :
                             toast.type === "error" ? <X className="w-4 h-4" /> :
                             <Bell className="w-4 h-4" />}
                            {toast.message}
                        </motion.div>
                    )}
                </AnimatePresence>

                {/* Checkout Success Welcome Banner */}
                {showWelcome && (
                    <motion.div
                        initial={{ opacity: 0, y: -10 }}
                        animate={{ opacity: 1, y: 0 }}
                        className="mx-8 mt-6 p-4 bg-gradient-to-r from-emerald-500/10 to-cyan-500/10 border border-emerald-500/20 rounded-xl flex items-center justify-between"
                    >
                        <div className="flex items-center gap-3">
                            <div className="w-10 h-10 rounded-full bg-emerald-500/20 flex items-center justify-center">
                                <CheckCircle className="w-5 h-5 text-emerald-400" />
                            </div>
                            <div>
                                <p className="text-white font-medium">Payment Successful! Welcome to AgentAuth</p>
                                <p className="text-gray-400 text-sm">Your subscription is active. Explore your dashboard to get started.</p>
                            </div>
                        </div>
                        <button
                            onClick={() => { setShowWelcome(false); onDismissCheckout?.(); }}
                            className="p-2 hover:bg-white/10 rounded-lg"
                        >
                            <X className="w-4 h-4 text-gray-400" />
                        </button>
                    </motion.div>
                )}

                {/* Header */}
                <header className="flex justify-between items-center px-8 py-5 border-b border-[#222]">
                    <h1 className="text-xl font-semibold">{pageTitles[activeNav]}</h1>
                    <div className="flex gap-3">
                        <button
                            onClick={fetchData}
                            disabled={isLoading}
                            className="flex items-center gap-2 px-4 py-2 bg-white/5 hover:bg-white/10 border border-[#333] rounded-lg text-sm transition-colors"
                        >
                            <RefreshCw className={`w-4 h-4 ${isLoading ? "animate-spin" : ""}`} />
                            Refresh
                        </button>
                        <a
                            href="/docs"
                            className="flex items-center gap-2 px-4 py-2 bg-white/5 hover:bg-white/10 border border-[#333] rounded-lg text-sm transition-colors"
                        >
                            <BookOpen className="w-4 h-4" />
                            Docs
                        </a>
                        <button
                            onClick={() => setActiveNav("apikeys")}
                            className="flex items-center gap-2 px-4 py-2 bg-white hover:bg-gray-200 text-black rounded-lg text-sm font-medium transition-colors"
                        >
                            <Plus className="w-4 h-4" />
                            New API Key
                        </button>
                        <button
                            onClick={handleLogout}
                            className="flex items-center gap-2 px-4 py-2 bg-red-500/10 hover:bg-red-500/20 text-red-500 border border-red-500/20 rounded-lg text-sm transition-colors"
                        >
                            <LogOut className="w-4 h-4" />
                            Logout
                        </button>
                    </div>
                </header>

                {/* Content */}
                <div className="p-8">
                    <AnimatePresence mode="wait">
                        {activeNav === "dashboard" && (
                            <DashboardOverview
                                stats={stats}
                                isLoading={isLoading}
                                chartData={chartData}
                                period={period}
                                onPeriodChange={setPeriod}
                                onNavigate={setActiveNav}
                            />
                        )}
                        {activeNav === "analytics" && <AnalyticsPage />}
                        {activeNav === "transactions" && (
                            <TransactionsPage showToast={showToast} onExport={handleExport} />
                        )}
                        {activeNav === "consents" && <ConsentsPage showToast={showToast} />}
                        {activeNav === "agents" && <AgentsPage showToast={showToast} />}
                        {activeNav === "logs" && <AuditLogsPage onExport={handleExport} />}
                        {activeNav === "apikeys" && (
                            <ApiKeysPage showToast={showToast} copyToClipboard={copyToClipboard} />
                        )}
                        {activeNav === "webhooks" && <WebhooksPage showToast={showToast} />}
                        {activeNav === "team" && <TeamPage showToast={showToast} />}
                        {activeNav === "billing" && (
                            <BillingPage showToast={showToast} onExport={handleExport} />
                        )}
                        {activeNav === "settings" && <SettingsPage showToast={showToast} />}
                    </AnimatePresence>
                </div>
            </main>
        </div>
    );
}
