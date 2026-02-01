import { motion } from "motion/react";
import {
    CheckCircle,
    XCircle,
    Clock,
    AlertTriangle,
    Bot,
} from "lucide-react";

interface ConsentsPageProps {
    showToast: (message: string, type: "success" | "error" | "info") => void;
}

export function ConsentsPage({ showToast }: ConsentsPageProps) {
    const handleConsentAction = (agent: string, action: "approve" | "deny") => {
        showToast(`${action === "approve" ? "Approved" : "Denied"} consent for ${agent}`, action === "approve" ? "success" : "info");
    };

    const handleRevokeConsent = (agent: string) => {
        showToast(`Revoked consent for ${agent}`, "info");
    };

    return (
        <motion.div
            key="consents"
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            transition={{ duration: 0.2 }}
        >
            {/* Stats */}
            <div className="grid grid-cols-3 gap-4 mb-8">
                <div className="bg-[#111] border border-[#222] rounded-xl p-5">
                    <div className="flex items-center gap-2 text-emerald-500 mb-2">
                        <CheckCircle className="w-5 h-5" />
                        <span className="text-xs text-gray-500">Active Consents</span>
                    </div>
                    <div className="text-3xl font-semibold text-white">24</div>
                </div>
                <div className="bg-[#111] border border-[#222] rounded-xl p-5">
                    <div className="flex items-center gap-2 text-yellow-500 mb-2">
                        <Clock className="w-5 h-5" />
                        <span className="text-xs text-gray-500">Pending Approval</span>
                    </div>
                    <div className="text-3xl font-semibold text-white">3</div>
                </div>
                <div className="bg-[#111] border border-[#222] rounded-xl p-5">
                    <div className="flex items-center gap-2 text-gray-500 mb-2">
                        <XCircle className="w-5 h-5" />
                        <span className="text-xs text-gray-500">Expired</span>
                    </div>
                    <div className="text-3xl font-semibold text-white">7</div>
                </div>
            </div>

            {/* Pending Approvals */}
            <div className="mb-8">
                <h3 className="text-sm font-medium text-white mb-4 flex items-center gap-2">
                    <AlertTriangle className="w-4 h-4 text-yellow-500" />
                    Pending Approval
                </h3>
                <div className="space-y-3">
                    {[
                        { agent: "travel-assistant", scope: "Book flights up to $3,000", requested: "10 min ago" },
                        { agent: "procurement-bot", scope: "Access new vendor: Dell Technologies", requested: "2 hr ago" },
                        { agent: "expense-agent", scope: "Increase daily limit to $5,000", requested: "1 day ago" },
                    ].map((consent, i) => (
                        <div key={i} className="bg-yellow-500/5 border border-yellow-500/20 rounded-xl p-4 flex items-center justify-between">
                            <div className="flex items-center gap-4">
                                <div className="w-10 h-10 bg-yellow-500/10 rounded-lg flex items-center justify-center">
                                    <Bot className="w-5 h-5 text-yellow-500" />
                                </div>
                                <div>
                                    <code className="text-cyan-400 text-sm">{consent.agent}</code>
                                    <p className="text-white text-sm mt-0.5">{consent.scope}</p>
                                    <p className="text-xs text-gray-500">Requested {consent.requested}</p>
                                </div>
                            </div>
                            <div className="flex gap-2">
                                <button
                                    onClick={() => handleConsentAction(consent.agent, "deny")}
                                    className="px-4 py-2 bg-red-500/10 hover:bg-red-500/20 text-red-500 rounded-lg text-sm"
                                >
                                    Deny
                                </button>
                                <button
                                    onClick={() => handleConsentAction(consent.agent, "approve")}
                                    className="px-4 py-2 bg-emerald-500 hover:bg-emerald-600 text-white rounded-lg text-sm"
                                >
                                    Approve
                                </button>
                            </div>
                        </div>
                    ))}
                </div>
            </div>

            {/* Active Consents */}
            <div>
                <h3 className="text-sm font-medium text-white mb-4">Active Consents</h3>
                <div className="bg-[#111] border border-[#222] rounded-xl overflow-hidden">
                    <table className="w-full">
                        <thead>
                            <tr className="border-b border-[#222] bg-[#0d0d0d] text-left">
                                <th className="py-3 px-4 text-xs font-medium text-gray-500 uppercase tracking-wider">Agent</th>
                                <th className="py-3 px-4 text-xs font-medium text-gray-500 uppercase tracking-wider">Scope</th>
                                <th className="py-3 px-4 text-xs font-medium text-gray-500 uppercase tracking-wider">Granted</th>
                                <th className="py-3 px-4 text-xs font-medium text-gray-500 uppercase tracking-wider">Expires</th>
                                <th className="py-3 px-4 text-xs font-medium text-gray-500 uppercase tracking-wider">Status</th>
                                <th className="py-3 px-4 text-xs font-medium text-gray-500 uppercase tracking-wider"></th>
                            </tr>
                        </thead>
                        <tbody>
                            {[
                                { agent: "procurement-bot", scope: "Purchase SaaS subscriptions up to $500/mo", granted: "Jan 1, 2026", expires: "Dec 31, 2026", status: "active" },
                                { agent: "expense-agent", scope: "Submit expense reports up to $1,000", granted: "Jan 5, 2026", expires: "Mar 5, 2026", status: "active" },
                                { agent: "travel-assistant", scope: "Book hotels under $300/night", granted: "Jan 10, 2026", expires: "Apr 10, 2026", status: "active" },
                                { agent: "subscription-mgr", scope: "Manage recurring payments", granted: "Dec 15, 2025", expires: "Jun 15, 2026", status: "active" },
                                { agent: "inventory-bot", scope: "Reorder supplies under $200", granted: "Jan 20, 2026", expires: "Jul 20, 2026", status: "active" },
                            ].map((c, i) => (
                                <tr key={i} className="border-b border-white/5 hover:bg-white/[0.02]">
                                    <td className="py-3.5 px-4">
                                        <code className="text-cyan-400 text-sm">{c.agent}</code>
                                    </td>
                                    <td className="py-3.5 px-4 text-white text-sm">{c.scope}</td>
                                    <td className="py-3.5 px-4 text-gray-500 text-sm">{c.granted}</td>
                                    <td className="py-3.5 px-4 text-gray-500 text-sm">{c.expires}</td>
                                    <td className="py-3.5 px-4">
                                        <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium bg-emerald-500/10 text-emerald-500">
                                            <span className="w-1.5 h-1.5 rounded-full bg-current" />
                                            Active
                                        </span>
                                    </td>
                                    <td className="py-3.5 px-4">
                                        <button
                                            onClick={() => handleRevokeConsent(c.agent)}
                                            className="px-3 py-1.5 bg-red-500/10 hover:bg-red-500/20 text-red-500 rounded-lg text-xs"
                                        >
                                            Revoke
                                        </button>
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            </div>
        </motion.div>
    );
}
