import { useState } from "react";
import { motion } from "motion/react";
import {
    Plus,
    Webhook,
    Send,
} from "lucide-react";

interface WebhooksPageProps {
    showToast: (message: string, type: "success" | "error" | "info") => void;
}

export function WebhooksPage({ showToast }: WebhooksPageProps) {
    const [webhookUrl, setWebhookUrl] = useState("");

    const handleAddWebhook = () => {
        if (!webhookUrl.trim()) {
            showToast("Please enter a webhook URL", "error");
            return;
        }
        try {
            new URL(webhookUrl);
            showToast(`Webhook endpoint added: ${webhookUrl}`, "success");
            setWebhookUrl("");
        } catch {
            showToast("Please enter a valid URL", "error");
        }
    };

    const handleTestWebhook = (url: string) => {
        showToast(`Test event sent to ${url}`, "info");
    };

    const handleDeleteWebhook = (url: string) => {
        if (confirm(`Delete webhook endpoint?\n${url}`)) {
            showToast("Webhook deleted", "info");
        }
    };

    return (
        <motion.div
            key="webhooks"
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            transition={{ duration: 0.2 }}
        >
            {/* Add Webhook Section */}
            <div className="bg-[#111] border border-[#222] rounded-xl p-6 mb-6">
                <h3 className="text-white font-medium mb-4">Add Webhook Endpoint</h3>
                <div className="flex gap-4">
                    <input
                        type="text"
                        placeholder="https://your-server.com/webhooks/agentauth"
                        value={webhookUrl}
                        onChange={(e) => setWebhookUrl(e.target.value)}
                        className="flex-1 px-4 py-2.5 bg-white/5 border border-[#333] rounded-lg text-white text-sm focus:outline-none focus:border-[#444]"
                    />
                    <button
                        onClick={handleAddWebhook}
                        className="flex items-center gap-2 px-6 py-2.5 bg-white hover:bg-gray-200 text-black rounded-lg text-sm font-medium"
                    >
                        <Plus className="w-4 h-4" />
                        Add Endpoint
                    </button>
                </div>
            </div>

            {/* Webhooks List */}
            <div className="space-y-4">
                {[
                    { url: "https://api.company.com/webhooks/agentauth", events: ["authorization.created", "authorization.denied"], status: "active", successRate: 99.8 },
                    { url: "https://slack.company.com/hooks/notify", events: ["authorization.denied", "consent.requested"], status: "active", successRate: 100 },
                    { url: "https://analytics.company.com/events", events: ["all"], status: "failing", successRate: 85.2 },
                ].map((webhook, i) => (
                    <div key={i} className="bg-[#111] border border-[#222] rounded-xl p-5">
                        <div className="flex items-start justify-between mb-4">
                            <div className="flex items-center gap-3">
                                <div className={`w-10 h-10 rounded-lg flex items-center justify-center ${webhook.status === "active" ? "bg-emerald-500/10" : "bg-red-500/10"}`}>
                                    <Webhook className={`w-5 h-5 ${webhook.status === "active" ? "text-emerald-500" : "text-red-500"}`} />
                                </div>
                                <div>
                                    <code className="text-cyan-400 text-sm">{webhook.url}</code>
                                    <div className="flex items-center gap-2 mt-1">
                                        <span className={`inline-flex items-center gap-1 text-xs ${webhook.status === "active" ? "text-emerald-500" : "text-red-500"}`}>
                                            <span className="w-1.5 h-1.5 rounded-full bg-current" />
                                            {webhook.status === "active" ? "Healthy" : "Failing"}
                                        </span>
                                        <span className="text-xs text-gray-500">• {webhook.successRate}% success rate</span>
                                    </div>
                                </div>
                            </div>
                            <div className="flex items-center gap-2">
                                <button
                                    onClick={() => handleTestWebhook(webhook.url)}
                                    className="px-3 py-1.5 bg-white/5 hover:bg-white/10 border border-[#333] rounded-lg text-xs"
                                >
                                    <Send className="w-3.5 h-3.5 inline mr-1" />
                                    Test
                                </button>
                                <button
                                    onClick={() => showToast(`Editing webhook: ${webhook.url}`, "info")}
                                    className="px-3 py-1.5 bg-white/5 hover:bg-white/10 border border-[#333] rounded-lg text-xs"
                                >
                                    Edit
                                </button>
                                <button
                                    onClick={() => handleDeleteWebhook(webhook.url)}
                                    className="px-3 py-1.5 bg-red-500/10 hover:bg-red-500/20 text-red-500 border border-red-500/20 rounded-lg text-xs"
                                >
                                    Delete
                                </button>
                            </div>
                        </div>
                        <div>
                            <p className="text-xs text-gray-500 mb-2">Subscribed Events</p>
                            <div className="flex flex-wrap gap-2">
                                {webhook.events.map((event, j) => (
                                    <span key={j} className="px-2.5 py-1 bg-white/5 rounded-lg text-xs text-gray-400">
                                        {event}
                                    </span>
                                ))}
                            </div>
                        </div>
                    </div>
                ))}
            </div>

            {/* Event Types Reference */}
            <div className="mt-8">
                <h3 className="text-white font-medium mb-4">Available Event Types</h3>
                <div className="grid grid-cols-3 gap-3">
                    {[
                        "authorization.created", "authorization.denied", "authorization.pending",
                        "consent.requested", "consent.granted", "consent.revoked",
                        "agent.registered", "agent.updated", "agent.deactivated",
                    ].map((event, i) => (
                        <div key={i} className="px-4 py-3 bg-[#111] border border-[#222] rounded-lg">
                            <code className="text-cyan-400 text-sm">{event}</code>
                        </div>
                    ))}
                </div>
            </div>
        </motion.div>
    );
}
