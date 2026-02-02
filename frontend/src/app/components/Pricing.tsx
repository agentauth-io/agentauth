import { Check } from "lucide-react";
import { motion } from "motion/react";

const pricingTiers = [
  {
    id: "community",
    name: "Community",
    price: "Free",
    period: "forever",
    description: "For developers exploring AI agent commerce",
    features: [
      "1,000 monthly active agents",
      "Core authorization API",
      "7-day audit logs",
      "Community support",
      "1 environment",
    ],
    cta: "Get Started Free",
    highlighted: false,
  },
  {
    id: "pro",
    name: "Pro",
    price: "$199",
    period: "/month",
    description: "For teams building production AI applications",
    features: [
      "50,000 monthly active agents",
      "Full audit dashboard",
      "SSO/SAML integration",
      "Priority Slack support",
      "SOC2 compliance report",
      "1,000 tenants",
    ],
    cta: "Start Free Trial",
    highlighted: true,
  },
  {
    id: "enterprise",
    name: "Enterprise",
    price: "Custom",
    period: "",
    description: "For organizations with advanced requirements",
    features: [
      "Unlimited agents",
      "On-premise deployment",
      "99.99% SLA guarantee",
      "Dedicated CSM",
      "Custom integrations",
      "HIPAA compliance",
    ],
    cta: "Contact Sales",
    highlighted: false,
  },
];

interface PricingProps {
  onSelectPlan?: (planId: string) => void;
}

export function Pricing({ onSelectPlan: _onSelectPlan }: PricingProps) {
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
    <section id="pricing" className="px-6 lg:px-12 py-32 lg:py-40 border-t border-[#1d1d1f]">
      <div className="max-w-6xl mx-auto">
        {/* Section Header */}
        <motion.div
          className="text-center max-w-2xl mx-auto mb-20"
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true, margin: "-100px" }}
          transition={{ duration: 0.6 }}
        >
          <h2 className="text-4xl md:text-5xl font-semibold tracking-tight text-white mb-6">
            Simple, Transparent Pricing
          </h2>
          <p className="text-lg text-[#86868b] leading-relaxed">
            Start free and scale as your AI agents grow. All plans include core authorization features.
          </p>
        </motion.div>

        {/* Pricing Grid - 3 columns */}
        <div className="grid md:grid-cols-3 gap-6 lg:gap-8">
          {pricingTiers.map((tier, index) => (
            <motion.div
              key={tier.id}
              className={`relative p-8 lg:p-10 rounded-2xl ${
                tier.highlighted
                  ? "bg-white text-black"
                  : "bg-[#1d1d1f]/50"
              }`}
              initial={{ opacity: 0, y: 30 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true, margin: "-50px" }}
              transition={{ duration: 0.6, delay: index * 0.1 }}
            >
              {/* Popular Badge */}
              {tier.highlighted && (
                <div className="absolute -top-3 left-1/2 -translate-x-1/2 px-4 py-1 bg-black text-white text-xs font-medium rounded-full">
                  Most Popular
                </div>
              )}

              {/* Plan Name */}
              <div className={`text-sm font-medium mb-4 ${tier.highlighted ? "text-black/60" : "text-[#86868b]"}`}>
                {tier.name}
              </div>

              {/* Price */}
              <div className="mb-4">
                <span className={`text-4xl font-semibold tracking-tight ${tier.highlighted ? "text-black" : "text-white"}`}>
                  {tier.price}
                </span>
                {tier.period && (
                  <span className={`text-sm ${tier.highlighted ? "text-black/60" : "text-[#86868b]"}`}>
                    {tier.period}
                  </span>
                )}
              </div>

              {/* Description */}
              <p className={`text-sm mb-8 ${tier.highlighted ? "text-black/60" : "text-[#86868b]"}`}>
                {tier.description}
              </p>

              {/* CTA Button */}
              <button
                onClick={() => handleSelectPlan(tier.id)}
                className={`w-full py-3 rounded-full text-sm font-medium transition-colors duration-300 mb-8 ${
                  tier.highlighted
                    ? "bg-black text-white hover:bg-black/90"
                    : "bg-white text-black hover:bg-[#f5f5f7]"
                }`}
              >
                {tier.cta}
              </button>

              {/* Features */}
              <ul className="space-y-3">
                {tier.features.map((feature, featureIndex) => (
                  <li key={featureIndex} className="flex items-start gap-3">
                    <Check className={`w-4 h-4 mt-0.5 flex-shrink-0 ${tier.highlighted ? "text-black" : "text-[#86868b]"}`} />
                    <span className={`text-sm ${tier.highlighted ? "text-black/80" : "text-[#86868b]"}`}>
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
