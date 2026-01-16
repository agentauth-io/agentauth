import { Check, Sparkles } from "lucide-react";
import { motion } from "motion/react";
import { useState } from "react";

const pricingTiers = [
    {
        id: "free",
        name: "Free",
        price: 0,
        period: "",
        apiCalls: "100/month",
        features: [
            "Basic authorization API",
            "Email support",
            "Community access",
        ],
        cta: "Get Started",
        popular: false,
    },
    {
        id: "pro",
        name: "Pro",
        price: 49,
        period: "/month",
        apiCalls: "10,000/month",
        features: [
            "Everything in Free",
            "Advanced analytics",
            "Priority support",
            "Custom spending rules",
            "Webhook notifications",
        ],
        cta: "Start Pro Trial",
        popular: true,
    },
    {
        id: "enterprise",
        name: "Enterprise",
        price: 199,
        period: "/month",
        apiCalls: "Unlimited",
        features: [
            "Everything in Pro",
            "Dedicated support",
            "Custom integrations",
            "SLA guarantee",
            "On-premise option",
            "Advanced security",
        ],
        cta: "Contact Sales",
        popular: false,
    },
];

const containerVariants = {
    hidden: { opacity: 0 },
    visible: {
        opacity: 1,
        transition: {
            staggerChildren: 0.15,
        },
    },
};

const cardVariants = {
    hidden: { opacity: 0, y: 40 },
    visible: {
        opacity: 1,
        y: 0,
        transition: {
            duration: 0.6,
            ease: "easeOut",
        },
    },
};

interface PricingProps {
    onSelectPlan?: (planId: string) => void;
}

export function Pricing({ onSelectPlan }: PricingProps) {
    const [hoveredCard, setHoveredCard] = useState<string | null>(null);

    const handleSelectPlan = (planId: string) => {
        if (planId === "enterprise") {
            // Open contact form or email
            window.location.href = "mailto:hello@agentauth.in?subject=Enterprise%20Inquiry";
            return;
        }
        if (onSelectPlan) {
            onSelectPlan(planId);
        }
    };

    return (
        <section id="pricing" className="relative px-6 py-24 border-t border-white/5">
            <div className="max-w-6xl mx-auto">
                <motion.div
                    className="text-center mb-16"
                    initial={{ opacity: 0, y: 20 }}
                    whileInView={{ opacity: 1, y: 0 }}
                    viewport={{ once: true }}
                    transition={{ duration: 0.6 }}
                >
                    <motion.div
                        className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-white/5 border border-white/10 mb-6"
                        whileHover={{ scale: 1.02 }}
                    >
                        <Sparkles className="w-4 h-4 text-white" />
                        <span className="text-sm text-white/80">Simple, Transparent Pricing</span>
                    </motion.div>

                    <h2 className="text-4xl md:text-5xl font-bold mb-4 text-white">
                        Choose Your Plan
                    </h2>
                    <p className="text-xl text-gray-400 max-w-2xl mx-auto">
                        Start free and scale as your AI agents grow. All plans include core authorization features.
                    </p>
                </motion.div>

                <motion.div
                    className="grid md:grid-cols-3 gap-6 lg:gap-8"
                    variants={containerVariants}
                    initial="hidden"
                    whileInView="visible"
                    viewport={{ once: true }}
                >
                    {pricingTiers.map((tier) => (
                        <motion.div
                            key={tier.id}
                            variants={cardVariants}
                            onMouseEnter={() => setHoveredCard(tier.id)}
                            onMouseLeave={() => setHoveredCard(null)}
                            whileHover={{
                                y: -8,
                                transition: { duration: 0.3 },
                            }}
                            className="relative"
                        >
                            {/* Popular badge */}
                            {tier.popular && (
                                <motion.div
                                    className="absolute -top-4 left-1/2 -translate-x-1/2 z-10"
                                    initial={{ opacity: 0, y: 10 }}
                                    animate={{ opacity: 1, y: 0 }}
                                    transition={{ delay: 0.5 }}
                                >
                                    <span className="px-4 py-1.5 bg-white text-black text-sm font-semibold rounded-full">
                                        Most Popular
                                    </span>
                                </motion.div>
                            )}

                            <motion.div
                                className={`relative p-8 rounded-2xl border h-full flex flex-col ${tier.popular
                                        ? "border-white/30 bg-gradient-to-b from-white/10 to-white/[0.02]"
                                        : "border-white/10 bg-gradient-to-b from-white/[0.05] to-transparent"
                                    } backdrop-blur-sm overflow-hidden`}
                            >
                                {/* Glow effect for popular */}
                                {tier.popular && (
                                    <div className="absolute inset-0 opacity-30">
                                        <div className="absolute top-0 left-1/2 -translate-x-1/2 w-full h-1/2 bg-white/10 blur-3xl" />
                                    </div>
                                )}

                                {/* Hover glow */}
                                <motion.div
                                    className="absolute inset-0 bg-gradient-to-br from-white/10 via-white/5 to-transparent"
                                    initial={{ opacity: 0 }}
                                    animate={{ opacity: hoveredCard === tier.id ? 1 : 0 }}
                                    transition={{ duration: 0.3 }}
                                />

                                <div className="relative flex-1">
                                    {/* Tier name */}
                                    <h3 className="text-lg font-medium text-white/80 mb-2">
                                        {tier.name}
                                    </h3>

                                    {/* Price */}
                                    <div className="mb-6">
                                        <span className="text-5xl font-bold text-white">
                                            ${tier.price}
                                        </span>
                                        <span className="text-gray-400">{tier.period}</span>
                                    </div>

                                    {/* API calls */}
                                    <p className="text-sm text-gray-400 mb-6 pb-6 border-b border-white/10">
                                        <span className="text-white font-medium">{tier.apiCalls}</span> API calls
                                    </p>

                                    {/* Features */}
                                    <ul className="space-y-3 mb-8">
                                        {tier.features.map((feature, idx) => (
                                            <motion.li
                                                key={idx}
                                                className="flex items-start gap-3 text-gray-300"
                                                initial={{ opacity: 0, x: -10 }}
                                                whileInView={{ opacity: 1, x: 0 }}
                                                viewport={{ once: true }}
                                                transition={{ delay: idx * 0.1 }}
                                            >
                                                <Check className="w-5 h-5 text-white/60 mt-0.5 flex-shrink-0" />
                                                <span className="text-sm">{feature}</span>
                                            </motion.li>
                                        ))}
                                    </ul>
                                </div>

                                {/* CTA Button */}
                                <motion.button
                                    onClick={() => handleSelectPlan(tier.id)}
                                    className={`w-full py-3 px-6 rounded-xl font-semibold text-sm transition-all ${tier.popular
                                            ? "bg-white text-black hover:bg-gray-100"
                                            : "bg-white/10 text-white hover:bg-white/20 border border-white/10"
                                        }`}
                                    whileHover={{ scale: 1.02 }}
                                    whileTap={{ scale: 0.98 }}
                                >
                                    {tier.cta}
                                </motion.button>
                            </motion.div>
                        </motion.div>
                    ))}
                </motion.div>

                {/* Bottom note */}
                <motion.p
                    className="text-center text-gray-500 text-sm mt-12"
                    initial={{ opacity: 0 }}
                    whileInView={{ opacity: 1 }}
                    viewport={{ once: true }}
                    transition={{ delay: 0.8 }}
                >
                    All plans include SSL encryption, 99.9% uptime SLA, and 24/7 monitoring.
                    <br />
                    Need a custom plan? <a href="mailto:hello@agentauth.in" className="text-white hover:underline">Contact us</a>
                </motion.p>
            </div>
        </section>
    );
}
