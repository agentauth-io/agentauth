// Connected Accounts Page Component

import { motion } from "motion/react";
import { 
    Landmark, 
    AlertTriangle, 
    X, 
    ExternalLink, 
    RefreshCw, 
    CheckCircle, 
    Link as LinkIcon, 
    Building, 
    Wallet 
} from "lucide-react";
import { ConnectedAccount } from "./types";

interface ConnectedAccountsPageProps {
    connectedAccounts: ConnectedAccount[];
    connectError: string;
    isConnecting: boolean;
    onConnectStripe: () => void;
    onDisconnectAccount: (accountId: string) => void;
    onClearError: () => void;
}

// Stripe SVG icon component
function StripeLogo() {
    return (
        <svg className="w-6 h-6" viewBox="0 0 24 24" fill="#635BFF">
            <path d="M13.976 9.15c-2.172-.806-3.356-1.426-3.356-2.409 0-.831.683-1.305 1.901-1.305 2.227 0 4.515.858 6.09 1.631l.89-5.494C18.252.975 15.697 0 12.165 0 9.667 0 7.589.654 6.104 1.872 4.56 3.147 3.757 4.992 3.757 7.218c0 4.039 2.467 5.76 6.476 7.219 2.585.92 3.445 1.574 3.445 2.583 0 .98-.84 1.545-2.354 1.545-1.875 0-4.965-.921-6.99-2.109l-.9 5.555C5.175 22.99 8.385 24 11.714 24c2.641 0 4.843-.624 6.328-1.813 1.664-1.305 2.525-3.236 2.525-5.732 0-4.128-2.524-5.851-6.591-7.305z"/>
        </svg>
    );
}

export function ConnectedAccountsPage({
    connectedAccounts,
    connectError,
    isConnecting,
    onConnectStripe,
    onDisconnectAccount,
    onClearError,
}: ConnectedAccountsPageProps) {
    const hasActiveStripe = connectedAccounts.some(a => a.provider === "stripe" && a.status === "active");

    return (
        <motion.div
            key="connected-accounts"
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            transition={{ duration: 0.2 }}
        >
            {/* Info Banner */}
            <div className="bg-cyan-500/10 border border-cyan-500/20 rounded-xl p-4 mb-6 flex items-start gap-3">
                <Landmark className="w-5 h-5 text-cyan-500 mt-0.5" />
                <div>
                    <p className="text-white text-sm font-medium">Connect your financial accounts</p>
                    <p className="text-gray-400 text-sm mt-0.5">Link your Stripe, bank accounts, or other payment providers to track all agent transactions in one place.</p>
                </div>
            </div>

            {/* Error Message */}
            {connectError && (
                <div className="bg-red-500/10 border border-red-500/20 rounded-xl p-4 mb-6 flex items-center gap-3">
                    <AlertTriangle className="w-5 h-5 text-red-500" />
                    <p className="text-red-400 text-sm">{connectError}</p>
                    <button onClick={onClearError} className="ml-auto text-red-400 hover:text-red-300">
                        <X className="w-4 h-4" />
                    </button>
                </div>
            )}

            {/* Connected Accounts */}
            {connectedAccounts.length > 0 && (
                <div className="mb-8">
                    <h3 className="text-white font-medium mb-4">Your Connected Accounts</h3>
                    <div className="space-y-4">
                        {connectedAccounts.map((account) => (
                            <div key={account.id} className="bg-[#111] border border-[#222] rounded-xl p-5">
                                <div className="flex items-center justify-between">
                                    <div className="flex items-center gap-4">
                                        <div className="w-12 h-12 bg-[#635BFF]/10 rounded-xl flex items-center justify-center">
                                            <StripeLogo />
                                        </div>
                                        <div>
                                            <div className="flex items-center gap-2">
                                                <span className="text-white font-medium">Stripe</span>
                                                <span className={`px-2 py-0.5 text-xs rounded ${
                                                    account.status === "active" 
                                                        ? "bg-emerald-500/20 text-emerald-400" 
                                                        : "bg-yellow-500/20 text-yellow-400"
                                                }`}>
                                                    {account.status === "active" ? "Connected" : "Pending"}
                                                </span>
                                            </div>
                                            <p className="text-gray-500 text-sm mt-0.5">{account.email} • ID: {account.id.slice(0, 12)}...</p>
                                        </div>
                                    </div>
                                    <div className="flex items-center gap-2">
                                        {account.status === "active" && (
                                            <button className="flex items-center gap-2 px-3 py-2 bg-white/5 hover:bg-white/10 border border-[#333] rounded-lg text-sm">
                                                <ExternalLink className="w-4 h-4" />
                                                Dashboard
                                            </button>
                                        )}
                                        <button 
                                            onClick={() => onDisconnectAccount(account.id)}
                                            className="px-3 py-2 bg-red-500/10 hover:bg-red-500/20 text-red-400 border border-red-500/20 rounded-lg text-sm"
                                        >
                                            Disconnect
                                        </button>
                                    </div>
                                </div>
                            </div>
                        ))}
                    </div>
                </div>
            )}

            {/* Connect Stripe Section */}
            <div className="mb-8">
                <h3 className="text-white font-medium mb-4">Payment Providers</h3>
                <div className="space-y-4">
                    {/* Stripe */}
                    <div className="bg-[#111] border border-[#222] rounded-xl p-5">
                        <div className="flex items-center justify-between">
                            <div className="flex items-center gap-4">
                                <div className="w-12 h-12 bg-[#635BFF]/10 rounded-xl flex items-center justify-center">
                                    <StripeLogo />
                                </div>
                                <div>
                                    <div className="flex items-center gap-2">
                                        <span className="text-white font-medium">Stripe</span>
                                        {hasActiveStripe ? (
                                            <span className="px-2 py-0.5 bg-emerald-500/20 text-emerald-400 text-xs rounded">Connected</span>
                                        ) : (
                                            <span className="px-2 py-0.5 bg-gray-500/20 text-gray-400 text-xs rounded">Not Connected</span>
                                        )}
                                    </div>
                                    <p className="text-gray-500 text-sm mt-0.5">Accept payments and track transactions from your Stripe account</p>
                                </div>
                            </div>
                            <button 
                                onClick={onConnectStripe}
                                disabled={isConnecting || hasActiveStripe}
                                className="flex items-center gap-2 px-4 py-2.5 bg-[#635BFF] hover:bg-[#5851ea] text-white rounded-lg text-sm font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                            >
                                {isConnecting ? (
                                    <>
                                        <RefreshCw className="w-4 h-4 animate-spin" />
                                        Connecting...
                                    </>
                                ) : hasActiveStripe ? (
                                    <>
                                        <CheckCircle className="w-4 h-4" />
                                        Connected
                                    </>
                                ) : (
                                    <>
                                        <LinkIcon className="w-4 h-4" />
                                        Connect Stripe
                                    </>
                                )}
                            </button>
                        </div>
                    </div>

                    {/* PayPal */}
                    <div className="bg-[#111] border border-[#222] rounded-xl p-5">
                        <div className="flex items-center justify-between">
                            <div className="flex items-center gap-4">
                                <div className="w-12 h-12 bg-[#003087]/10 rounded-xl flex items-center justify-center">
                                    <svg className="w-6 h-6" viewBox="0 0 24 24" fill="#003087">
                                        <path d="M7.076 21.337H2.47a.641.641 0 0 1-.633-.74L4.944 3.72a.77.77 0 0 1 .757-.658h6.542c2.297 0 4.126.512 5.44 1.523 1.369 1.053 2.017 2.59 1.926 4.573-.185 4.072-2.895 6.182-7.476 6.182H9.66a.77.77 0 0 0-.757.658l-1.21 5.07a.641.641 0 0 1-.617.269z"/>
                                    </svg>
                                </div>
                                <div>
                                    <div className="flex items-center gap-2">
                                        <span className="text-white font-medium">PayPal</span>
                                        <span className="px-2 py-0.5 bg-yellow-500/20 text-yellow-400 text-xs rounded">Coming Soon</span>
                                    </div>
                                    <p className="text-gray-500 text-sm mt-0.5">Connect your PayPal business account</p>
                                </div>
                            </div>
                            <button disabled className="flex items-center gap-2 px-4 py-2.5 bg-white/5 text-gray-500 rounded-lg text-sm font-medium cursor-not-allowed">
                                <LinkIcon className="w-4 h-4" />
                                Coming Soon
                            </button>
                        </div>
                    </div>

                    {/* Square */}
                    <div className="bg-[#111] border border-[#222] rounded-xl p-5">
                        <div className="flex items-center justify-between">
                            <div className="flex items-center gap-4">
                                <div className="w-12 h-12 bg-white/5 rounded-xl flex items-center justify-center">
                                    <div className="w-6 h-6 bg-white rounded" />
                                </div>
                                <div>
                                    <div className="flex items-center gap-2">
                                        <span className="text-white font-medium">Square</span>
                                        <span className="px-2 py-0.5 bg-yellow-500/20 text-yellow-400 text-xs rounded">Coming Soon</span>
                                    </div>
                                    <p className="text-gray-500 text-sm mt-0.5">Connect your Square seller account</p>
                                </div>
                            </div>
                            <button disabled className="flex items-center gap-2 px-4 py-2.5 bg-white/5 text-gray-500 rounded-lg text-sm font-medium cursor-not-allowed">
                                <LinkIcon className="w-4 h-4" />
                                Coming Soon
                            </button>
                        </div>
                    </div>
                </div>
            </div>

            {/* Bank Accounts Section */}
            <div className="mb-8">
                <h3 className="text-white font-medium mb-4">Bank Accounts</h3>
                <div className="bg-[#111] border border-[#222] rounded-xl p-5">
                    <div className="flex items-center justify-between">
                        <div className="flex items-center gap-4">
                            <div className="w-12 h-12 bg-emerald-500/10 rounded-xl flex items-center justify-center">
                                <Building className="w-6 h-6 text-emerald-500" />
                            </div>
                            <div>
                                <div className="flex items-center gap-2">
                                    <span className="text-white font-medium">Connect via Plaid</span>
                                    <span className="px-2 py-0.5 bg-yellow-500/20 text-yellow-400 text-xs rounded">Coming Soon</span>
                                </div>
                                <p className="text-gray-500 text-sm mt-0.5">Securely connect your bank accounts to track spending</p>
                            </div>
                        </div>
                        <button disabled className="flex items-center gap-2 px-4 py-2.5 bg-white/5 text-gray-500 rounded-lg text-sm font-medium cursor-not-allowed">
                            <LinkIcon className="w-4 h-4" />
                            Coming Soon
                        </button>
                    </div>
                </div>
            </div>

            {/* Agent Transaction Tracking */}
            <div>
                <h3 className="text-white font-medium mb-4">Agent Transaction Overview</h3>
                <div className="bg-[#111] border border-[#222] rounded-xl p-6">
                    <div className="text-center py-8">
                        <div className="w-16 h-16 bg-white/5 rounded-full flex items-center justify-center mx-auto mb-4">
                            <Wallet className="w-8 h-8 text-gray-500" />
                        </div>
                        <h4 className="text-white font-medium mb-2">No accounts connected</h4>
                        <p className="text-gray-500 text-sm max-w-md mx-auto mb-4">
                            Connect your payment providers to see a unified view of all transactions made by your AI agents.
                        </p>
                        <button className="px-6 py-2.5 bg-gradient-to-r from-zinc-700 to-cyan-600 text-white rounded-lg text-sm font-medium hover:opacity-90 transition-opacity">
                            Connect Your First Account
                        </button>
                    </div>
                </div>
            </div>
        </motion.div>
    );
}

export default ConnectedAccountsPage;
