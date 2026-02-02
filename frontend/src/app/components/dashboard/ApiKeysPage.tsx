// API Keys Page Component

import { useState, useEffect } from "react";
import { motion } from "motion/react";
import {
    Key,
    Plus,
    Copy,
    Trash2,
    RefreshCw,
    CheckCircle,
    AlertTriangle,
    X,
} from "lucide-react";
import { ApiKey } from "./types";

interface ApiKeysPageProps {
    apiKeys: ApiKey[];
    onCreateKey: (name: string, type: "live" | "test") => Promise<string | null>;
    onDeleteKey: (keyId: string) => void;
    onCopyKey: (key: string) => Promise<void>;
    copiedKey: string | null;
}

export function ApiKeysPage({
    apiKeys,
    onCreateKey,
    onDeleteKey,
    onCopyKey,
    copiedKey,
}: ApiKeysPageProps) {
    const [newKeyName, setNewKeyName] = useState("");
    const [newKeyType, setNewKeyType] = useState<"live" | "test">("live");
    const [isCreatingKey, setIsCreatingKey] = useState(false);
    const [showKeySecret, setShowKeySecret] = useState<string | null>(null);

    const handleCreateApiKey = async () => {
        if (!newKeyName.trim()) return;
        
        setIsCreatingKey(true);
        try {
            const keyValue = await onCreateKey(newKeyName.trim(), newKeyType);
            if (keyValue) {
                setShowKeySecret(keyValue);
                setNewKeyName("");
            }
        } finally {
            setIsCreatingKey(false);
        }
    };

    return (
        <motion.div
            key="apikeys"
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            transition={{ duration: 0.2 }}
        >
            {/* Info Banner */}
            <div className="bg-cyan-500/10 border border-cyan-500/20 rounded-xl p-4 mb-6 flex items-start gap-3">
                <AlertTriangle className="w-5 h-5 text-cyan-500 mt-0.5" />
                <div>
                    <p className="text-white text-sm font-medium">Keep your API keys secure</p>
                    <p className="text-gray-400 text-sm mt-0.5">Never share your API keys in public repositories or client-side code. Use environment variables instead.</p>
                </div>
            </div>

            {/* Show newly created key */}
            {showKeySecret && (
                <div className="bg-emerald-500/10 border border-emerald-500/20 rounded-xl p-4 mb-6">
                    <div className="flex items-start gap-3">
                        <CheckCircle className="w-5 h-5 text-emerald-500 mt-0.5" />
                        <div className="flex-1">
                            <p className="text-white text-sm font-medium">API Key Created Successfully!</p>
                            <p className="text-gray-400 text-sm mt-0.5 mb-2">Copy this key now - you won't be able to see it again.</p>
                            <div className="flex items-center gap-2 bg-black/20 p-2 rounded-lg">
                                <code className="text-emerald-400 text-sm flex-1 font-mono break-all">{showKeySecret}</code>
                                <button 
                                    onClick={() => onCopyKey(showKeySecret)}
                                    className="px-3 py-1.5 bg-emerald-500 hover:bg-emerald-600 text-white rounded text-xs font-medium flex-shrink-0"
                                >
                                    {copiedKey === showKeySecret ? "Copied!" : "Copy"}
                                </button>
                            </div>
                        </div>
                        <button onClick={() => setShowKeySecret(null)} className="text-gray-400 hover:text-white">
                            <X className="w-4 h-4" />
                        </button>
                    </div>
                </div>
            )}

            {/* Create Key Section */}
            <div className="bg-[#111] border border-[#222] rounded-xl p-6 mb-6">
                <h3 className="text-white font-medium mb-4">Create New API Key</h3>
                <div className="flex gap-4 flex-wrap">
                    <input
                        type="text"
                        value={newKeyName}
                        onChange={(e) => setNewKeyName(e.target.value)}
                        placeholder="Key name (e.g., Production, Staging)"
                        className="flex-1 min-w-[200px] px-4 py-2.5 bg-white/5 border border-[#333] rounded-lg text-white text-sm focus:outline-none focus:border-[#444]"
                    />
                    <select 
                        value={newKeyType}
                        onChange={(e) => setNewKeyType(e.target.value as "live" | "test")}
                        className="px-4 py-2.5 bg-white/5 border border-[#333] rounded-lg text-white text-sm focus:outline-none"
                    >
                        <option value="live">Live Key</option>
                        <option value="test">Test Key</option>
                    </select>
                    <button 
                        onClick={handleCreateApiKey}
                        disabled={!newKeyName.trim() || isCreatingKey}
                        className="flex items-center gap-2 px-6 py-2.5 bg-white hover:bg-gray-200 text-black rounded-lg text-sm font-medium disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                        {isCreatingKey ? (
                            <>
                                <RefreshCw className="w-4 h-4 animate-spin" />
                                Creating...
                            </>
                        ) : (
                            <>
                                <Plus className="w-4 h-4" />
                                Create Key
                            </>
                        )}
                    </button>
                </div>
            </div>

            {/* Keys List */}
            <div className="space-y-3">
                {apiKeys.length === 0 ? (
                    <div className="bg-[#111] border border-[#222] rounded-xl p-8 text-center">
                        <Key className="w-12 h-12 text-gray-600 mx-auto mb-4" />
                        <h3 className="text-white font-medium mb-2">No API Keys Yet</h3>
                        <p className="text-gray-500 text-sm">Create your first API key to start integrating AgentAuth.</p>
                    </div>
                ) : (
                    apiKeys.map((apiKey) => (
                        <div key={apiKey.id} className="bg-[#111] border border-[#222] rounded-xl p-4">
                            <div className="flex items-center justify-between flex-wrap gap-4">
                                <div className="flex items-center gap-4">
                                    <div className={`w-10 h-10 rounded-lg flex items-center justify-center ${apiKey.isLive ? "bg-emerald-500/10" : "bg-gray-500/10"}`}>
                                        <Key className={`w-5 h-5 ${apiKey.isLive ? "text-emerald-500" : "text-gray-500"}`} />
                                    </div>
                                    <div>
                                        <div className="flex items-center gap-2">
                                            <span className="text-white font-medium">{apiKey.name}</span>
                                            <span className={`px-2 py-0.5 rounded text-xs ${apiKey.isLive ? "bg-emerald-500/10 text-emerald-500" : "bg-gray-500/10 text-gray-500"}`}>
                                                {apiKey.isLive ? "Live" : "Test"}
                                            </span>
                                        </div>
                                        <div className="flex items-center gap-3 mt-1 flex-wrap">
                                            <code className="text-sm text-gray-500 bg-white/5 px-2 py-0.5 rounded">
                                                {apiKey.key.substring(0, 12)}...{apiKey.key.substring(apiKey.key.length - 4)}
                                            </code>
                                            <span className="text-xs text-gray-500">Created {apiKey.created}</span>
                                            <span className="text-xs text-gray-500">Last used {apiKey.lastUsed}</span>
                                        </div>
                                    </div>
                                </div>
                                <div className="flex items-center gap-2">
                                    <button 
                                        onClick={() => onCopyKey(apiKey.key)}
                                        className="p-2.5 bg-white/5 hover:bg-white/10 border border-[#333] rounded-lg"
                                        title="Copy key"
                                    >
                                        {copiedKey === apiKey.key ? (
                                            <CheckCircle className="w-4 h-4 text-emerald-500" />
                                        ) : (
                                            <Copy className="w-4 h-4 text-gray-400" />
                                        )}
                                    </button>
                                    <button 
                                        onClick={() => onDeleteKey(apiKey.id)}
                                        className="p-2.5 bg-red-500/10 hover:bg-red-500/20 border border-red-500/20 rounded-lg"
                                        title="Delete key"
                                    >
                                        <Trash2 className="w-4 h-4 text-red-500" />
                                    </button>
                                </div>
                            </div>
                        </div>
                    ))
                )}
            </div>
        </motion.div>
    );
}

export default ApiKeysPage;
