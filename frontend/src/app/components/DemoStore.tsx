import { useState, useEffect } from "react";
import { motion, AnimatePresence } from "motion/react";
import {
    ShoppingCart,
    Bot,
    Check,
    X,
    AlertTriangle,
    Loader2,
    Package,
    CreditCard,
    Shield,
    Zap,
    DollarSign,
    Ban,
    Sparkles,
    ArrowRight,
    RefreshCw,
} from "lucide-react";

// Demo products - designed to show different scenarios
const PRODUCTS = [
    {
        id: "prod_001",
        name: "Notion Pro Plan",
        price: 10.00,
        image: "📝",
        category: "SaaS",
        merchant: "notion.so",
        scenario: "approved"
    },
    {
        id: "prod_002",
        name: "GitHub Copilot",
        price: 19.00,
        image: "🤖",
        category: "Developer Tools",
        merchant: "github.com",
        scenario: "approved"
    },
    {
        id: "prod_003",
        name: "DigitalOcean Droplet",
        price: 24.00,
        image: "☁️",
        category: "Cloud Hosting",
        merchant: "digitalocean.com",
        scenario: "approved"
    },
    {
        id: "prod_004",
        name: "Premium Mechanical Keyboard",
        price: 149.99,
        image: "⌨️",
        category: "Hardware",
        merchant: "amazon.com",
        scenario: "over_budget"
    },
    {
        id: "prod_005",
        name: "Online Poker Credits",
        price: 25.00,
        image: "🎰",
        category: "Gambling",
        merchant: "pokerstars.com",
        scenario: "blocked_merchant"
    },
    {
        id: "prod_006",
        name: "AWS Monthly Bill",
        price: 45.99,
        image: "☁️",
        category: "Cloud Services",
        merchant: "aws.amazon.com",
        scenario: "approved"
    },
];

interface TransactionStep {
    step: string;
    status: "pending" | "success" | "error" | "active" | "warning";
    message?: string;
    detail?: string;
}

interface DemoStoreProps {
    onBack?: () => void;
}

export function DemoStore({ onBack }: DemoStoreProps) {
    const [selectedProduct, setSelectedProduct] = useState<typeof PRODUCTS[0] | null>(null);
    const [maxBudget, setMaxBudget] = useState(50);
    const [isProcessing, setIsProcessing] = useState(false);
    const [steps, setSteps] = useState<TransactionStep[]>([]);
    const [transactionComplete, setTransactionComplete] = useState(false);
    const [finalDecision, setFinalDecision] = useState<"ALLOW" | "DENY" | null>(null);
    const [denyReason, setDenyReason] = useState<string>("");
    const [showIntro, setShowIntro] = useState(true);

    const updateStep = (stepName: string, status: TransactionStep["status"], message?: string, detail?: string) => {
        setSteps(prev => {
            const existing = prev.find(s => s.step === stepName);
            if (existing) {
                return prev.map(s => s.step === stepName ? { ...s, status, message, detail } : s);
            }
            return [...prev, { step: stepName, status, message, detail }];
        });
    };

    const simulateAIPurchase = async (product: typeof PRODUCTS[0]) => {
        setIsProcessing(true);
        setSteps([]);
        setTransactionComplete(false);
        setFinalDecision(null);
        setDenyReason("");
        setShowIntro(false);

        // Fully simulated - no real API calls needed
        // Step 1: AI Agent Activation
        updateStep("agent", "active", "AI Shopping Agent activated...");
        await new Promise(r => setTimeout(r, 800));
        updateStep("agent", "success", "Agent ready to purchase", `Target: ${product.name}`);

        // Step 2: Create Consent (simulated)
        updateStep("consent", "active", "Creating user spending consent...");
        await new Promise(r => setTimeout(r, 1000));
        updateStep("consent", "success", "Consent granted", `Limit: $${maxBudget} max`);

        // Step 3: Check Spending Limits
        updateStep("limits", "active", "Checking spending limits...");
        await new Promise(r => setTimeout(r, 800));

        if (product.price > maxBudget) {
            updateStep("limits", "error", "LIMIT EXCEEDED", `$${product.price} > $${maxBudget} budget`);
        } else {
            updateStep("limits", "success", "Within spending limit", `$${product.price} < $${maxBudget}`);
        }

        // Step 4: Check Merchant Rules
        updateStep("rules", "active", "Evaluating merchant rules...");
        await new Promise(r => setTimeout(r, 800));

        if (product.scenario === "blocked_merchant") {
            updateStep("rules", "error", "MERCHANT BLOCKED", `${product.merchant} is on blacklist`);
        } else {
            updateStep("rules", "success", "Merchant allowed", `${product.merchant} verified`);
        }

        // Step 5: Request Authorization (simulated decision)
        updateStep("authorize", "active", "Requesting final authorization...");
        await new Promise(r => setTimeout(r, 1200));

        // Determine decision based on rules
        const isApproved = product.price <= maxBudget && product.scenario !== "blocked_merchant";

        if (isApproved) {
            setFinalDecision("ALLOW");
            const fakeAuthCode = `auth_${Date.now().toString(36)}_${Math.random().toString(36).substring(2, 8)}`;
            updateStep("authorize", "success", "✅ AUTHORIZED", `Code: ${fakeAuthCode}`);

            // Step 6: Process Payment (simulated)
            updateStep("payment", "active", "Processing Stripe payment...");
            await new Promise(r => setTimeout(r, 1000));
            updateStep("payment", "success", "💳 Payment processed", `$${product.price} charged`);

            // Step 7: Complete
            updateStep("complete", "success", "🎉 Purchase complete!", "Transaction recorded");
            setTransactionComplete(true);

        } else {
            setFinalDecision("DENY");
            const reason = product.price > maxBudget ? "amount_exceeded" : "merchant_blocked";
            setDenyReason(reason);
            updateStep("authorize", "error", "❌ DENIED", reason === "amount_exceeded"
                ? `Amount $${product.price} exceeds $${maxBudget} limit`
                : `Merchant ${product.merchant} is blocked`);
        }

        setIsProcessing(false);
    };

    const handlePurchase = (product: typeof PRODUCTS[0]) => {
        setSelectedProduct(product);
        simulateAIPurchase(product);
    };

    const resetDemo = () => {
        setSelectedProduct(null);
        setSteps([]);
        setTransactionComplete(false);
        setFinalDecision(null);
        setDenyReason("");
        setShowIntro(true);
    };

    const getScenarioLabel = (product: typeof PRODUCTS[0]) => {
        if (product.price > maxBudget) return { text: "Over Budget", color: "red" };
        if (product.scenario === "blocked_merchant") return { text: "Blocked Merchant", color: "orange" };
        return { text: "Will Approve", color: "green" };
    };

    return (
        <section className="relative px-6 py-8 min-h-screen bg-gradient-to-br from-[#0A0A0F] via-[#12121A] to-[#0A0A0F]">
            <div className="max-w-6xl mx-auto">
                {/* Header */}
                <motion.div
                    className="text-center mb-8"
                    initial={{ opacity: 0, y: -20 }}
                    animate={{ opacity: 1, y: 0 }}
                >
                    <div className="inline-flex items-center gap-2 px-4 py-2 bg-gradient-to-r from-purple-500/20 to-cyan-500/20 border border-purple-500/30 rounded-full mb-4">
                        <Sparkles className="w-4 h-4 text-purple-400" />
                        <span className="text-transparent bg-clip-text bg-gradient-to-r from-purple-400 to-cyan-400 text-sm font-medium">
                            Live Interactive Demo
                        </span>
                    </div>
                    <h1 className="text-4xl font-bold text-white mb-3">
                        Watch AI Agents Buy <span className="text-transparent bg-clip-text bg-gradient-to-r from-purple-400 to-cyan-400">Safely</span>
                    </h1>
                    <p className="text-gray-400 max-w-xl mx-auto">
                        Set a spending limit, click a product, and watch AgentAuth authorize (or deny) the purchase in real-time
                    </p>
                </motion.div>

                {/* Budget Control */}
                <motion.div
                    className="mb-8 p-6 bg-gradient-to-r from-purple-500/10 to-cyan-500/10 border border-white/10 rounded-2xl max-w-lg mx-auto"
                    initial={{ opacity: 0, scale: 0.95 }}
                    animate={{ opacity: 1, scale: 1 }}
                    transition={{ delay: 0.1 }}
                >
                    <div className="flex items-center gap-3 mb-4">
                        <div className="w-10 h-10 rounded-xl bg-green-500/20 flex items-center justify-center">
                            <DollarSign className="w-5 h-5 text-green-400" />
                        </div>
                        <div>
                            <h3 className="text-white font-semibold">Your Spending Limit</h3>
                            <p className="text-gray-500 text-sm">AI agent cannot exceed this amount</p>
                        </div>
                    </div>
                    <div className="flex items-center gap-4">
                        <input
                            type="range"
                            min={10}
                            max={200}
                            step={5}
                            value={maxBudget}
                            onChange={(e) => setMaxBudget(Number(e.target.value))}
                            className="flex-1 h-2 bg-white/10 rounded-full appearance-none cursor-pointer
                                       [&::-webkit-slider-thumb]:appearance-none
                                       [&::-webkit-slider-thumb]:w-5
                                       [&::-webkit-slider-thumb]:h-5
                                       [&::-webkit-slider-thumb]:rounded-full
                                       [&::-webkit-slider-thumb]:bg-gradient-to-r
                                       [&::-webkit-slider-thumb]:from-purple-500
                                       [&::-webkit-slider-thumb]:to-cyan-500
                                       [&::-webkit-slider-thumb]:cursor-pointer"
                            disabled={isProcessing}
                        />
                        <span className="text-3xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-green-400 to-emerald-400 w-24 text-right">
                            ${maxBudget}
                        </span>
                    </div>
                </motion.div>

                <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
                    {/* Products Grid */}
                    <motion.div
                        initial={{ opacity: 0, x: -20 }}
                        animate={{ opacity: 1, x: 0 }}
                        transition={{ delay: 0.2 }}
                    >
                        <h2 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
                            <Package className="w-5 h-5 text-purple-400" />
                            Click a product to start the AI purchase
                        </h2>
                        <div className="grid grid-cols-2 gap-3">
                            {PRODUCTS.map((product) => {
                                const scenario = getScenarioLabel(product);
                                return (
                                    <motion.div
                                        key={product.id}
                                        className={`p-4 rounded-xl border transition-all cursor-pointer ${isProcessing
                                            ? "opacity-50 cursor-not-allowed"
                                            : scenario.color === "green"
                                                ? "bg-white/5 border-white/10 hover:border-green-500/50 hover:bg-green-500/5"
                                                : scenario.color === "red"
                                                    ? "bg-red-500/5 border-red-500/20 hover:border-red-500/50"
                                                    : "bg-orange-500/5 border-orange-500/20 hover:border-orange-500/50"
                                            }`}
                                        whileHover={!isProcessing ? { scale: 1.02 } : {}}
                                        whileTap={!isProcessing ? { scale: 0.98 } : {}}
                                        onClick={() => !isProcessing && handlePurchase(product)}
                                    >
                                        <div className="text-3xl mb-2">{product.image}</div>
                                        <h3 className="text-sm font-semibold text-white mb-1 truncate">{product.name}</h3>
                                        <p className="text-xs text-gray-500 mb-2">{product.category}</p>
                                        <div className="flex items-center justify-between">
                                            <span className="text-lg font-bold text-white">${product.price}</span>
                                            <span className={`text-[10px] px-2 py-0.5 rounded-full ${scenario.color === "green" ? "bg-green-500/20 text-green-400" :
                                                scenario.color === "red" ? "bg-red-500/20 text-red-400" :
                                                    "bg-orange-500/20 text-orange-400"
                                                }`}>
                                                {scenario.text}
                                            </span>
                                        </div>
                                    </motion.div>
                                );
                            })}
                        </div>
                    </motion.div>

                    {/* Authorization Flow */}
                    <motion.div
                        initial={{ opacity: 0, x: 20 }}
                        animate={{ opacity: 1, x: 0 }}
                        transition={{ delay: 0.3 }}
                        className="bg-[#0a0a0f] border border-white/10 rounded-2xl p-6 min-h-[400px]"
                    >
                        <h2 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
                            <Shield className="w-5 h-5 text-cyan-400" />
                            Authorization Flow
                        </h2>

                        {showIntro && steps.length === 0 && (
                            <div className="flex flex-col items-center justify-center h-64 text-center">
                                <Bot className="w-16 h-16 text-purple-400/30 mb-4" />
                                <p className="text-gray-500">Click a product to watch<br />the authorization process</p>
                                <div className="flex items-center gap-2 mt-4 text-gray-600">
                                    <ArrowRight className="w-4 h-4" />
                                    <span className="text-sm">Real-time API calls shown here</span>
                                </div>
                            </div>
                        )}

                        <AnimatePresence mode="wait">
                            {steps.length > 0 && (
                                <motion.div
                                    initial={{ opacity: 0 }}
                                    animate={{ opacity: 1 }}
                                    exit={{ opacity: 0 }}
                                    className="space-y-3"
                                >
                                    {steps.map((step, index) => (
                                        <motion.div
                                            key={step.step}
                                            className={`flex items-start gap-3 p-3 rounded-lg ${step.status === "success" ? "bg-green-500/10" :
                                                step.status === "error" ? "bg-red-500/10" :
                                                    step.status === "warning" ? "bg-yellow-500/10" :
                                                        step.status === "active" ? "bg-purple-500/10" :
                                                            "bg-gray-500/10"
                                                }`}
                                            initial={{ opacity: 0, x: -20 }}
                                            animate={{ opacity: 1, x: 0 }}
                                            transition={{ delay: index * 0.05 }}
                                        >
                                            <div className={`w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 ${step.status === "success" ? "bg-green-500/30" :
                                                step.status === "error" ? "bg-red-500/30" :
                                                    step.status === "warning" ? "bg-yellow-500/30" :
                                                        step.status === "active" ? "bg-purple-500/30" :
                                                            "bg-gray-500/30"
                                                }`}>
                                                {step.status === "success" && <Check className="w-4 h-4 text-green-400" />}
                                                {step.status === "error" && <X className="w-4 h-4 text-red-400" />}
                                                {step.status === "warning" && <AlertTriangle className="w-4 h-4 text-yellow-400" />}
                                                {step.status === "active" && <Loader2 className="w-4 h-4 text-purple-400 animate-spin" />}
                                                {step.status === "pending" && <Zap className="w-4 h-4 text-gray-400" />}
                                            </div>
                                            <div className="flex-1 min-w-0">
                                                <p className={`font-medium ${step.status === "success" ? "text-green-400" :
                                                    step.status === "error" ? "text-red-400" :
                                                        step.status === "warning" ? "text-yellow-400" :
                                                            "text-white"
                                                    }`}>{step.message}</p>
                                                {step.detail && (
                                                    <p className="text-xs text-gray-500 mt-0.5">{step.detail}</p>
                                                )}
                                            </div>
                                        </motion.div>
                                    ))}
                                </motion.div>
                            )}
                        </AnimatePresence>

                        {/* Final Decision Banner */}
                        <AnimatePresence>
                            {finalDecision && !isProcessing && (
                                <motion.div
                                    className={`mt-6 p-4 rounded-xl ${finalDecision === "ALLOW"
                                        ? "bg-gradient-to-r from-green-500/20 to-emerald-500/20 border border-green-500/30"
                                        : "bg-gradient-to-r from-red-500/20 to-orange-500/20 border border-red-500/30"
                                        }`}
                                    initial={{ opacity: 0, y: 10 }}
                                    animate={{ opacity: 1, y: 0 }}
                                    exit={{ opacity: 0, y: -10 }}
                                >
                                    <div className="flex items-center gap-3">
                                        {finalDecision === "ALLOW" ? (
                                            <>
                                                <Shield className="w-8 h-8 text-green-400" />
                                                <div>
                                                    <p className="text-green-400 font-bold text-lg">PURCHASE AUTHORIZED ✓</p>
                                                    <p className="text-sm text-gray-400">
                                                        ${selectedProduct?.price} payment processed via Stripe
                                                    </p>
                                                </div>
                                            </>
                                        ) : (
                                            <>
                                                <Ban className="w-8 h-8 text-red-400" />
                                                <div>
                                                    <p className="text-red-400 font-bold text-lg">PURCHASE BLOCKED ✗</p>
                                                    <p className="text-sm text-gray-400">
                                                        {denyReason === "amount_exceeded"
                                                            ? `$${selectedProduct?.price} exceeds your $${maxBudget} limit`
                                                            : `Merchant ${selectedProduct?.merchant} is blocked`
                                                        }
                                                    </p>
                                                </div>
                                            </>
                                        )}
                                    </div>
                                    <button
                                        onClick={resetDemo}
                                        className="mt-4 w-full py-2 px-4 bg-white/10 hover:bg-white/20 rounded-lg text-white text-sm flex items-center justify-center gap-2 transition-colors"
                                    >
                                        <RefreshCw className="w-4 h-4" />
                                        Try Another Purchase
                                    </button>
                                </motion.div>
                            )}
                        </AnimatePresence>
                    </motion.div>
                </div>

                {/* Back link */}
                {onBack && (
                    <div className="text-center mt-8">
                        <button
                            onClick={onBack}
                            className="text-gray-400 hover:text-white transition-colors"
                        >
                            ← Back to Home
                        </button>
                    </div>
                )}
            </div>
        </section>
    );
}
