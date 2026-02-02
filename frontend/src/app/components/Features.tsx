import { Shield, Wallet, Zap, Lock, Eye, Globe } from "lucide-react";
import { motion } from "motion/react";

const features = [
  {
    icon: Shield,
    title: "Cryptographic Consent",
    description: "Ed25519 signatures prove human authorization. Chargeback-proof transactions with immutable consent chains.",
  },
  {
    icon: Wallet,
    title: "Spending Controls",
    description: "Set per-transaction, daily, weekly, and monthly limits. Agents can't exceed what you authorize.",
  },
  {
    icon: Zap,
    title: "Sub-50ms Latency",
    description: "Authorization decisions in milliseconds. No perceptible delay for your AI agents or customers.",
  },
  {
    icon: Lock,
    title: "Merchant Rules",
    description: "Allowlist trusted merchants, block risky categories. Full control over where your agents can transact.",
  },
  {
    icon: Eye,
    title: "Complete Audit Trail",
    description: "Every authorization logged immutably. Export for compliance, debug issues, analyze patterns.",
  },
  {
    icon: Globe,
    title: "Framework Agnostic",
    description: "Works with LangChain, LlamaIndex, AutoGPT, or any custom agent. Simple REST API + SDKs.",
  },
];

export function Features() {
  return (
    <section id="features" className="relative px-6 lg:px-12 py-24 lg:py-32 overflow-hidden bg-[#050505]">
      {/* Subtle gradient */}
      <div className="absolute inset-0 bg-gradient-to-b from-black via-[#050505] to-black" />

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
            <span className="text-sm text-gray-400">Why AgentAuth?</span>
          </div>
          <h2 className="text-3xl md:text-4xl lg:text-5xl font-bold text-white mb-6">
            Authorization Infrastructure
            <br />
            <span className="text-gray-500">Built for AI Commerce</span>
          </h2>
          <p className="text-lg text-gray-500 leading-relaxed">
            Everything you need to let AI agents transact safely on behalf of humans.
          </p>
        </motion.div>

        {/* Features Grid */}
        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
          {features.map((feature, index) => (
            <motion.div
              key={feature.title}
              className="group p-6 rounded-2xl border border-white/5 bg-white/[0.02] hover:bg-white/[0.04] hover:border-white/10 transition-all duration-300"
              initial={{ opacity: 0, y: 30 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.5, delay: index * 0.1 }}
            >
              {/* Icon */}
              <div className="w-12 h-12 rounded-xl bg-white/5 border border-white/10 flex items-center justify-center mb-5 group-hover:bg-white/10 transition-colors">
                <feature.icon className="w-6 h-6 text-gray-400" />
              </div>

              {/* Content */}
              <h3 className="text-lg font-semibold text-white mb-2">
                {feature.title}
              </h3>
              <p className="text-gray-500 text-sm leading-relaxed">
                {feature.description}
              </p>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  );
}
