import { Check, Sparkles } from "lucide-react";
import { motion } from "motion/react";

const pricingTiers = [
  {
    id: "free",
    name: "Free",
    price: "$0",
    period: "/month",
    description: "Perfect for exploring and prototyping",
    features: [
      "1,000 authorizations/month",
      "Core authorization API",
      "7-day audit logs",
      "Community support",
      "1 AI agent",
    ],
    cta: "Start Free",
    highlighted: false,
  },
  {
    id: "pro",
    name: "Pro",
    price: "$199",
    period: "/month",
    description: "For teams building production AI applications",
    features: [
      "50,000 authorizations/month",
      "Full audit dashboard",
      "SSO/SAML integration",
      "Priority Slack support",
      "SOC2 compliance report",
      "Unlimited AI agents",
      "Custom spending rules",
    ],
    cta: "Join Waitlist",
    highlighted: true,
  },
  {
    id: "enterprise",
    name: "Enterprise",
    price: "Custom",
    period: "",
    description: "For organizations with advanced requirements",
    features: [
      "Unlimited authorizations",
      "On-premise deployment",
      "99.99% SLA guarantee",
      "Dedicated CSM",
      "Custom integrations",
      "HIPAA compliance",
      "24/7 phone support",
    ],
    cta: "Contact Sales",
    highlighted: false,
  },
];

export function Pricing() {
  const handleSelectPlan = (planId: string) => {
    if (planId === "enterprise") {
      window.location.href = "mailto:hello@agentauth.in?subject=Enterprise%20Inquiry";
      return;
    }
    // Scroll to waitlist form
    const heroSection = document.querySelector('input[type="email"]');
    if (heroSection) {
      heroSection.scrollIntoView({ behavior: 'smooth', block: 'center' });
      (heroSection as HTMLInputElement).focus();
    }
  };

  return (
    <section id="pricing" className="relative px-6 lg:px-12 py-24 lg:py-32 overflow-hidden">
      {/* Background */}
      <div className="absolute inset-0 bg-gradient-to-b from-[#1a1a2e] to-[#0f0f1a]" />
      
      {/* Decorative elements */}
      <div className="absolute top-1/2 left-0 w-96 h-96 bg-purple-600/5 rounded-full blur-3xl -translate-y-1/2" />
      <div className="absolute top-1/2 right-0 w-96 h-96 bg-blue-600/5 rounded-full blur-3xl -translate-y-1/2" />

      <div className="relative z-10 max-w-6xl mx-auto">
        {/* Section Header */}
        <motion.div
          className="text-center max-w-2xl mx-auto mb-16"
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.6 }}
        >
          <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-white/5 border border-white/10 mb-6">
            <Sparkles className="w-4 h-4 text-purple-400" />
            <span className="text-sm text-gray-400">Simple Pricing</span>
          </div>
          <h2 className="text-3xl md:text-4xl lg:text-5xl font-bold text-white mb-6">
            Start Free,
            <span className="bg-gradient-to-r from-purple-400 to-blue-400 bg-clip-text text-transparent"> Scale Infinitely</span>
          </h2>
          <p className="text-lg text-gray-400 leading-relaxed">
            No hidden fees. No setup costs. Pay only for what you use.
          </p>
        </motion.div>

        {/* Pricing Grid */}
        <div className="grid md:grid-cols-3 gap-6 lg:gap-8">
          {pricingTiers.map((tier, index) => (
            <motion.div
              key={tier.id}
              className={`relative p-8 rounded-2xl transition-all duration-300 ${
                tier.highlighted
                  ? "bg-gradient-to-br from-purple-600/20 to-blue-600/20 border-2 border-purple-500/30 scale-105"
                  : "bg-white/[0.02] border border-white/[0.05] hover:border-white/10"
              }`}
              initial={{ opacity: 0, y: 30 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.6, delay: index * 0.1 }}
            >
              {/* Popular Badge */}
              {tier.highlighted && (
                <div className="absolute -top-4 left-1/2 -translate-x-1/2 px-4 py-1.5 bg-gradient-to-r from-purple-600 to-blue-600 text-white text-xs font-semibold rounded-full shadow-lg shadow-purple-500/25">
                  Most Popular
                </div>
              )}

              {/* Plan Name */}
              <div className="text-gray-400 text-sm font-medium mb-2">
                {tier.name}
              </div>

              {/* Price */}
              <div className="mb-4">
                <span className="text-4xl font-bold text-white">
                  {tier.price}
                </span>
                {tier.period && (
                  <span className="text-gray-500 text-sm">
                    {tier.period}
                  </span>
                )}
              </div>

              {/* Description */}
              <p className="text-gray-400 text-sm mb-8">
                {tier.description}
              </p>

              {/* CTA Button */}
              <button
                onClick={() => handleSelectPlan(tier.id)}
                className={`w-full py-3.5 rounded-xl text-sm font-semibold transition-all duration-300 mb-8 ${
                  tier.highlighted
                    ? "bg-gradient-to-r from-purple-600 to-blue-600 text-white hover:shadow-lg hover:shadow-purple-500/25"
                    : "bg-white/5 text-white border border-white/10 hover:bg-white/10"
                }`}
              >
                {tier.cta}
              </button>

              {/* Features */}
              <ul className="space-y-4">
                {tier.features.map((feature, featureIndex) => (
                  <li key={featureIndex} className="flex items-start gap-3">
                    <div className="mt-0.5">
                      <Check className={`w-4 h-4 ${tier.highlighted ? 'text-purple-400' : 'text-gray-500'}`} />
                    </div>
                    <span className="text-gray-400 text-sm">
                      {feature}
                    </span>
                  </li>
                ))}
              </ul>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  );
}
