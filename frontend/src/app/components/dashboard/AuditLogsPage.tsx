import { useState } from "react";
import { motion } from "motion/react";
import {
    Shield,
    Clock,
    Settings,
    Key,
    Lock,
    Search,
    Download,
    XCircle,
    Webhook,
    UserPlus,
} from "lucide-react";
import { colorBgMap, colorTextMap } from "./shared";

interface AuditLogsPageProps {
    onExport: (type: string) => void;
}

export function AuditLogsPage({ onExport }: AuditLogsPageProps) {
    const [logSearch, setLogSearch] = useState("");
    const [logEventFilter, setLogEventFilter] = useState("all");
    const [logTimeFilter, setLogTimeFilter] = useState("24h");
    const [visibleLogs, setVisibleLogs] = useState(10);

    return (
        <motion.div
            key="logs"
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            transition={{ duration: 0.2 }}
        >
            {/* Filters */}
            <div className="flex items-center gap-4 mb-6">
                <div className="flex-1 relative">
                    <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-500" />
                    <input
                        type="text"
                        placeholder="Search logs..."
                        value={logSearch}
                        onChange={(e) => setLogSearch(e.target.value)}
                        className="w-full pl-10 pr-4 py-2.5 bg-[#111] border border-[#222] rounded-lg text-white text-sm focus:outline-none focus:border-[#444]"
                    />
                </div>
                <select
                    value={logEventFilter}
                    onChange={(e) => setLogEventFilter(e.target.value)}
                    className="px-4 py-2.5 bg-[#111] border border-[#222] rounded-lg text-white text-sm focus:outline-none"
                >
                    <option value="all">All Events</option>
                    <option value="authorization">Authorization</option>
                    <option value="config">Configuration</option>
                    <option value="security">Security</option>
                    <option value="api">API</option>
                </select>
                <select
                    value={logTimeFilter}
                    onChange={(e) => setLogTimeFilter(e.target.value)}
                    className="px-4 py-2.5 bg-[#111] border border-[#222] rounded-lg text-white text-sm focus:outline-none"
                >
                    <option value="24h">Last 24 hours</option>
                    <option value="7d">Last 7 days</option>
                    <option value="30d">Last 30 days</option>
                </select>
                <button
                    onClick={() => onExport("audit logs")}
                    className="flex items-center gap-2 px-4 py-2.5 bg-white/5 border border-[#333] rounded-lg text-sm hover:bg-white/10"
                >
                    <Download className="w-4 h-4" />
                    Export
                </button>
            </div>

            {/* Logs Timeline */}
            <div className="space-y-2">
                {[
                    { type: "authorization", icon: Shield, color: "emerald", title: "Transaction authorized", details: "procurement-bot authorized $1,249.99 at AWS", time: "2 min ago" },
                    { type: "authorization", icon: Shield, color: "emerald", title: "Transaction authorized", details: "expense-agent authorized $499.00 at Stripe", time: "15 min ago" },
                    { type: "authorization", icon: Clock, color: "yellow", title: "Transaction pending approval", details: "travel-assistant requested $2,847.50 at United Airlines", time: "32 min ago" },
                    { type: "authorization", icon: XCircle, color: "red", title: "Transaction denied", details: "procurement-bot blocked - Gambling Site not allowed", time: "1 hr ago" },
                    { type: "config", icon: Settings, color: "purple", title: "Settings updated", details: "Daily spending limit changed to $5,000", time: "2 hr ago" },
                    { type: "api", icon: Key, color: "cyan", title: "API key created", details: "New test API key generated: aa_test_****m2Pq", time: "3 hr ago" },
                    { type: "security", icon: Lock, color: "orange", title: "Login detected", details: "Admin login from 192.168.1.1 (San Francisco, US)", time: "5 hr ago" },
                    { type: "config", icon: Webhook, color: "purple", title: "Webhook configured", details: "Added endpoint: https://api.example.com/webhooks", time: "1 day ago" },
                    { type: "authorization", icon: Shield, color: "emerald", title: "Consent granted", details: "subscription-mgr granted access to manage recurring payments", time: "1 day ago" },
                    { type: "security", icon: UserPlus, color: "blue", title: "Team member added", details: "sarah@company.com invited as Admin", time: "2 days ago" },
                ].map((log, i) => (
                    <div key={i} className="flex items-start gap-4 p-4 bg-[#111] border border-[#222] rounded-xl hover:bg-white/[0.02]">
                        <div className={`w-10 h-10 rounded-lg flex items-center justify-center ${colorBgMap[log.color] || "bg-gray-500/10"}`}>
                            <log.icon className={`w-5 h-5 ${colorTextMap[log.color] || "text-gray-500"}`} />
                        </div>
                        <div className="flex-1">
                            <div className="flex items-center gap-2">
                                <span className="text-white font-medium text-sm">{log.title}</span>
                                <span className={`px-2 py-0.5 rounded text-xs ${colorBgMap[log.color] || "bg-gray-500/10"} ${colorTextMap[log.color] || "text-gray-500"}`}>
                                    {log.type}
                                </span>
                            </div>
                            <p className="text-gray-400 text-sm mt-0.5">{log.details}</p>
                        </div>
                        <span className="text-xs text-gray-500">{log.time}</span>
                    </div>
                ))}
            </div>

            {/* Load More */}
            <div className="mt-6 text-center">
                <button
                    onClick={() => setVisibleLogs(prev => prev + 10)}
                    className="px-6 py-2.5 bg-white/5 border border-[#333] rounded-lg text-sm hover:bg-white/10"
                >
                    Load More
                </button>
            </div>
        </motion.div>
    );
}
