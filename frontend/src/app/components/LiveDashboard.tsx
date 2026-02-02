import { useState, useEffect, useCallback } from "react";
import { motion, AnimatePresence } from "motion/react";
import {
    LayoutDashboard, Shield, Activity, TrendingUp,
    Check, X, AlertTriangle, Clock, Zap, RefreshCw, Copy, Eye, EyeOff,
    ArrowRight, CheckCircle, XCircle, Bot, FileText,
    Settings, ChevronRight, ExternalLink, BarChart3, Users, 
    Key, Bell, LogOut, Menu, Search, Plus, Sparkles, Globe, Lock
} from "lucide-react";

const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8080";

interface Policy {
    id: string;
    name: string;
    effect: "allow" | "deny";
    priority: number;
    enabled: boolean;
    rules: Record<string, any>;
    constraints: Record<string, any>;
}

interface Stats {
    total: number;
    approved: number;
    denied: number;
    approvalRate: number;
    avgResponseTime: number;
    uptime: number;
}

export function LiveDashboard() {
    const [apiKey, setApiKey] = useState("");
    const [isAuthenticated, setIsAuthenticated] = useState(false);
    const [showKey, setShowKey] = useState(false);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState("");
    const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
    
    const [stats, setStats] = useState<Stats>({ total: 0, approved: 0, denied: 0, approvalRate: 0, avgResponseTime: 15.2, uptime: 99.9 });
    const [policies, setPolicies] = useState<Policy[]>([]);
    const [activeTab, setActiveTab] = useState<"overview" | "policies" | "test" | "logs">("overview");
    
    // Test authorization state
    const [testAction, setTestAction] = useState("purchase");
    const [testAmount, setTestAmount] = useState("25");
    const [testCategory, setTestCategory] = useState("");
    const [testResult, setTestResult] = useState<any>(null);
    const [testing, setTesting] = useState(false);

    const fetchData = useCallback(async () => {
        if (!apiKey) return;
        
        try {
            const policiesRes = await fetch(`${API_URL}/v1/policies`, {
                headers: { "X-API-Key": apiKey }
            });
            if (policiesRes.ok) {
                const policiesData = await policiesRes.json();
                setPolicies(Array.isArray(policiesData) ? policiesData : policiesData.policies || []);
            }

            const metricsRes = await fetch(`${API_URL}/metrics`);
            if (metricsRes.ok) {
                const metricsText = await metricsRes.text();
                const totalMatch = metricsText.match(/agentauth_requests_total\s+(\d+)/);
                const approvedMatch = metricsText.match(/agentauth_approvals_total\s+(\d+)/);
                const deniedMatch = metricsText.match(/agentauth_denials_total\s+(\d+)/);
                const uptimeMatch = metricsText.match(/agentauth_uptime_seconds\s+([\d.]+)/);
                
                const total = parseInt(totalMatch?.[1] || "0");
                const approved = parseInt(approvedMatch?.[1] || "0");
                const denied = parseInt(deniedMatch?.[1] || "0");
                const uptime = parseFloat(uptimeMatch?.[1] || "0");
                
                setStats({
                    total,
                    approved,
                    denied,
                    approvalRate: total > 0 ? (approved / total) * 100 : 0,
                    avgResponseTime: 15.2,
                    uptime: uptime / 60
                });
            }
        } catch (e) {
            console.error("Fetch error:", e);
        }
    }, [apiKey]);

    useEffect(() => {
        if (isAuthenticated) {
            fetchData();
            const interval = setInterval(fetchData, 5000);
            return () => clearInterval(interval);
        }
    }, [isAuthenticated, fetchData]);

    const handleLogin = async () => {
        setLoading(true);
        setError("");
        
        try {
            const res = await fetch(`${API_URL}/v1/policies`, {
                headers: { "X-API-Key": apiKey }
            });
            
            if (res.ok) {
                setIsAuthenticated(true);
                localStorage.setItem("agentauth_key", apiKey);
            } else {
                setError("Invalid API key");
            }
        } catch (e) {
            setError("Connection failed. Is the API running?");
        } finally {
            setLoading(false);
        }
    };

    const handleBootstrap = async () => {
        setLoading(true);
        setError("");
        
        try {
            const res = await fetch(`${API_URL}/v1/bootstrap?bootstrap_secret=a1b2c3d4e5f6789012345678901234567890abcdef1234567890abcdef123456&owner=dashboard`, {
                method: "POST"
            });
            
            if (res.ok) {
                const data = await res.json();
                setApiKey(data.key);
                setIsAuthenticated(true);
                localStorage.setItem("agentauth_key", data.key);
            } else {
                setError("Bootstrap failed");
            }
        } catch (e) {
            setError("Connection failed");
        } finally {
            setLoading(false);
        }
    };

    const handleTest = async () => {
        setTesting(true);
        setTestResult(null);
        
        try {
            const payload: any = {
                agent_id: "dashboard-test",
                user_id: "test-user",
                action: testAction,
            };
            
            if (testAmount && parseFloat(testAmount) > 0) {
                payload.amount = parseFloat(testAmount);
            }
            if (testCategory) {
                payload.category = testCategory;
            }
            
            const res = await fetch(`${API_URL}/v1/authorize`, {
                method: "POST",
                headers: {
                    "X-API-Key": apiKey,
                    "Content-Type": "application/json"
                },
                body: JSON.stringify(payload)
            });
            
            const data = await res.json();
            setTestResult(data);
            fetchData();
        } catch (e) {
            setTestResult({ error: "Request failed" });
        } finally {
            setTesting(false);
        }
    };

    const togglePolicy = async (policyId: string) => {
        try {
            await fetch(`${API_URL}/v1/policies/${policyId}/toggle`, {
                method: "POST",
                headers: { "X-API-Key": apiKey }
            });
            fetchData();
        } catch (e) {
            console.error("Toggle failed:", e);
        }
    };

    useEffect(() => {
        const savedKey = localStorage.getItem("agentauth_key");
        if (savedKey) {
            setApiKey(savedKey);
            fetch(`${API_URL}/v1/policies`, { headers: { "X-API-Key": savedKey } })
                .then(res => {
                    if (res.ok) setIsAuthenticated(true);
                    else localStorage.removeItem("agentauth_key");
                })
                .catch(() => localStorage.removeItem("agentauth_key"));
        }
    }, []);

    // =========================================================================
    // LOGIN SCREEN - Beautiful glassmorphism design
    // =========================================================================
    if (!isAuthenticated) {
        return (
            <div className="min-h-screen bg-[#0f0f13] flex items-center justify-center p-6 relative overflow-hidden">
                {/* Background Effects */}
                <div className="absolute inset-0">
                    <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-emerald-500/20 rounded-full blur-[120px]" />
                    <div className="absolute bottom-1/4 right-1/4 w-96 h-96 bg-violet-500/20 rounded-full blur-[120px]" />
                    <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[600px] bg-cyan-500/10 rounded-full blur-[150px]" />
                </div>
                
                {/* Grid Pattern */}
                <div className="absolute inset-0 bg-[linear-gradient(rgba(255,255,255,0.02)_1px,transparent_1px),linear-gradient(90deg,rgba(255,255,255,0.02)_1px,transparent_1px)] bg-[size:64px_64px]" />

                <motion.div 
                    className="relative w-full max-w-md z-10"
                    initial={{ opacity: 0, y: 20, scale: 0.95 }}
                    animate={{ opacity: 1, y: 0, scale: 1 }}
                    transition={{ duration: 0.5, ease: "easeOut" }}
                >
                    {/* Card */}
                    <div className="backdrop-blur-2xl bg-white/5 border border-white/10 rounded-3xl p-8 shadow-2xl">
                        {/* Logo & Header */}
                        <div className="flex flex-col items-center mb-10">
                            <motion.div 
                                className="w-16 h-16 rounded-2xl bg-gradient-to-br from-emerald-400 via-cyan-400 to-violet-500 flex items-center justify-center mb-4 shadow-lg shadow-emerald-500/25"
                                whileHover={{ scale: 1.05, rotate: 5 }}
                                transition={{ type: "spring", stiffness: 400 }}
                            >
                                <Shield className="w-8 h-8 text-white" />
                            </motion.div>
                            <h1 className="text-2xl font-bold text-white tracking-tight">AgentAuth</h1>
                            <p className="text-white/50 text-sm mt-1">Authorization Control Center</p>
                        </div>

                        {/* Form */}
                        <div className="space-y-5">
                            <div>
                                <label className="block text-sm text-white/60 mb-2 font-medium">API Key</label>
                                <div className="relative group">
                                    <div className="absolute -inset-0.5 bg-gradient-to-r from-emerald-500 to-cyan-500 rounded-xl opacity-0 group-focus-within:opacity-100 blur transition-opacity" />
                                    <div className="relative">
                                        <Key className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-white/30" />
                                        <input
                                            type={showKey ? "text" : "password"}
                                            value={apiKey}
                                            onChange={(e) => setApiKey(e.target.value)}
                                            placeholder="aa_admin_..."
                                            className="w-full pl-11 pr-11 py-3.5 bg-white/5 border border-white/10 rounded-xl text-white placeholder:text-white/30 focus:outline-none focus:bg-white/10 transition-all"
                                        />
                                        <button
                                            onClick={() => setShowKey(!showKey)}
                                            className="absolute right-4 top-1/2 -translate-y-1/2 text-white/30 hover:text-white/60 transition-colors"
                                        >
                                            {showKey ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                                        </button>
                                    </div>
                                </div>
                            </div>

                            {error && (
                                <motion.div 
                                    className="flex items-center gap-2 text-red-400 text-sm bg-red-500/10 border border-red-500/20 rounded-xl px-4 py-3"
                                    initial={{ opacity: 0, y: -10 }}
                                    animate={{ opacity: 1, y: 0 }}
                                >
                                    <AlertTriangle className="w-4 h-4 flex-shrink-0" />
                                    {error}
                                </motion.div>
                            )}

                            <motion.button
                                onClick={handleLogin}
                                disabled={loading || !apiKey}
                                className="w-full py-4 bg-gradient-to-r from-emerald-500 to-cyan-500 hover:from-emerald-400 hover:to-cyan-400 disabled:opacity-50 disabled:cursor-not-allowed rounded-xl text-white font-semibold transition-all flex items-center justify-center gap-2 shadow-lg shadow-emerald-500/25"
                                whileHover={{ scale: 1.01 }}
                                whileTap={{ scale: 0.99 }}
                            >
                                {loading ? (
                                    <RefreshCw className="w-5 h-5 animate-spin" />
                                ) : (
                                    <>
                                        <Lock className="w-4 h-4" />
                                        Connect to Dashboard
                                    </>
                                )}
                            </motion.button>

                            <div className="relative py-4">
                                <div className="absolute inset-0 flex items-center">
                                    <div className="w-full border-t border-white/10" />
                                </div>
                                <div className="relative flex justify-center">
                                    <span className="px-4 bg-[#0f0f13]/80 text-white/40 text-sm">or</span>
                                </div>
                            </div>

                            <motion.button
                                onClick={handleBootstrap}
                                disabled={loading}
                                className="w-full py-4 bg-white/5 hover:bg-white/10 border border-white/10 hover:border-white/20 rounded-xl text-white font-medium transition-all flex items-center justify-center gap-3"
                                whileHover={{ scale: 1.01 }}
                                whileTap={{ scale: 0.99 }}
                            >
                                <Sparkles className="w-5 h-5 text-amber-400" />
                                Generate Development Key
                            </motion.button>

                            <p className="text-xs text-white/30 text-center pt-4">
                                <Globe className="w-3 h-3 inline mr-1" />
                                Connected to {API_URL}
                            </p>
                        </div>
                    </div>

                    {/* Footer Links */}
                    <div className="flex items-center justify-center gap-6 mt-6">
                        <a href="/docs" className="text-white/40 hover:text-white/60 text-sm transition-colors">Documentation</a>
                        <span className="text-white/20">•</span>
                        <a href="http://localhost:3000" target="_blank" className="text-white/40 hover:text-white/60 text-sm transition-colors">Grafana</a>
                        <span className="text-white/20">•</span>
                        <a href="/" className="text-white/40 hover:text-white/60 text-sm transition-colors">Home</a>
                    </div>
                </motion.div>
            </div>
        );
    }

    // =========================================================================
    // MAIN DASHBOARD - Professional layout with sidebar
    // =========================================================================
    return (
        <div className="min-h-screen bg-[#0f0f13] flex">
            {/* Sidebar */}
            <motion.aside
                className={`${sidebarCollapsed ? 'w-20' : 'w-64'} bg-[#16161d] border-r border-white/5 flex flex-col transition-all duration-300 fixed h-full z-40`}
                initial={{ x: -20, opacity: 0 }}
                animate={{ x: 0, opacity: 1 }}
            >
                {/* Logo */}
                <div className="p-5 border-b border-white/5">
                    <div className="flex items-center gap-3">
                        <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-emerald-400 to-cyan-500 flex items-center justify-center flex-shrink-0">
                            <Shield className="w-5 h-5 text-white" />
                        </div>
                        {!sidebarCollapsed && (
                            <div>
                                <h1 className="text-white font-bold">AgentAuth</h1>
                                <p className="text-white/40 text-xs">Control Center</p>
                            </div>
                        )}
                    </div>
                </div>

                {/* Navigation */}
                <nav className="flex-1 p-3 space-y-1">
                    <NavItem icon={LayoutDashboard} label="Overview" active={activeTab === "overview"} collapsed={sidebarCollapsed} onClick={() => setActiveTab("overview")} />
                    <NavItem icon={FileText} label="Policies" active={activeTab === "policies"} collapsed={sidebarCollapsed} onClick={() => setActiveTab("policies")} />
                    <NavItem icon={Zap} label="Test Auth" active={activeTab === "test"} collapsed={sidebarCollapsed} onClick={() => setActiveTab("test")} />
                    <NavItem icon={BarChart3} label="Analytics" collapsed={sidebarCollapsed} onClick={() => window.open('http://localhost:3000', '_blank')} external />
                </nav>

                {/* User Section */}
                <div className="p-4 border-t border-white/5">
                    <button
                        onClick={() => {
                            localStorage.removeItem("agentauth_key");
                            setIsAuthenticated(false);
                            setApiKey("");
                        }}
                        className={`flex items-center gap-3 text-white/50 hover:text-white transition-colors w-full ${sidebarCollapsed ? 'justify-center' : ''}`}
                    >
                        <LogOut className="w-4 h-4" />
                        {!sidebarCollapsed && <span className="text-sm">Logout</span>}
                    </button>
                </div>

                {/* Collapse Toggle */}
                <button
                    onClick={() => setSidebarCollapsed(!sidebarCollapsed)}
                    className="absolute -right-3 top-20 w-6 h-6 bg-[#1e1e28] border border-white/10 rounded-full flex items-center justify-center text-white/50 hover:text-white transition-colors"
                >
                    <ChevronRight className={`w-3 h-3 transition-transform ${sidebarCollapsed ? '' : 'rotate-180'}`} />
                </button>
            </motion.aside>

            {/* Main Content */}
            <main className={`flex-1 ${sidebarCollapsed ? 'ml-20' : 'ml-64'} transition-all duration-300`}>
                {/* Top Bar */}
                <header className="sticky top-0 z-30 backdrop-blur-xl bg-[#0f0f13]/80 border-b border-white/5 px-8 py-4">
                    <div className="flex items-center justify-between">
                        <div className="flex items-center gap-4">
                            <h2 className="text-xl font-semibold text-white capitalize">{activeTab}</h2>
                            <div className="flex items-center gap-2 px-3 py-1.5 bg-emerald-500/10 border border-emerald-500/20 rounded-full">
                                <div className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
                                <span className="text-xs text-emerald-400 font-medium">Live</span>
                            </div>
                        </div>
                        
                        <div className="flex items-center gap-4">
                            <div className="relative">
                                <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-white/30" />
                                <input
                                    type="text"
                                    placeholder="Search..."
                                    className="pl-10 pr-4 py-2 bg-white/5 border border-white/10 rounded-xl text-white text-sm placeholder:text-white/30 focus:outline-none focus:bg-white/10 w-64 transition-all"
                                />
                            </div>
                            <button className="p-2 text-white/50 hover:text-white hover:bg-white/5 rounded-xl transition-colors relative">
                                <Bell className="w-5 h-5" />
                                <span className="absolute top-1.5 right-1.5 w-2 h-2 bg-red-500 rounded-full" />
                            </button>
                            <button
                                onClick={fetchData}
                                className="p-2 text-white/50 hover:text-white hover:bg-white/5 rounded-xl transition-colors"
                            >
                                <RefreshCw className="w-5 h-5" />
                            </button>
                        </div>
                    </div>
                </header>

                {/* Page Content */}
                <div className="p-8">
                    <AnimatePresence mode="wait">
                        {activeTab === "overview" && (
                            <motion.div
                                key="overview"
                                initial={{ opacity: 0, y: 20 }}
                                animate={{ opacity: 1, y: 0 }}
                                exit={{ opacity: 0, y: -20 }}
                                transition={{ duration: 0.3 }}
                                className="space-y-8"
                            >
                                {/* Stats Grid */}
                                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                                    <StatCard
                                        title="Total Requests"
                                        value={stats.total.toLocaleString()}
                                        icon={Activity}
                                        gradient="from-blue-500 to-cyan-500"
                                        change="+12%"
                                        changePositive
                                    />
                                    <StatCard
                                        title="Approved"
                                        value={stats.approved.toLocaleString()}
                                        icon={CheckCircle}
                                        gradient="from-emerald-500 to-green-500"
                                        change={`${((stats.approved / Math.max(stats.total, 1)) * 100).toFixed(0)}%`}
                                        changePositive
                                    />
                                    <StatCard
                                        title="Denied"
                                        value={stats.denied.toLocaleString()}
                                        icon={XCircle}
                                        gradient="from-red-500 to-rose-500"
                                        subtext="Blocked by policies"
                                    />
                                    <StatCard
                                        title="Approval Rate"
                                        value={`${stats.approvalRate.toFixed(1)}%`}
                                        icon={TrendingUp}
                                        gradient="from-violet-500 to-purple-500"
                                        highlight
                                    />
                                </div>

                                {/* Charts Row */}
                                <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                                    {/* Main Chart */}
                                    <div className="lg:col-span-2 bg-[#16161d] border border-white/5 rounded-2xl p-6">
                                        <div className="flex items-center justify-between mb-6">
                                            <h3 className="text-white font-semibold">Authorization Flow</h3>
                                            <div className="flex items-center gap-4 text-sm">
                                                <div className="flex items-center gap-2">
                                                    <div className="w-3 h-3 rounded-full bg-emerald-500" />
                                                    <span className="text-white/50">Approved</span>
                                                </div>
                                                <div className="flex items-center gap-2">
                                                    <div className="w-3 h-3 rounded-full bg-red-500" />
                                                    <span className="text-white/50">Denied</span>
                                                </div>
                                            </div>
                                        </div>
                                        
                                        {/* Simple Bar Visualization */}
                                        <div className="flex items-end justify-around h-48 px-4">
                                            {[65, 78, 90, 85, 70, 95, 88].map((val, i) => (
                                                <motion.div
                                                    key={i}
                                                    className="w-12 bg-gradient-to-t from-emerald-500 to-cyan-400 rounded-t-lg relative"
                                                    initial={{ height: 0 }}
                                                    animate={{ height: `${val}%` }}
                                                    transition={{ delay: i * 0.1, duration: 0.5, ease: "easeOut" }}
                                                >
                                                    <div className="absolute -top-8 left-1/2 -translate-x-1/2 text-white/60 text-xs">
                                                        {val}%
                                                    </div>
                                                </motion.div>
                                            ))}
                                        </div>
                                        <div className="flex justify-around mt-4 text-white/40 text-xs">
                                            <span>Mon</span><span>Tue</span><span>Wed</span><span>Thu</span><span>Fri</span><span>Sat</span><span>Sun</span>
                                        </div>
                                    </div>

                                    {/* Approval Gauge */}
                                    <div className="bg-[#16161d] border border-white/5 rounded-2xl p-6">
                                        <h3 className="text-white font-semibold mb-6">Health Score</h3>
                                        <div className="flex items-center justify-center">
                                            <div className="relative w-40 h-40">
                                                <svg className="w-full h-full -rotate-90">
                                                    <circle
                                                        cx="80"
                                                        cy="80"
                                                        r="70"
                                                        stroke="rgba(255,255,255,0.05)"
                                                        strokeWidth="12"
                                                        fill="none"
                                                    />
                                                    <motion.circle
                                                        cx="80"
                                                        cy="80"
                                                        r="70"
                                                        stroke="url(#gaugeGradient)"
                                                        strokeWidth="12"
                                                        fill="none"
                                                        strokeLinecap="round"
                                                        initial={{ strokeDasharray: "0 440" }}
                                                        animate={{ strokeDasharray: `${(stats.approvalRate / 100) * 440} 440` }}
                                                        transition={{ duration: 1, ease: "easeOut" }}
                                                    />
                                                    <defs>
                                                        <linearGradient id="gaugeGradient" x1="0%" y1="0%" x2="100%" y2="0%">
                                                            <stop offset="0%" stopColor="#10b981" />
                                                            <stop offset="50%" stopColor="#06b6d4" />
                                                            <stop offset="100%" stopColor="#8b5cf6" />
                                                        </linearGradient>
                                                    </defs>
                                                </svg>
                                                <div className="absolute inset-0 flex flex-col items-center justify-center">
                                                    <span className="text-3xl font-bold text-white">{stats.approvalRate.toFixed(0)}%</span>
                                                    <span className="text-white/40 text-xs">Healthy</span>
                                                </div>
                                            </div>
                                        </div>
                                        
                                        <div className="grid grid-cols-2 gap-4 mt-6 pt-6 border-t border-white/5">
                                            <div className="text-center">
                                                <p className="text-xl font-semibold text-white">{policies.length}</p>
                                                <p className="text-white/40 text-xs">Policies</p>
                                            </div>
                                            <div className="text-center">
                                                <p className="text-xl font-semibold text-white">{stats.uptime.toFixed(0)}m</p>
                                                <p className="text-white/40 text-xs">Uptime</p>
                                            </div>
                                        </div>
                                    </div>
                                </div>

                                {/* Quick Actions */}
                                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                                    <QuickAction
                                        icon={Zap}
                                        title="Test Authorization"
                                        description="Run live policy tests"
                                        gradient="from-amber-500 to-orange-500"
                                        onClick={() => setActiveTab("test")}
                                    />
                                    <QuickAction
                                        icon={FileText}
                                        title="Manage Policies"
                                        description="Configure rules and limits"
                                        gradient="from-blue-500 to-indigo-500"
                                        onClick={() => setActiveTab("policies")}
                                    />
                                    <QuickAction
                                        icon={BarChart3}
                                        title="View Analytics"
                                        description="Open Grafana dashboard"
                                        gradient="from-emerald-500 to-teal-500"
                                        onClick={() => window.open('http://localhost:3000', '_blank')}
                                        external
                                    />
                                </div>
                            </motion.div>
                        )}

                        {activeTab === "policies" && (
                            <motion.div
                                key="policies"
                                initial={{ opacity: 0, y: 20 }}
                                animate={{ opacity: 1, y: 0 }}
                                exit={{ opacity: 0, y: -20 }}
                                className="space-y-6"
                            >
                                <div className="flex items-center justify-between">
                                    <div>
                                        <h3 className="text-lg font-semibold text-white">Authorization Policies</h3>
                                        <p className="text-white/40 text-sm mt-1">Configure rules that control AI agent permissions</p>
                                    </div>
                                    <button className="px-4 py-2.5 bg-gradient-to-r from-emerald-500 to-cyan-500 hover:from-emerald-400 hover:to-cyan-400 rounded-xl text-white text-sm font-medium transition-all flex items-center gap-2 shadow-lg shadow-emerald-500/20">
                                        <Plus className="w-4 h-4" />
                                        Add Policy
                                    </button>
                                </div>

                                <div className="grid gap-4">
                                    {policies.map((policy, i) => (
                                        <motion.div
                                            key={policy.id}
                                            initial={{ opacity: 0, x: -20 }}
                                            animate={{ opacity: 1, x: 0 }}
                                            transition={{ delay: i * 0.05 }}
                                            className="bg-[#16161d] border border-white/5 rounded-2xl p-5 hover:border-white/10 transition-all group"
                                        >
                                            <div className="flex items-start justify-between">
                                                <div className="flex items-start gap-4">
                                                    <div className={`w-12 h-12 rounded-xl flex items-center justify-center ${
                                                        policy.effect === "allow" 
                                                            ? "bg-emerald-500/10 text-emerald-400"
                                                            : "bg-red-500/10 text-red-400"
                                                    }`}>
                                                        {policy.effect === "allow" ? <Check className="w-6 h-6" /> : <X className="w-6 h-6" />}
                                                    </div>
                                                    <div>
                                                        <h4 className="text-white font-medium">{policy.name}</h4>
                                                        <p className="text-white/40 text-sm mt-0.5 font-mono">{policy.id}</p>
                                                        
                                                        <div className="flex items-center gap-2 mt-3">
                                                            <span className={`px-2.5 py-1 text-xs font-medium rounded-lg ${
                                                                policy.effect === "allow"
                                                                    ? "bg-emerald-500/10 text-emerald-400"
                                                                    : "bg-red-500/10 text-red-400"
                                                            }`}>
                                                                {policy.effect.toUpperCase()}
                                                            </span>
                                                            <span className="px-2.5 py-1 text-xs bg-white/5 text-white/50 rounded-lg">
                                                                Priority: {policy.priority}
                                                            </span>
                                                        </div>

                                                        {policy.rules?.actions && (
                                                            <div className="flex flex-wrap gap-1.5 mt-3">
                                                                {policy.rules.actions.slice(0, 5).map((action: string) => (
                                                                    <span key={action} className="px-2 py-0.5 text-xs bg-white/5 text-white/60 rounded-md">
                                                                        {action}
                                                                    </span>
                                                                ))}
                                                                {policy.rules.actions.length > 5 && (
                                                                    <span className="px-2 py-0.5 text-xs bg-white/5 text-white/40 rounded-md">
                                                                        +{policy.rules.actions.length - 5} more
                                                                    </span>
                                                                )}
                                                            </div>
                                                        )}
                                                    </div>
                                                </div>

                                                <button
                                                    onClick={() => togglePolicy(policy.id)}
                                                    className={`relative w-14 h-7 rounded-full transition-colors ${
                                                        policy.enabled 
                                                            ? "bg-gradient-to-r from-emerald-500 to-cyan-500" 
                                                            : "bg-white/10"
                                                    }`}
                                                >
                                                    <motion.div
                                                        className="absolute top-1 w-5 h-5 bg-white rounded-full shadow-lg"
                                                        animate={{ left: policy.enabled ? "calc(100% - 24px)" : "4px" }}
                                                        transition={{ type: "spring", stiffness: 500, damping: 30 }}
                                                    />
                                                </button>
                                            </div>
                                        </motion.div>
                                    ))}
                                </div>
                            </motion.div>
                        )}

                        {activeTab === "test" && (
                            <motion.div
                                key="test"
                                initial={{ opacity: 0, y: 20 }}
                                animate={{ opacity: 1, y: 0 }}
                                exit={{ opacity: 0, y: -20 }}
                                className="max-w-2xl space-y-6"
                            >
                                <div>
                                    <h3 className="text-lg font-semibold text-white">Test Authorization</h3>
                                    <p className="text-white/40 text-sm mt-1">Simulate requests to test your policies in real-time</p>
                                </div>

                                <div className="bg-[#16161d] border border-white/5 rounded-2xl p-6 space-y-6">
                                    <div className="grid grid-cols-2 gap-4">
                                        <div>
                                            <label className="block text-sm text-white/60 mb-2 font-medium">Action</label>
                                            <select
                                                value={testAction}
                                                onChange={(e) => setTestAction(e.target.value)}
                                                className="w-full px-4 py-3 bg-white/5 border border-white/10 rounded-xl text-white focus:outline-none focus:bg-white/10 transition-all appearance-none cursor-pointer"
                                            >
                                                <option value="purchase">💳 Purchase</option>
                                                <option value="read">📖 Read</option>
                                                <option value="write">✏️ Write</option>
                                                <option value="transfer">💸 Transfer</option>
                                                <option value="delete">🗑️ Delete</option>
                                                <option value="bet">🎰 Bet</option>
                                            </select>
                                        </div>

                                        <div>
                                            <label className="block text-sm text-white/60 mb-2 font-medium">Amount ($)</label>
                                            <input
                                                type="number"
                                                value={testAmount}
                                                onChange={(e) => setTestAmount(e.target.value)}
                                                placeholder="0"
                                                className="w-full px-4 py-3 bg-white/5 border border-white/10 rounded-xl text-white placeholder:text-white/30 focus:outline-none focus:bg-white/10 transition-all"
                                            />
                                        </div>
                                    </div>

                                    <div>
                                        <label className="block text-sm text-white/60 mb-2 font-medium">Category (optional)</label>
                                        <input
                                            type="text"
                                            value={testCategory}
                                            onChange={(e) => setTestCategory(e.target.value)}
                                            placeholder="gambling, retail, saas..."
                                            className="w-full px-4 py-3 bg-white/5 border border-white/10 rounded-xl text-white placeholder:text-white/30 focus:outline-none focus:bg-white/10 transition-all"
                                        />
                                    </div>

                                    <motion.button
                                        onClick={handleTest}
                                        disabled={testing}
                                        className="w-full py-4 bg-gradient-to-r from-emerald-500 via-cyan-500 to-violet-500 hover:from-emerald-400 hover:via-cyan-400 hover:to-violet-400 disabled:opacity-50 rounded-xl text-white font-semibold transition-all flex items-center justify-center gap-2 shadow-lg"
                                        whileHover={{ scale: 1.01 }}
                                        whileTap={{ scale: 0.99 }}
                                    >
                                        {testing ? (
                                            <RefreshCw className="w-5 h-5 animate-spin" />
                                        ) : (
                                            <>
                                                <Zap className="w-5 h-5" />
                                                Run Authorization Test
                                            </>
                                        )}
                                    </motion.button>

                                    {/* Result */}
                                    <AnimatePresence>
                                        {testResult && (
                                            <motion.div
                                                initial={{ opacity: 0, y: 20, scale: 0.95 }}
                                                animate={{ opacity: 1, y: 0, scale: 1 }}
                                                exit={{ opacity: 0, scale: 0.95 }}
                                                className={`p-6 rounded-2xl border ${
                                                    testResult.authorized
                                                        ? "bg-emerald-500/5 border-emerald-500/20"
                                                        : "bg-red-500/5 border-red-500/20"
                                                }`}
                                            >
                                                <div className="flex items-start gap-4">
                                                    <div className={`w-14 h-14 rounded-2xl flex items-center justify-center ${
                                                        testResult.authorized
                                                            ? "bg-emerald-500/10 text-emerald-400"
                                                            : "bg-red-500/10 text-red-400"
                                                    }`}>
                                                        {testResult.authorized ? (
                                                            <CheckCircle className="w-7 h-7" />
                                                        ) : (
                                                            <XCircle className="w-7 h-7" />
                                                        )}
                                                    </div>
                                                    <div className="flex-1">
                                                        <h4 className={`text-xl font-bold ${
                                                            testResult.authorized ? "text-emerald-400" : "text-red-400"
                                                        }`}>
                                                            {testResult.authorized ? "✓ Authorized" : "✗ Denied"}
                                                        </h4>
                                                        <p className="text-white/60 mt-1">{testResult.reason}</p>
                                                        
                                                        <div className="grid grid-cols-2 gap-4 mt-4 pt-4 border-t border-white/5">
                                                            <div>
                                                                <p className="text-white/40 text-xs">Policy</p>
                                                                <p className="text-white font-mono text-sm">{testResult.policy_id || "N/A"}</p>
                                                            </div>
                                                            <div>
                                                                <p className="text-white/40 text-xs">Response Time</p>
                                                                <p className="text-white text-sm">{testResult.evaluation_time_ms?.toFixed(1) || "N/A"}ms</p>
                                                            </div>
                                                        </div>

                                                        {testResult.token && (
                                                            <div className="mt-4 pt-4 border-t border-white/5">
                                                                <p className="text-white/40 text-xs mb-2">Token</p>
                                                                <div className="flex items-center gap-2">
                                                                    <code className="flex-1 px-3 py-2 bg-black/30 rounded-lg text-xs text-emerald-400 font-mono truncate">
                                                                        {testResult.token}
                                                                    </code>
                                                                    <button
                                                                        onClick={() => navigator.clipboard.writeText(testResult.token)}
                                                                        className="p-2 bg-white/5 hover:bg-white/10 rounded-lg text-white/50 hover:text-white transition-colors"
                                                                    >
                                                                        <Copy className="w-4 h-4" />
                                                                    </button>
                                                                </div>
                                                            </div>
                                                        )}
                                                    </div>
                                                </div>
                                            </motion.div>
                                        )}
                                    </AnimatePresence>

                                    {/* Quick Tests */}
                                    <div className="pt-6 border-t border-white/5">
                                        <p className="text-white/40 text-xs mb-3 font-medium">Quick Tests</p>
                                        <div className="flex flex-wrap gap-2">
                                            {[
                                                { label: "☕ Coffee $5", action: "purchase", amount: "5", category: "" },
                                                { label: "📖 Read Docs", action: "read", amount: "0", category: "" },
                                                { label: "🎰 Casino Bet", action: "bet", amount: "100", category: "gambling" },
                                                { label: "💸 Wire $20k", action: "transfer", amount: "20000", category: "" },
                                            ].map((test) => (
                                                <button
                                                    key={test.label}
                                                    onClick={() => {
                                                        setTestAction(test.action);
                                                        setTestAmount(test.amount);
                                                        setTestCategory(test.category);
                                                        setTimeout(handleTest, 100);
                                                    }}
                                                    className="px-4 py-2 bg-white/5 hover:bg-white/10 border border-white/10 rounded-xl text-sm text-white/70 hover:text-white transition-all"
                                                >
                                                    {test.label}
                                                </button>
                                            ))}
                                        </div>
                                    </div>
                                </div>
                            </motion.div>
                        )}
                    </AnimatePresence>
                </div>
            </main>
        </div>
    );
}

// =========================================================================
// HELPER COMPONENTS
// =========================================================================

function NavItem({ icon: Icon, label, active, collapsed, onClick, external }: {
    icon: React.ElementType;
    label: string;
    active?: boolean;
    collapsed?: boolean;
    onClick?: () => void;
    external?: boolean;
}) {
    return (
        <button
            onClick={onClick}
            className={`w-full flex items-center gap-3 px-4 py-3 rounded-xl transition-all ${
                active
                    ? "bg-gradient-to-r from-emerald-500/10 to-cyan-500/10 text-white border border-emerald-500/20"
                    : "text-white/50 hover:text-white hover:bg-white/5"
            } ${collapsed ? 'justify-center' : ''}`}
        >
            <Icon className="w-5 h-5 flex-shrink-0" />
            {!collapsed && (
                <>
                    <span className="text-sm font-medium flex-1 text-left">{label}</span>
                    {external && <ExternalLink className="w-3 h-3 opacity-50" />}
                </>
            )}
        </button>
    );
}

function StatCard({ title, value, icon: Icon, gradient, change, changePositive, subtext, highlight }: {
    title: string;
    value: string;
    icon: React.ElementType;
    gradient: string;
    change?: string;
    changePositive?: boolean;
    subtext?: string;
    highlight?: boolean;
}) {
    return (
        <motion.div
            className={`relative overflow-hidden rounded-2xl p-6 ${
                highlight 
                    ? "bg-gradient-to-br from-violet-500/10 via-purple-500/5 to-transparent border border-violet-500/20"
                    : "bg-[#16161d] border border-white/5 hover:border-white/10"
            } transition-all`}
            whileHover={{ y: -2 }}
        >
            <div className="flex items-start justify-between">
                <div className={`w-12 h-12 rounded-xl bg-gradient-to-br ${gradient} flex items-center justify-center shadow-lg`}>
                    <Icon className="w-6 h-6 text-white" />
                </div>
                {change && (
                    <span className={`text-xs font-medium px-2 py-1 rounded-lg ${
                        changePositive ? "text-emerald-400 bg-emerald-500/10" : "text-red-400 bg-red-500/10"
                    }`}>
                        {change}
                    </span>
                )}
            </div>
            <div className="mt-4">
                <p className="text-3xl font-bold text-white">{value}</p>
                <p className="text-white/40 text-sm mt-1">{subtext || title}</p>
            </div>
        </motion.div>
    );
}

function QuickAction({ icon: Icon, title, description, gradient, onClick, external }: {
    icon: React.ElementType;
    title: string;
    description: string;
    gradient: string;
    onClick?: () => void;
    external?: boolean;
}) {
    return (
        <motion.button
            onClick={onClick}
            className="relative overflow-hidden bg-[#16161d] border border-white/5 rounded-2xl p-5 text-left hover:border-white/10 transition-all group"
            whileHover={{ y: -2 }}
        >
            <div className={`w-12 h-12 rounded-xl bg-gradient-to-br ${gradient} flex items-center justify-center mb-4 shadow-lg`}>
                <Icon className="w-6 h-6 text-white" />
            </div>
            <h4 className="text-white font-semibold mb-1 flex items-center gap-2">
                {title}
                {external && <ExternalLink className="w-3 h-3 opacity-50" />}
            </h4>
            <p className="text-white/40 text-sm">{description}</p>
            <ArrowRight className="absolute bottom-5 right-5 w-5 h-5 text-white/20 group-hover:text-white/50 group-hover:translate-x-1 transition-all" />
        </motion.button>
    );
}
