// Agents Page Component

import { useState } from "react";
import { motion } from "motion/react";
import { Bot, Search, Plus, Trash2 } from "lucide-react";
import { Agent } from "./types";

interface AgentsPageProps {
    agents: Agent[];
    onRegisterAgent: (name: string) => void;
    onDeleteAgent: (agentId: string) => void;
}

export function AgentsPage({
    agents,
    onRegisterAgent,
    onDeleteAgent,
}: AgentsPageProps) {
    const [agentSearch, setAgentSearch] = useState("");
    const [showRegisterAgent, setShowRegisterAgent] = useState(false);
    const [newAgentName, setNewAgentName] = useState("");

    const handleRegisterAgent = () => {
        if (newAgentName.trim()) {
            onRegisterAgent(newAgentName.trim());
            setNewAgentName("");
            setShowRegisterAgent(false);
        }
    };

    const filteredAgents = agents.filter(agent => 
        agent.name.toLowerCase().includes(agentSearch.toLowerCase())
    );

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
                    onClick={() => setShowRegisterAgent(true)}
                    className="flex items-center gap-2 px-4 py-2.5 bg-white hover:bg-gray-200 text-black rounded-lg text-sm font-medium"
                >
                    <Plus className="w-4 h-4" />
                    Register Agent
                </button>
            </div>

            {/* Register Agent Modal */}
            {showRegisterAgent && (
                <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50">
                    <div className="bg-[#111] border border-[#333] rounded-2xl p-6 w-full max-w-md">
                        <h3 className="text-lg font-semibold text-white mb-4">Register New Agent</h3>
                        <div className="mb-4">
                            <label className="block text-sm text-gray-400 mb-2">Agent Name</label>
                            <input
                                type="text"
                                placeholder="e.g., procurement-bot"
                                value={newAgentName}
                                onChange={(e) => setNewAgentName(e.target.value)}
                                className="w-full px-4 py-3 bg-black border border-[#333] rounded-lg text-white focus:outline-none focus:border-[#555]"
                            />
                        </div>
                        <div className="flex gap-3">
                            <button
                                onClick={() => setShowRegisterAgent(false)}
                                className="flex-1 px-4 py-3 border border-[#333] rounded-lg text-white hover:bg-white/5"
                            >
                                Cancel
                            </button>
                            <button
                                onClick={handleRegisterAgent}
                                disabled={!newAgentName.trim()}
                                className="flex-1 px-4 py-3 bg-white text-black rounded-lg font-medium hover:bg-gray-200 disabled:opacity-50"
                            >
                                Register
                            </button>
                        </div>
                    </div>
                </div>
            )}

            {/* Agents Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {filteredAgents.map((agent) => (
                    <div key={agent.id} className="bg-[#111] border border-[#222] rounded-xl p-5">
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
                                onClick={() => onDeleteAgent(agent.id)}
                                className="p-2 hover:bg-red-500/10 rounded-lg text-gray-500 hover:text-red-500"
                            >
                                <Trash2 className="w-4 h-4" />
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
            
            {/* Empty State */}
            {filteredAgents.length === 0 && (
                <div className="bg-[#111] border border-[#222] rounded-xl p-12 text-center">
                    <Bot className="w-12 h-12 text-gray-600 mx-auto mb-4" />
                    <h3 className="text-white font-medium mb-2">No Agents Found</h3>
                    <p className="text-gray-500 text-sm mb-4">
                        {agentSearch ? "No agents match your search." : "Register your first agent to get started."}
                    </p>
                    {!agentSearch && (
                        <button
                            onClick={() => setShowRegisterAgent(true)}
                            className="px-4 py-2 bg-white text-black rounded-lg text-sm font-medium hover:bg-gray-200"
                        >
                            Register Agent
                        </button>
                    )}
                </div>
            )}
        </motion.div>
    );
}

export default AgentsPage;
