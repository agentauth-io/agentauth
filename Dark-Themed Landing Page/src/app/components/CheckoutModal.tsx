import { motion, AnimatePresence } from "motion/react";
import { X, CreditCard, Lock, Loader2 } from "lucide-react";
import { useState } from "react";

interface CheckoutModalProps {
    isOpen: boolean;
    onClose: () => void;
    planId: string;
    planName: string;
    price: number;
}

export function CheckoutModal({
    isOpen,
    onClose,
    planId,
    planName,
    price,
}: CheckoutModalProps) {
    const [isLoading, setIsLoading] = useState(false);
    const [email, setEmail] = useState("");
    const [name, setName] = useState("");
    const [error, setError] = useState("");
    const [success, setSuccess] = useState(false);

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setError("");
        setIsLoading(true);

        try {
            // For free tier, just register
            if (planId === "free") {
                // Simulate API call
                await new Promise((resolve) => setTimeout(resolve, 1000));
                setSuccess(true);
                return;
            }

            // For paid tiers, create subscription via API
            const response = await fetch("/api/payments/subscribe", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                },
                body: JSON.stringify({
                    email,
                    name,
                    price_id: planId,
                }),
            });

            if (!response.ok) {
                const data = await response.json();
                throw new Error(data.detail || "Failed to create subscription");
            }

            const data = await response.json();

            // If we have a client_secret, redirect to Stripe checkout
            // In a real implementation, you'd use Stripe.js Elements here
            if (data.client_secret) {
                // For now, show success - in production, integrate Stripe Elements
                console.log("Stripe client secret:", data.client_secret);
                setSuccess(true);
            } else {
                setSuccess(true);
            }
        } catch (err) {
            setError(err instanceof Error ? err.message : "Something went wrong");
        } finally {
            setIsLoading(false);
        }
    };

    const handleClose = () => {
        if (!isLoading) {
            setEmail("");
            setName("");
            setError("");
            setSuccess(false);
            onClose();
        }
    };

    return (
        <AnimatePresence>
            {isOpen && (
                <>
                    {/* Backdrop */}
                    <motion.div
                        className="fixed inset-0 bg-black/80 backdrop-blur-sm z-50"
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        exit={{ opacity: 0 }}
                        onClick={handleClose}
                    />

                    {/* Modal */}
                    <motion.div
                        className="fixed left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 z-50 w-full max-w-md"
                        initial={{ opacity: 0, scale: 0.95, y: 20 }}
                        animate={{ opacity: 1, scale: 1, y: 0 }}
                        exit={{ opacity: 0, scale: 0.95, y: 20 }}
                        transition={{ duration: 0.2 }}
                    >
                        <div className="bg-[#0a0a0f] border border-white/10 rounded-2xl overflow-hidden shadow-2xl">
                            {/* Header */}
                            <div className="flex items-center justify-between p-6 border-b border-white/10">
                                <div>
                                    <h3 className="text-xl font-semibold text-white">
                                        {success ? "Welcome to AgentAuth!" : `Subscribe to ${planName}`}
                                    </h3>
                                    {!success && (
                                        <p className="text-sm text-gray-400 mt-1">
                                            ${price}/month • Cancel anytime
                                        </p>
                                    )}
                                </div>
                                <button
                                    onClick={handleClose}
                                    className="p-2 rounded-lg hover:bg-white/10 transition-colors"
                                    disabled={isLoading}
                                >
                                    <X className="w-5 h-5 text-gray-400" />
                                </button>
                            </div>

                            {/* Content */}
                            <div className="p-6">
                                {success ? (
                                    <motion.div
                                        initial={{ opacity: 0, y: 10 }}
                                        animate={{ opacity: 1, y: 0 }}
                                        className="text-center py-8"
                                    >
                                        <div className="w-16 h-16 mx-auto mb-4 rounded-full bg-green-500/20 flex items-center justify-center">
                                            <svg
                                                className="w-8 h-8 text-green-500"
                                                fill="none"
                                                viewBox="0 0 24 24"
                                                stroke="currentColor"
                                            >
                                                <path
                                                    strokeLinecap="round"
                                                    strokeLinejoin="round"
                                                    strokeWidth={2}
                                                    d="M5 13l4 4L19 7"
                                                />
                                            </svg>
                                        </div>
                                        <h4 className="text-lg font-medium text-white mb-2">
                                            You're all set!
                                        </h4>
                                        <p className="text-gray-400 text-sm mb-6">
                                            Check your email for next steps to get started with AgentAuth.
                                        </p>
                                        <button
                                            onClick={handleClose}
                                            className="px-6 py-2 bg-white text-black rounded-lg font-medium hover:bg-gray-100 transition-colors"
                                        >
                                            Got it
                                        </button>
                                    </motion.div>
                                ) : (
                                    <form onSubmit={handleSubmit} className="space-y-4">
                                        {/* Email input */}
                                        <div>
                                            <label className="block text-sm font-medium text-gray-300 mb-2">
                                                Email
                                            </label>
                                            <input
                                                type="email"
                                                value={email}
                                                onChange={(e) => setEmail(e.target.value)}
                                                required
                                                className="w-full px-4 py-3 bg-white/5 border border-white/10 rounded-xl text-white placeholder-gray-500 focus:outline-none focus:border-white/30 transition-colors"
                                                placeholder="you@company.com"
                                                disabled={isLoading}
                                            />
                                        </div>

                                        {/* Name input */}
                                        <div>
                                            <label className="block text-sm font-medium text-gray-300 mb-2">
                                                Full Name
                                            </label>
                                            <input
                                                type="text"
                                                value={name}
                                                onChange={(e) => setName(e.target.value)}
                                                required
                                                className="w-full px-4 py-3 bg-white/5 border border-white/10 rounded-xl text-white placeholder-gray-500 focus:outline-none focus:border-white/30 transition-colors"
                                                placeholder="John Doe"
                                                disabled={isLoading}
                                            />
                                        </div>

                                        {/* Card info placeholder */}
                                        {planId !== "free" && (
                                            <div>
                                                <label className="block text-sm font-medium text-gray-300 mb-2">
                                                    Payment Method
                                                </label>
                                                <div className="flex items-center gap-3 px-4 py-3 bg-white/5 border border-white/10 rounded-xl">
                                                    <CreditCard className="w-5 h-5 text-gray-400" />
                                                    <span className="text-gray-400 text-sm">
                                                        Card details will be collected securely via Stripe
                                                    </span>
                                                </div>
                                            </div>
                                        )}

                                        {/* Error message */}
                                        {error && (
                                            <motion.div
                                                initial={{ opacity: 0, y: -10 }}
                                                animate={{ opacity: 1, y: 0 }}
                                                className="p-3 bg-red-500/10 border border-red-500/20 rounded-lg text-red-400 text-sm"
                                            >
                                                {error}
                                            </motion.div>
                                        )}

                                        {/* Submit button */}
                                        <button
                                            type="submit"
                                            disabled={isLoading}
                                            className="w-full py-3 px-6 bg-white text-black rounded-xl font-semibold hover:bg-gray-100 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
                                        >
                                            {isLoading ? (
                                                <>
                                                    <Loader2 className="w-5 h-5 animate-spin" />
                                                    Processing...
                                                </>
                                            ) : planId === "free" ? (
                                                "Create Free Account"
                                            ) : (
                                                `Subscribe for $${price}/month`
                                            )}
                                        </button>

                                        {/* Security note */}
                                        <div className="flex items-center justify-center gap-2 text-gray-500 text-xs">
                                            <Lock className="w-3 h-3" />
                                            <span>Secured by Stripe. Your data is encrypted.</span>
                                        </div>
                                    </form>
                                )}
                            </div>
                        </div>
                    </motion.div>
                </>
            )}
        </AnimatePresence>
    );
}
