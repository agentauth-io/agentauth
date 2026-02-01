import { useState } from "react";
import { motion } from "motion/react";
import {
    Search,
    Plus,
    Bot,
    MoreVertical,
} from "lucide-react";

interface AgentsPageProps {
    showToast: (message: string, type: "success" | "error" | "info") => void;
}

export function AgentsPage({ showToast }: AgentsPageProps) {
    const [agentSearch, setAgentSearch] = useState("");

    return (
        <motion.div
            key="agents"
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            transition={{ duration: 0.2 }}
        >
            {/* Header */}
            <div className="flex items-center justify-between mb-6">
                <div className="flex items-center gap-4">
                    <div className="relative">
                        <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-500" />
                        <input
                            type="text"
                            placeholder="Search agents..."
                            value={agentSearch}
                            onChange={(e) => setAgentSearch(e.target.value)}
                            className="pl-10 pr-4 py-2.5 bg-[#111] border border-[#222] rounded-lg text-white text-sm focus:outline-none focus:border-[#444] w-64"
                        />
                    </div>
                </div>
                <button
                    onClick={() => showToast("Agent registration form coming soon!", "info")}
                    className="flex items-center gap-2 px-4 py-2.5 bg-white hover:bg-gray-200 text-black rounded-lg text-sm font-medium"
                >
                    <Plus className="w-4 h-4" />
                    Register Agent
                </button>
            </div>

            {/* Agents Grid */}
            <div className="grid grid-cols-2 gap-4">
                {[
                    { name: "procurement-bot", status: "active", lastActive: "2 min ago", transactions: 3421, volume: "$289.3K", approvalRate: 98.2 },
                    { name: "expense-agent", status: "active", lastActive: "15 min ago", transactions: 2156, volume: "$187.2K", approvalRate: 97.8 },
                    { name: "travel-assistant", status: "active", lastActive: "32 min ago", transactions: 1823, volume: "$156.8K", approvalRate: 96.5 },
                    { name: "subscription-mgr", status: "active", lastActive: "1 hr ago", transactions: 1245, volume: "$112.4K", approvalRate: 99.1 },
                    { name: "inventory-bot", status: "inactive", lastActive: "2 days ago", transactions: 987, volume: "$101.5K", approvalRate: 97.3 },
                    { name: "analytics-agent", status: "active", lastActive: "5 min ago", transactions: 456, volume: "$45.2K", approvalRate: 100 },
                ].map((agent, i) => (
                    <div key={i} className="bg-[#111] border border-[#222] rounded-xl p-5">
                        <div className="flex items-start justify-between mb-4">
                            <div className="flex items-center gap-3">
                                <div className={`w-10 h-10 rounded-lg flex items-center justify-center ${agent.status === "active" ? "bg-emerald-500/10" : "bg-gray-500/10"}`}>
                                    <Bot className={`w-5 h-5 ${agent.status === "active" ? "text-emerald-500" : "text-gray-500"}`} />
                                </div>
                                <div>
                                    <code className="text-cyan-400">{agent.name}</code>
                                    <div className="flex items-center gap-2 mt-0.5">
                                        <span className={`inline-flex items-center gap-1 text-xs ${agent.status === "active" ? "text-emerald-500" : "text-gray-500"}`}>
                                            <span className="w-1.5 h-1.5 rounded-full bg-current" />
                                            {agent.status === "active" ? "Active" : "Inactive"}
                                        </span>
                                        <span className="text-xs text-gray-500">• Last active {agent.lastActive}</span>
                                    </div>
                                </div>
                            </div>
                            <button
                                onClick={() => showToast(`Agent "${agent.name}" options: Configure, Deactivate, View Logs`, "info")}
                                className="p-2 hover:bg-white/5 rounded-lg"
                            >
                                <MoreVertical className="w-4 h-4 text-gray-500" />
                            </button>
                        </div>
                        <div className="grid grid-cols-3 gap-4">
                            <div>
                                <p className="text-xs text-gray-500 mb-1">Transactions</p>
                                <p className="text-white font-medium">{agent.transactions.toLocaleString()}</p>
                            </div>
                            <div>
                                <p className="text-xs text-gray-500 mb-1">Volume</p>
                                <p className="text-white font-medium">{agent.volume}</p>
                            </div>
                            <div>
                                <p className="text-xs text-gray-500 mb-1">Approval Rate</p>
                                <p className="text-emerald-500 font-medium">{agent.approvalRate}%</p>
                            </div>
                        </div>
                    </div>
                ))}
            </div>
        </motion.div>
    );
}
