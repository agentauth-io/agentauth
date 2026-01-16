import { useState, useEffect } from "react";
import { motion } from "motion/react";
import {
    Shield,
    Lock,
    Eye,
    EyeOff,
    Zap,
    Play,
    ExternalLink,
    Check,
    ArrowRight,
} from "lucide-react";
import { DemoStore } from "./DemoStore";
import { Docs } from "./Docs";

interface YCDemoProps {
    onBack?: () => void;
}

// Secret access code for YC demo
const YC_ACCESS_CODE = "yc2026";

export function YCDemo({ onBack }: YCDemoProps) {
    const [isAuthenticated, setIsAuthenticated] = useState(false);
    const [accessCode, setAccessCode] = useState("");
    const [showPassword, setShowPassword] = useState(false);
    const [error, setError] = useState("");
    const [activeView, setActiveView] = useState<"hub" | "demo" | "docs" | "dashboard">("hub");

    // Check if already authenticated
    useEffect(() => {
        const stored = sessionStorage.getItem("yc_demo_auth");
        if (stored === "true") {
            setIsAuthenticated(true);
        }
    }, []);

    const handleLogin = (e: React.FormEvent) => {
        e.preventDefault();
        if (accessCode === YC_ACCESS_CODE) {
            setIsAuthenticated(true);
            sessionStorage.setItem("yc_demo_auth", "true");
            setError("");
        } else {
            setError("Invalid access code");
        }
    };

    // Login screen
    if (!isAuthenticated) {
        return (
            <div className="min-h-screen bg-gradient-to-br from-[#0A0A0F] via-[#12121A] to-[#0A0A0F] flex items-center justify-center p-6">
                <motion.div
                    className="w-full max-w-md"
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                >
                    <div className="text-center mb-8">
                        <div className="w-16 h-16 mx-auto mb-4 rounded-2xl bg-gradient-to-br from-orange-500 to-red-500 flex items-center justify-center">
                            <span className="text-2xl font-bold text-white">YC</span>
                        </div>
                        <h1 className="text-3xl font-bold text-white mb-2">YC Demo Access</h1>
                        <p className="text-gray-500">Enter access code to view the demo</p>
                    </div>

                    <form onSubmit={handleLogin} className="space-y-4">
                        <div className="relative">
                            <Lock className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-500" />
                            <input
                                type={showPassword ? "text" : "password"}
                                value={accessCode}
                                onChange={(e) => setAccessCode(e.target.value)}
                                placeholder="Access code"
                                className="w-full pl-12 pr-12 py-4 bg-white/5 border border-white/10 rounded-xl text-white placeholder:text-gray-500 focus:outline-none focus:border-orange-500/50"
                                autoFocus
                            />
                            <button
                                type="button"
                                onClick={() => setShowPassword(!showPassword)}
                                className="absolute right-4 top-1/2 -translate-y-1/2 text-gray-500 hover:text-white"
                            >
                                {showPassword ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
                            </button>
                        </div>

                        {error && (
                            <p className="text-red-400 text-sm text-center">{error}</p>
                        )}

                        <button
                            type="submit"
                            className="w-full py-4 bg-gradient-to-r from-orange-500 to-red-500 text-white font-semibold rounded-xl hover:opacity-90 transition-opacity"
                        >
                            Access Demo
                        </button>
                    </form>

                    {onBack && (
                        <button
                            onClick={onBack}
                            className="w-full mt-4 py-3 text-gray-500 hover:text-white transition-colors text-sm"
                        >
                            ← Back to main site
                        </button>
                    )}
                </motion.div>
            </div>
        );
    }

    // Demo Hub
    if (activeView === "hub") {
        return (
            <div className="min-h-screen bg-gradient-to-br from-[#0A0A0F] via-[#12121A] to-[#0A0A0F] p-6">
                <div className="max-w-4xl mx-auto">
                    {/* Header */}
                    <motion.div
                        className="flex items-center justify-between mb-12"
                        initial={{ opacity: 0, y: -20 }}
                        animate={{ opacity: 1, y: 0 }}
                    >
                        <div className="flex items-center gap-4">
                            <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-orange-500 to-red-500 flex items-center justify-center">
                                <span className="text-lg font-bold text-white">YC</span>
                            </div>
                            <div>
                                <h1 className="text-2xl font-bold text-white">AgentAuth Demo Hub</h1>
                                <p className="text-gray-500 text-sm">Private YC Presentation</p>
                            </div>
                        </div>
                        <div className="flex items-center gap-3">
                            <span className="text-green-400 text-sm flex items-center gap-1">
                                <Check className="w-4 h-4" /> Authenticated
                            </span>
                            <button
                                onClick={() => {
                                    sessionStorage.removeItem("yc_demo_auth");
                                    setIsAuthenticated(false);
                                }}
                                className="text-gray-500 hover:text-white text-sm"
                            >
                                Logout
                            </button>
                        </div>
                    </motion.div>

                    {/* Demo Cards */}
                    <motion.div
                        className="grid md:grid-cols-2 gap-6 mb-12"
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        transition={{ delay: 0.1 }}
                    >
                        {/* Interactive Demo */}
                        <motion.div
                            className="p-6 bg-gradient-to-br from-purple-500/10 to-cyan-500/10 border border-purple-500/20 rounded-2xl cursor-pointer hover:border-purple-500/40 transition-colors"
                            whileHover={{ y: -4 }}
                            onClick={() => setActiveView("demo")}
                        >
                            <div className="w-12 h-12 rounded-xl bg-purple-500/20 flex items-center justify-center mb-4">
                                <Play className="w-6 h-6 text-purple-400" />
                            </div>
                            <h3 className="text-xl font-semibold text-white mb-2">Interactive Demo</h3>
                            <p className="text-gray-400 mb-4">
                                Watch AI agents make purchases with real-time authorization. Shows ALLOW/DENY decisions.
                            </p>
                            <span className="text-purple-400 flex items-center gap-1 text-sm">
                                Launch Demo <ArrowRight className="w-4 h-4" />
                            </span>
                        </motion.div>

                        {/* Documentation */}
                        <motion.div
                            className="p-6 bg-gradient-to-br from-cyan-500/10 to-blue-500/10 border border-cyan-500/20 rounded-2xl cursor-pointer hover:border-cyan-500/40 transition-colors"
                            whileHover={{ y: -4 }}
                            onClick={() => setActiveView("docs")}
                        >
                            <div className="w-12 h-12 rounded-xl bg-cyan-500/20 flex items-center justify-center mb-4">
                                <Zap className="w-6 h-6 text-cyan-400" />
                            </div>
                            <h3 className="text-xl font-semibold text-white mb-2">Documentation</h3>
                            <p className="text-gray-400 mb-4">
                                API reference, SDK guides, and integration examples for LangChain & CrewAI.
                            </p>
                            <span className="text-cyan-400 flex items-center gap-1 text-sm">
                                View Docs <ArrowRight className="w-4 h-4" />
                            </span>
                        </motion.div>

                        {/* Dashboard */}
                        <motion.div
                            className="p-6 bg-gradient-to-br from-green-500/10 to-emerald-500/10 border border-green-500/20 rounded-2xl cursor-pointer hover:border-green-500/40 transition-colors"
                            whileHover={{ y: -4 }}
                            onClick={() => window.location.hash = "#nucleus"}
                        >
                            <div className="w-12 h-12 rounded-xl bg-green-500/20 flex items-center justify-center mb-4">
                                <Shield className="w-6 h-6 text-green-400" />
                            </div>
                            <h3 className="text-xl font-semibold text-white mb-2">Admin Dashboard</h3>
                            <p className="text-gray-400 mb-4">
                                Real-time monitoring, spending limits, rules management, and analytics.
                            </p>
                            <span className="text-green-400 flex items-center gap-1 text-sm">
                                Open Dashboard <ArrowRight className="w-4 h-4" />
                            </span>
                        </motion.div>

                        {/* API Status */}
                        <motion.div
                            className="p-6 bg-gradient-to-br from-orange-500/10 to-red-500/10 border border-orange-500/20 rounded-2xl"
                            whileHover={{ y: -4 }}
                        >
                            <div className="w-12 h-12 rounded-xl bg-orange-500/20 flex items-center justify-center mb-4">
                                <ExternalLink className="w-6 h-6 text-orange-400" />
                            </div>
                            <h3 className="text-xl font-semibold text-white mb-2">Quick Links</h3>
                            <div className="space-y-2">
                                <a href="http://localhost:8000/docs" target="_blank" rel="noopener noreferrer" className="text-gray-400 hover:text-white flex items-center gap-2 text-sm">
                                    <ExternalLink className="w-3 h-3" /> API Swagger Docs
                                </a>
                                <a href="https://dashboard.stripe.com/test/payments" target="_blank" rel="noopener noreferrer" className="text-gray-400 hover:text-white flex items-center gap-2 text-sm">
                                    <ExternalLink className="w-3 h-3" /> Stripe Dashboard
                                </a>
                                <a href="https://github.com/Ashok-kumar290/agentauth" target="_blank" rel="noopener noreferrer" className="text-gray-400 hover:text-white flex items-center gap-2 text-sm">
                                    <ExternalLink className="w-3 h-3" /> GitHub Repository
                                </a>
                            </div>
                        </motion.div>
                    </motion.div>

                    {/* Demo Script */}
                    <motion.div
                        className="p-6 bg-white/5 border border-white/10 rounded-2xl"
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        transition={{ delay: 0.2 }}
                    >
                        <h3 className="text-lg font-semibold text-white mb-4">🎬 2-Minute Demo Script</h3>
                        <div className="space-y-3 text-sm">
                            <div className="flex gap-3">
                                <span className="text-orange-400 font-mono w-16 flex-shrink-0">0:00</span>
                                <p className="text-gray-300">"AI agents are starting to spend money. But there's no way for users to control them."</p>
                            </div>
                            <div className="flex gap-3">
                                <span className="text-orange-400 font-mono w-16 flex-shrink-0">0:15</span>
                                <p className="text-gray-300">"Imagine giving your AI a credit card with no limits. It could spend $10K before you notice."</p>
                            </div>
                            <div className="flex gap-3">
                                <span className="text-orange-400 font-mono w-16 flex-shrink-0">0:30</span>
                                <p className="text-gray-300">"AgentAuth is the authorization layer for AI payments." → <strong className="text-white">Launch Interactive Demo</strong></p>
                            </div>
                            <div className="flex gap-3">
                                <span className="text-orange-400 font-mono w-16 flex-shrink-0">0:45</span>
                                <p className="text-gray-300">Set budget to $50. Click Notion ($10) → APPROVED ✓. Click Keyboard ($149) → DENIED ✗</p>
                            </div>
                            <div className="flex gap-3">
                                <span className="text-orange-400 font-mono w-16 flex-shrink-0">1:30</span>
                                <p className="text-gray-300">Show Dashboard with real Stripe transactions and analytics</p>
                            </div>
                            <div className="flex gap-3">
                                <span className="text-orange-400 font-mono w-16 flex-shrink-0">1:45</span>
                                <p className="text-gray-300">"We're looking for 10 beta customers building AI agents that need payment capabilities."</p>
                            </div>
                        </div>
                    </motion.div>
                </div>
            </div>
        );
    }

    // Demo view
    if (activeView === "demo") {
        return <DemoStore onBack={() => setActiveView("hub")} />;
    }

    // Docs view
    if (activeView === "docs") {
        return <Docs onBack={() => setActiveView("hub")} />;
    }

    return null;
}
