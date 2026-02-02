"use client";

import { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import Link from "next/link";

// Password must be set via NEXT_PUBLIC_ADMIN_PASSWORD environment variable
const ADMIN_PASSWORD = process.env.NEXT_PUBLIC_ADMIN_PASSWORD || "";

if (!ADMIN_PASSWORD) {
    console.warn("NEXT_PUBLIC_ADMIN_PASSWORD not set - admin login will fail");
}

interface Transaction {
  id: string;
  agent_id: string;
  merchant: string;
  amount: number;
  decision: "ALLOW" | "DENY";
  timestamp: Date;
  latency_ms: number;
}

interface Agent {
  id: string;
  name: string;
  status: "active" | "inactive" | "suspended";
  daily_limit: number;
  daily_spent: number;
  transactions_today: number;
}

export default function NucleusPage() {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const [activeTab, setActiveTab] = useState<"overview" | "agents" | "transactions" | "policies" | "settings">("overview");
  
  // Demo data
  const [transactions] = useState<Transaction[]>([
    { id: "txn_001", agent_id: "agent_shopping_7x8k2m", merchant: "Amazon", amount: 149.99, decision: "ALLOW", timestamp: new Date(), latency_ms: 34 },
    { id: "txn_002", agent_id: "agent_travel_3y9n4p", merchant: "United Airlines", amount: 450.00, decision: "ALLOW", timestamp: new Date(Date.now() - 3600000), latency_ms: 28 },
    { id: "txn_003", agent_id: "agent_shopping_7x8k2m", merchant: "Suspicious Store", amount: 999.99, decision: "DENY", timestamp: new Date(Date.now() - 7200000), latency_ms: 12 },
    { id: "txn_004", agent_id: "agent_food_1z5m8q", merchant: "DoorDash", amount: 45.50, decision: "ALLOW", timestamp: new Date(Date.now() - 10800000), latency_ms: 41 },
    { id: "txn_005", agent_id: "agent_shopping_7x8k2m", merchant: "Best Buy", amount: 299.99, decision: "ALLOW", timestamp: new Date(Date.now() - 14400000), latency_ms: 22 },
  ]);

  const [agents] = useState<Agent[]>([
    { id: "agent_shopping_7x8k2m", name: "Shopping Assistant", status: "active", daily_limit: 500, daily_spent: 449.98, transactions_today: 3 },
    { id: "agent_travel_3y9n4p", name: "Travel Booker", status: "active", daily_limit: 2000, daily_spent: 450.00, transactions_today: 1 },
    { id: "agent_food_1z5m8q", name: "Food Orderer", status: "active", daily_limit: 100, daily_spent: 45.50, transactions_today: 1 },
    { id: "agent_finance_9k2l7w", name: "Finance Manager", status: "suspended", daily_limit: 5000, daily_spent: 0, transactions_today: 0 },
  ]);

  useEffect(() => {
    const token = localStorage.getItem("nucleus_token");
    const expires = localStorage.getItem("nucleus_expires");
    if (token && expires) {
      if (new Date(expires) > new Date()) {
        setIsAuthenticated(true);
      } else {
        localStorage.removeItem("nucleus_token");
        localStorage.removeItem("nucleus_expires");
      }
    }
  }, []);

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setIsLoading(true);

    await new Promise(resolve => setTimeout(resolve, 500));

    if (password === ADMIN_PASSWORD) {
      const expiresAt = new Date();
      expiresAt.setHours(expiresAt.getHours() + 1);
      
      const token = `nucleus.${btoa(JSON.stringify({ exp: expiresAt.getTime() }))}.token`;
      localStorage.setItem("nucleus_token", token);
      localStorage.setItem("nucleus_expires", expiresAt.toISOString());
      setIsAuthenticated(true);
    } else {
      setError("Invalid password");
    }
    setIsLoading(false);
  };

  const handleLogout = () => {
    localStorage.removeItem("nucleus_token");
    localStorage.removeItem("nucleus_expires");
    setIsAuthenticated(false);
    setPassword("");
  };

  // Stats
  const totalTransactions = transactions.length;
  const approvedCount = transactions.filter(t => t.decision === "ALLOW").length;
  const deniedCount = transactions.filter(t => t.decision === "DENY").length;
  const avgLatency = Math.round(transactions.reduce((a, t) => a + t.latency_ms, 0) / transactions.length);
  const activeAgents = agents.filter(a => a.status === "active").length;

  if (!isAuthenticated) {
    return (
      <div className="min-h-screen bg-black flex items-center justify-center p-4">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="w-full max-w-md"
        >
          <div className="bg-zinc-900 border border-zinc-800 rounded-2xl p-8">
            <div className="text-center mb-8">
              <div className="w-16 h-16 bg-gradient-to-br from-emerald-500 to-emerald-600 rounded-2xl flex items-center justify-center mx-auto mb-4">
                <svg className="w-8 h-8 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
                </svg>
              </div>
              <h1 className="text-2xl font-bold text-white mb-2">Nucleus Admin</h1>
              <p className="text-zinc-400 text-sm">Enter your admin password to continue</p>
            </div>

            <form onSubmit={handleLogin} className="space-y-4">
              <div>
                <label className="block text-sm text-zinc-400 mb-2">Password</label>
                <div className="relative">
                  <input
                    type={showPassword ? "text" : "password"}
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    placeholder="Enter admin password"
                    className="w-full px-4 py-3 bg-zinc-800 border border-zinc-700 rounded-xl text-white placeholder-zinc-500 focus:outline-none focus:border-emerald-500 transition-colors"
                    autoFocus
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword(!showPassword)}
                    className="absolute right-3 top-1/2 -translate-y-1/2 text-zinc-500 hover:text-zinc-300"
                  >
                    {showPassword ? (
                      <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13.875 18.825A10.05 10.05 0 0112 19c-4.478 0-8.268-2.943-9.543-7a9.97 9.97 0 011.563-3.029m5.858.908a3 3 0 114.243 4.243M9.878 9.878l4.242 4.242M9.88 9.88l-3.29-3.29m7.532 7.532l3.29 3.29M3 3l3.59 3.59m0 0A9.953 9.953 0 0112 5c4.478 0 8.268 2.943 9.543 7a10.025 10.025 0 01-4.132 5.411m0 0L21 21" />
                      </svg>
                    ) : (
                      <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                      </svg>
                    )}
                  </button>
                </div>
              </div>

              {error && (
                <motion.div
                  initial={{ opacity: 0, y: -10 }}
                  animate={{ opacity: 1, y: 0 }}
                  className="flex items-center gap-2 text-red-400 text-sm bg-red-500/10 p-3 rounded-lg"
                >
                  <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                  {error}
                </motion.div>
              )}

              <button
                type="submit"
                disabled={isLoading || !password}
                className="w-full py-3 bg-emerald-600 hover:bg-emerald-500 disabled:bg-zinc-700 disabled:cursor-not-allowed text-white font-medium rounded-xl transition-colors flex items-center justify-center gap-2"
              >
                {isLoading ? (
                  <>
                    <svg className="w-5 h-5 animate-spin" fill="none" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                    </svg>
                    Authenticating...
                  </>
                ) : (
                  <>
                    <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 16l-4-4m0 0l4-4m-4 4h14m-5 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h7a3 3 0 013 3v1" />
                    </svg>
                    Sign In
                  </>
                )}
              </button>
            </form>

            <div className="mt-6 text-center">
              <Link href="/" className="text-zinc-500 hover:text-zinc-300 text-sm transition-colors">
                Back to home
              </Link>
            </div>
          </div>
        </motion.div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-black">
      {/* Header */}
      <header className="border-b border-zinc-800 bg-zinc-900/50 backdrop-blur-sm sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <div className="flex items-center gap-4">
              <div className="w-8 h-8 bg-gradient-to-br from-emerald-500 to-emerald-600 rounded-lg flex items-center justify-center">
                <span className="text-white font-bold text-sm">A</span>
              </div>
              <span className="text-white font-semibold">Nucleus</span>
              <span className="px-2 py-0.5 bg-emerald-500/20 text-emerald-400 text-xs rounded-full">Admin</span>
            </div>
            <button
              onClick={handleLogout}
              className="px-4 py-2 text-zinc-400 hover:text-white text-sm transition-colors"
            >
              Sign Out
            </button>
          </div>
        </div>
      </header>

      {/* Navigation */}
      <nav className="border-b border-zinc-800 bg-zinc-900/30">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex gap-1">
            {(["overview", "agents", "transactions", "policies", "settings"] as const).map((tab) => (
              <button
                key={tab}
                onClick={() => setActiveTab(tab)}
                className={`px-4 py-3 text-sm font-medium capitalize transition-colors border-b-2 -mb-px ${
                  activeTab === tab
                    ? "text-emerald-400 border-emerald-400"
                    : "text-zinc-500 border-transparent hover:text-zinc-300"
                }`}
              >
                {tab}
              </button>
            ))}
          </div>
        </div>
      </nav>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <AnimatePresence mode="wait">
          {activeTab === "overview" && (
            <motion.div
              key="overview"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              className="space-y-6"
            >
              {/* Stats Grid */}
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-6">
                  <div className="text-zinc-400 text-sm mb-2">Total Transactions</div>
                  <div className="text-3xl font-bold text-white">{totalTransactions}</div>
                </div>
                <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-6">
                  <div className="text-zinc-400 text-sm mb-2">Approval Rate</div>
                  <div className="text-3xl font-bold text-emerald-400">{Math.round((approvedCount / totalTransactions) * 100)}%</div>
                </div>
                <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-6">
                  <div className="text-zinc-400 text-sm mb-2">Avg Latency</div>
                  <div className="text-3xl font-bold text-white">{avgLatency}ms</div>
                </div>
                <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-6">
                  <div className="text-zinc-400 text-sm mb-2">Active Agents</div>
                  <div className="text-3xl font-bold text-white">{activeAgents}</div>
                </div>
              </div>

              {/* Recent Transactions */}
              <div className="bg-zinc-900 border border-zinc-800 rounded-xl">
                <div className="p-4 border-b border-zinc-800">
                  <h2 className="text-lg font-semibold text-white">Recent Transactions</h2>
                </div>
                <div className="divide-y divide-zinc-800">
                  {transactions.slice(0, 5).map((txn) => (
                    <div key={txn.id} className="p-4 flex items-center justify-between">
                      <div className="flex items-center gap-4">
                        <div className={`w-2 h-2 rounded-full ${txn.decision === "ALLOW" ? "bg-emerald-400" : "bg-red-400"}`} />
                        <div>
                          <div className="text-white font-medium">{txn.merchant}</div>
                          <div className="text-zinc-500 text-sm">{txn.agent_id}</div>
                        </div>
                      </div>
                      <div className="text-right">
                        <div className="text-white font-medium">${txn.amount.toFixed(2)}</div>
                        <div className="text-zinc-500 text-sm">{txn.latency_ms}ms</div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </motion.div>
          )}

          {activeTab === "agents" && (
            <motion.div
              key="agents"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
            >
              <div className="bg-zinc-900 border border-zinc-800 rounded-xl">
                <div className="p-4 border-b border-zinc-800 flex items-center justify-between">
                  <h2 className="text-lg font-semibold text-white">Registered Agents</h2>
                  <button className="px-4 py-2 bg-emerald-600 hover:bg-emerald-500 text-white text-sm font-medium rounded-lg transition-colors">
                    Add Agent
                  </button>
                </div>
                <div className="divide-y divide-zinc-800">
                  {agents.map((agent) => (
                    <div key={agent.id} className="p-4 flex items-center justify-between">
                      <div className="flex items-center gap-4">
                        <div className={`w-10 h-10 rounded-lg flex items-center justify-center ${
                          agent.status === "active" ? "bg-emerald-500/20" : agent.status === "suspended" ? "bg-red-500/20" : "bg-zinc-700"
                        }`}>
                          <span className={`text-lg ${
                            agent.status === "active" ? "text-emerald-400" : agent.status === "suspended" ? "text-red-400" : "text-zinc-400"
                          }`}>
                            {agent.name[0]}
                          </span>
                        </div>
                        <div>
                          <div className="text-white font-medium">{agent.name}</div>
                          <div className="text-zinc-500 text-sm">{agent.id}</div>
                        </div>
                      </div>
                      <div className="flex items-center gap-6">
                        <div className="text-right">
                          <div className="text-white">${agent.daily_spent.toFixed(2)} / ${agent.daily_limit}</div>
                          <div className="text-zinc-500 text-sm">{agent.transactions_today} txns today</div>
                        </div>
                        <span className={`px-2 py-1 text-xs font-medium rounded-full ${
                          agent.status === "active" 
                            ? "bg-emerald-500/20 text-emerald-400" 
                            : agent.status === "suspended"
                            ? "bg-red-500/20 text-red-400"
                            : "bg-zinc-700 text-zinc-400"
                        }`}>
                          {agent.status}
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </motion.div>
          )}

          {activeTab === "transactions" && (
            <motion.div
              key="transactions"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
            >
              <div className="bg-zinc-900 border border-zinc-800 rounded-xl">
                <div className="p-4 border-b border-zinc-800">
                  <h2 className="text-lg font-semibold text-white">All Transactions</h2>
                </div>
                <div className="overflow-x-auto">
                  <table className="w-full">
                    <thead>
                      <tr className="text-left text-zinc-500 text-sm border-b border-zinc-800">
                        <th className="p-4">ID</th>
                        <th className="p-4">Agent</th>
                        <th className="p-4">Merchant</th>
                        <th className="p-4">Amount</th>
                        <th className="p-4">Decision</th>
                        <th className="p-4">Latency</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-zinc-800">
                      {transactions.map((txn) => (
                        <tr key={txn.id} className="hover:bg-zinc-800/50 transition-colors">
                          <td className="p-4 text-zinc-400 font-mono text-sm">{txn.id}</td>
                          <td className="p-4 text-white">{txn.agent_id}</td>
                          <td className="p-4 text-white">{txn.merchant}</td>
                          <td className="p-4 text-white">${txn.amount.toFixed(2)}</td>
                          <td className="p-4">
                            <span className={`px-2 py-1 text-xs font-medium rounded-full ${
                              txn.decision === "ALLOW" 
                                ? "bg-emerald-500/20 text-emerald-400" 
                                : "bg-red-500/20 text-red-400"
                            }`}>
                              {txn.decision}
                            </span>
                          </td>
                          <td className="p-4 text-zinc-400">{txn.latency_ms}ms</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            </motion.div>
          )}

          {activeTab === "policies" && (
            <motion.div
              key="policies"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              className="space-y-4"
            >
              <div className="flex items-center justify-between">
                <h2 className="text-lg font-semibold text-white">Authorization Policies</h2>
                <button className="px-4 py-2 bg-emerald-600 hover:bg-emerald-500 text-white text-sm font-medium rounded-lg transition-colors">
                  Create Policy
                </button>
              </div>
              
              <div className="grid gap-4">
                {[
                  { name: "Default Spending Limit", description: "Maximum $500 per day per agent", status: "active" },
                  { name: "Merchant Blocklist", description: "Block transactions to suspicious merchants", status: "active" },
                  { name: "High Value Approval", description: "Require approval for transactions > $300", status: "active" },
                  { name: "Time-based Restrictions", description: "Block transactions outside business hours", status: "inactive" },
                ].map((policy, i) => (
                  <div key={i} className="bg-zinc-900 border border-zinc-800 rounded-xl p-4 flex items-center justify-between">
                    <div>
                      <div className="text-white font-medium">{policy.name}</div>
                      <div className="text-zinc-500 text-sm">{policy.description}</div>
                    </div>
                    <div className="flex items-center gap-4">
                      <span className={`px-2 py-1 text-xs font-medium rounded-full ${
                        policy.status === "active" 
                          ? "bg-emerald-500/20 text-emerald-400" 
                          : "bg-zinc-700 text-zinc-400"
                      }`}>
                        {policy.status}
                      </span>
                      <button className="text-zinc-400 hover:text-white transition-colors">
                        <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 5v.01M12 12v.01M12 19v.01M12 6a1 1 0 110-2 1 1 0 010 2zm0 7a1 1 0 110-2 1 1 0 010 2zm0 7a1 1 0 110-2 1 1 0 010 2z" />
                        </svg>
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            </motion.div>
          )}

          {activeTab === "settings" && (
            <motion.div
              key="settings"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              className="space-y-6"
            >
              <div className="bg-zinc-900 border border-zinc-800 rounded-xl">
                <div className="p-4 border-b border-zinc-800">
                  <h2 className="text-lg font-semibold text-white">Account Settings</h2>
                </div>
                <div className="p-6 space-y-6">
                  <div>
                    <label className="block text-sm text-zinc-400 mb-2">Organization Name</label>
                    <input
                      type="text"
                      defaultValue="AgentAuth"
                      className="w-full max-w-md px-4 py-2 bg-zinc-800 border border-zinc-700 rounded-lg text-white focus:outline-none focus:border-emerald-500"
                    />
                  </div>
                  <div>
                    <label className="block text-sm text-zinc-400 mb-2">API Key</label>
                    <div className="flex items-center gap-2 max-w-md">
                      <input
                        type="password"
                        defaultValue="sk_live_xxxxxxxxxxxxxxxxxxxxxx"
                        className="flex-1 px-4 py-2 bg-zinc-800 border border-zinc-700 rounded-lg text-white font-mono text-sm focus:outline-none focus:border-emerald-500"
                        readOnly
                      />
                      <button className="px-4 py-2 bg-zinc-800 hover:bg-zinc-700 border border-zinc-700 text-white text-sm rounded-lg transition-colors">
                        Regenerate
                      </button>
                    </div>
                  </div>
                  <div>
                    <label className="block text-sm text-zinc-400 mb-2">Webhook URL</label>
                    <input
                      type="url"
                      placeholder="https://your-server.com/webhook"
                      className="w-full max-w-md px-4 py-2 bg-zinc-800 border border-zinc-700 rounded-lg text-white focus:outline-none focus:border-emerald-500"
                    />
                  </div>
                </div>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </main>
    </div>
  );
}
