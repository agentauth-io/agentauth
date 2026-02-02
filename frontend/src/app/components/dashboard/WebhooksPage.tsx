// Webhooks Page Component

import { useState } from "react";
import { motion } from "motion/react";
import { Webhook, Plus, Send } from "lucide-react";
import { Webhook as WebhookType } from "./types";

interface WebhooksPageProps {
    webhooks: WebhookType[];
    onAddWebhook: (url: string) => void;
    onDeleteWebhook: (webhookId: string) => void;
    onTestWebhook: (webhookId: string) => void;
}

const AVAILABLE_EVENTS = [
    "authorization.created", "authorization.denied", "authorization.pending",
    "consent.requested", "consent.granted", "consent.revoked",
    "agent.registered", "agent.updated", "agent.deactivated",
];

export function WebhooksPage({
    webhooks,
    onAddWebhook,
    onDeleteWebhook,
    onTestWebhook,
}: WebhooksPageProps) {
    const [newWebhookUrl, setNewWebhookUrl] = useState("");

    const handleAddWebhook = () => {
        if (newWebhookUrl.trim()) {
            onAddWebhook(newWebhookUrl.trim());
            setNewWebhookUrl("");
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
                        value={newWebhookUrl}
                        onChange={(e) => setNewWebhookUrl(e.target.value)}
                        className="flex-1 px-4 py-2.5 bg-white/5 border border-[#333] rounded-lg text-white text-sm focus:outline-none focus:border-[#444]"
                    />
                    <button 
                        onClick={handleAddWebhook}
                        disabled={!newWebhookUrl.trim()}
                        className="flex items-center gap-2 px-6 py-2.5 bg-white hover:bg-gray-200 text-black rounded-lg text-sm font-medium disabled:opacity-50"
                    >
                        <Plus className="w-4 h-4" />
                        Add Endpoint
                    </button>
                </div>
            </div>

            {/* Webhooks List */}
            <div className="space-y-4">
                {webhooks.length === 0 ? (
                    <div className="bg-[#111] border border-[#222] rounded-xl p-12 text-center">
                        <Webhook className="w-12 h-12 text-gray-600 mx-auto mb-4" />
                        <h3 className="text-white font-medium mb-2">No Webhooks Configured</h3>
                        <p className="text-gray-500 text-sm">Add a webhook endpoint to receive real-time notifications.</p>
                    </div>
                ) : webhooks.map((webhook) => (
                    <div key={webhook.id} className="bg-[#111] border border-[#222] rounded-xl p-5">
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
                                    onClick={() => onTestWebhook(webhook.id)}
                                    className="px-3 py-1.5 bg-white/5 hover:bg-white/10 border border-[#333] rounded-lg text-xs"
                                >
                                    <Send className="w-3.5 h-3.5 inline mr-1" />
                                    Test
                                </button>
                                <button 
                                    onClick={() => onDeleteWebhook(webhook.id)}
                                    className="px-3 py-1.5 bg-red-500/10 hover:bg-red-500/20 text-red-500 border border-red-500/20 rounded-lg text-xs"
                                >
                                    Delete
                                </button>
                            </div>
                        </div>
                        <div>
                            <p className="text-xs text-gray-500 mb-2">Subscribed Events</p>
                            <div className="flex flex-wrap gap-2">
                                {webhook.events.map((event: string, j: number) => (
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
                <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                    {AVAILABLE_EVENTS.map((event, i) => (
                        <div key={i} className="px-4 py-3 bg-[#111] border border-[#222] rounded-lg">
                            <code className="text-cyan-400 text-sm">{event}</code>
                        </div>
                    ))}
                </div>
            </div>
        </motion.div>
    );
}

export default WebhooksPage;
