// Account Page Component

import { motion } from "motion/react";
import { 
    CheckCircle, 
    X, 
    Key, 
    Landmark, 
    BookOpen, 
    Package, 
    Shield, 
    DollarSign, 
    Bot, 
    Lock, 
    Mail 
} from "lucide-react";
import { DashboardStats, formatCurrency } from "./types";

interface AccountPageProps {
    user: { email?: string; user_metadata?: { name?: string } } | null;
    stats: DashboardStats | null;
    isAdminMode: boolean;
    showWelcome: boolean;
    onSetShowWelcome: (show: boolean) => void;
    onNavigate: (nav: string) => void;
}

export function AccountPage({
    user,
    stats,
    isAdminMode,
    showWelcome,
    onSetShowWelcome,
    onNavigate,
}: AccountPageProps) {
    return (
        <motion.div
            key="account"
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            transition={{ duration: 0.2 }}
        >
            {/* Welcome Banner (shown after checkout) */}
            {showWelcome && (
                <div className="bg-gradient-to-r from-green-500/10 to-emerald-500/10 border border-green-500/20 rounded-xl p-6 mb-6">
                    <div className="flex items-start gap-4">
                        <div className="w-12 h-12 bg-green-500/20 rounded-full flex items-center justify-center">
                            <CheckCircle className="w-6 h-6 text-green-400" />
                        </div>
                        <div className="flex-1">
                            <h2 className="text-xl font-semibold text-white mb-1">Welcome to AgentAuth!</h2>
                            <p className="text-gray-400 text-sm">Your subscription is active. Let's get you set up.</p>
                        </div>
                        <button 
                            onClick={() => onSetShowWelcome(false)}
                            className="text-gray-500 hover:text-white"
                        >
                            <X className="w-5 h-5" />
                        </button>
                    </div>
                    <div className="mt-4 grid grid-cols-3 gap-4">
                        <button 
                            onClick={() => onNavigate("apikeys")}
                            className="p-4 bg-white/5 rounded-xl hover:bg-white/10 text-left transition-colors"
                        >
                            <Key className="w-5 h-5 text-zinc-400 mb-2" />
                            <p className="text-white text-sm font-medium">Create API Key</p>
                            <p className="text-gray-500 text-xs">Get started with integration</p>
                        </button>
                        <button 
                            onClick={() => onNavigate("connected-accounts")}
                            className="p-4 bg-white/5 rounded-xl hover:bg-white/10 text-left transition-colors"
                        >
                            <Landmark className="w-5 h-5 text-cyan-400 mb-2" />
                            <p className="text-white text-sm font-medium">Connect Accounts</p>
                            <p className="text-gray-500 text-xs">Link your financial accounts</p>
                        </button>
                        <a 
                            href="/docs"
                            className="p-4 bg-white/5 rounded-xl hover:bg-white/10 text-left transition-colors"
                        >
                            <BookOpen className="w-5 h-5 text-emerald-400 mb-2" />
                            <p className="text-white text-sm font-medium">View Docs</p>
                            <p className="text-gray-500 text-xs">Learn how to use AgentAuth</p>
                        </a>
                    </div>
                </div>
            )}

            {/* Profile Section */}
            <div className="mb-8">
                <h3 className="text-white font-medium mb-4">Profile</h3>
                <div className="bg-[#111] border border-[#222] rounded-xl p-6">
                    <div className="flex items-center gap-4 mb-6">
                        <div className="w-16 h-16 bg-gradient-to-br from-zinc-600 to-zinc-500 rounded-full flex items-center justify-center text-white text-xl font-bold">
                            {user?.email?.charAt(0).toUpperCase() || "U"}
                        </div>
                        <div>
                            <h2 className="text-xl font-semibold text-white">{user?.user_metadata?.name || user?.email?.split("@")[0] || "User"}</h2>
                            <p className="text-gray-500">{user?.email}</p>
                        </div>
                    </div>
                    <div className="grid grid-cols-2 gap-4">
                        <div>
                            <label className="block text-sm text-gray-400 mb-2">Email</label>
                            <input 
                                type="email" 
                                value={user?.email || ""} 
                                disabled 
                                className="w-full bg-white/5 border border-[#333] rounded-lg px-4 py-2.5 text-gray-400"
                            />
                        </div>
                        <div>
                            <label className="block text-sm text-gray-400 mb-2">Account Type</label>
                            <input 
                                type="text" 
                                value={isAdminMode ? "Administrator" : "Developer"} 
                                disabled 
                                className="w-full bg-white/5 border border-[#333] rounded-lg px-4 py-2.5 text-gray-400"
                            />
                        </div>
                    </div>
                </div>
            </div>

            {/* Subscription Info */}
            <div className="mb-8">
                <h3 className="text-white font-medium mb-4">Subscription</h3>
                <div className="bg-gradient-to-r from-zinc-800/50 to-zinc-700/50 border border-zinc-700 rounded-xl p-6">
                    <div className="flex items-center justify-between">
                        <div className="flex items-center gap-4">
                            <div className="w-12 h-12 bg-zinc-800 rounded-xl flex items-center justify-center">
                                <Package className="w-6 h-6 text-zinc-400" />
                            </div>
                            <div>
                                <div className="flex items-center gap-2">
                                    <span className="text-white font-semibold text-lg">Pro Plan</span>
                                    <span className="px-2 py-0.5 bg-emerald-500/20 text-emerald-500 text-xs rounded">Active</span>
                                </div>
                                <p className="text-gray-500 text-sm">50,000 MAA • Unlimited API calls • Priority support</p>
                            </div>
                        </div>
                        <div className="text-right">
                            <div className="text-2xl font-bold text-white">$199</div>
                            <div className="text-gray-500 text-sm">/month</div>
                        </div>
                    </div>
                    <div className="mt-4 pt-4 border-t border-white/10 flex items-center justify-between">
                        <span className="text-gray-500 text-sm">Next billing: February 1, 2026</span>
                        <button 
                            onClick={() => onNavigate("billing")}
                            className="text-zinc-400 text-sm hover:underline"
                        >
                            Manage Subscription →
                        </button>
                    </div>
                </div>
            </div>

            {/* Quick Stats */}
            <div className="mb-8">
                <h3 className="text-white font-medium mb-4">This Month's Usage</h3>
                <div className="grid grid-cols-3 gap-4">
                    <div className="bg-[#111] border border-[#222] rounded-xl p-5">
                        <div className="flex items-center gap-2 text-gray-500 mb-2">
                            <Shield className="w-4 h-4" />
                            <span className="text-xs">Authorizations</span>
                        </div>
                        <div className="text-2xl font-semibold text-white">{stats?.total_authorizations?.toLocaleString() || "0"}</div>
                        <div className="text-xs text-emerald-500 mt-1">↑ 12% from last month</div>
                    </div>
                    <div className="bg-[#111] border border-[#222] rounded-xl p-5">
                        <div className="flex items-center gap-2 text-gray-500 mb-2">
                            <DollarSign className="w-4 h-4" />
                            <span className="text-xs">Transaction Volume</span>
                        </div>
                        <div className="text-2xl font-semibold text-white">{formatCurrency(stats?.transaction_volume || 0)}</div>
                        <div className="text-xs text-emerald-500 mt-1">↑ 8% from last month</div>
                    </div>
                    <div className="bg-[#111] border border-[#222] rounded-xl p-5">
                        <div className="flex items-center gap-2 text-gray-500 mb-2">
                            <Bot className="w-4 h-4" />
                            <span className="text-xs">Active Agents</span>
                        </div>
                        <div className="text-2xl font-semibold text-white">6</div>
                        <div className="text-xs text-gray-500 mt-1">No change</div>
                    </div>
                </div>
            </div>

            {/* Security */}
            <div>
                <h3 className="text-white font-medium mb-4">Security</h3>
                <div className="bg-[#111] border border-[#222] rounded-xl divide-y divide-[#222]">
                    <div className="p-4 flex items-center justify-between">
                        <div className="flex items-center gap-3">
                            <Lock className="w-5 h-5 text-gray-500" />
                            <div>
                                <p className="text-white text-sm">Password</p>
                                <p className="text-gray-500 text-xs">Last changed: Never</p>
                            </div>
                        </div>
                        <a href="/reset-password" className="px-4 py-2 bg-white/5 hover:bg-white/10 border border-[#333] rounded-lg text-sm">
                            Change Password
                        </a>
                    </div>
                    <div className="p-4 flex items-center justify-between">
                        <div className="flex items-center gap-3">
                            <Mail className="w-5 h-5 text-gray-500" />
                            <div>
                                <p className="text-white text-sm">Two-Factor Authentication</p>
                                <p className="text-gray-500 text-xs">Add an extra layer of security</p>
                            </div>
                        </div>
                        <button className="px-4 py-2 bg-white/5 hover:bg-white/10 border border-[#333] rounded-lg text-sm">
                            Enable 2FA
                        </button>
                    </div>
                </div>
            </div>
        </motion.div>
    );
}

export default AccountPage;
