import { motion } from "motion/react";
import { Shield, Zap, Lock, Eye, Wallet, Globe } from "lucide-react";

const features = [
  {
    icon: Shield,
    title: "Cryptographic Proof",
    description: "Every transaction includes verifiable proof that a human authorized the purchase. Immutable audit trail for compliance.",
    gradient: "from-purple-500 to-purple-600",
  },
  {
    icon: Wallet,
    title: "Spending Controls",
    description: "Set daily, weekly, and per-transaction limits. Control which merchants and categories your agents can access.",
    gradient: "from-blue-500 to-blue-600",
  },
  {
    icon: Zap,
    title: "50ms Authorization",
    description: "Real-time decisioning with sub-50ms latency. Your AI agents never wait. Built for production scale.",
    gradient: "from-yellow-500 to-orange-500",
  },
  {
    icon: Lock,
    title: "Bank-Grade Security",
    description: "Ed25519 signatures, X25519 key exchange. Zero-knowledge architecture. Your keys never leave your infrastructure.",
    gradient: "from-green-500 to-emerald-500",
  },
  {
    icon: Eye,
    title: "Complete Visibility",
    description: "Real-time dashboard showing all agent activity. See every transaction, approval, and denial as it happens.",
    gradient: "from-pink-500 to-rose-500",
  },
  {
    icon: Globe,
    title: "Multi-Agent Support",
    description: "Manage hundreds of AI agents from one dashboard. Each with their own policies, limits, and audit logs.",
    gradient: "from-cyan-500 to-blue-500",
  },
];

export function Features() {
  return (
    <section className="relative py-24 lg:py-32 px-6 lg:px-12 overflow-hidden">
      {/* Background */}
      <div className="absolute inset-0 bg-gradient-to-b from-[#1a1a2e] via-[#16213e] to-[#0f0f1a]" />
      
      {/* Decorative elements */}
      <div className="absolute top-1/2 left-0 w-96 h-96 bg-purple-600/10 rounded-full blur-3xl -translate-y-1/2" />
      <div className="absolute top-1/2 right-0 w-96 h-96 bg-blue-600/10 rounded-full blur-3xl -translate-y-1/2" />

      <div className="relative z-10 max-w-6xl mx-auto">
        {/* Section Header */}
        <motion.div
          className="text-center max-w-3xl mx-auto mb-16 lg:mb-20"
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
            <span className="bg-gradient-to-r from-purple-400 to-blue-400 bg-clip-text text-transparent">
              Built for AI Commerce
            </span>
          </h2>
          <p className="text-lg text-gray-400 leading-relaxed">
            The missing piece between your AI agents and real-world purchases.
            Secure, fast, and auditable.
          </p>
        </motion.div>

        {/* Features Grid */}
        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
          {features.map((feature, index) => (
            <motion.div
              key={feature.title}
              className="group relative p-8 rounded-2xl bg-white/[0.02] border border-white/[0.05] hover:border-white/10 hover:bg-white/[0.04] transition-all duration-500"
              initial={{ opacity: 0, y: 30 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true, margin: "-50px" }}
              transition={{ duration: 0.5, delay: index * 0.1 }}
            >
              {/* Hover glow effect */}
              <div className={`absolute inset-0 rounded-2xl bg-gradient-to-br ${feature.gradient} opacity-0 group-hover:opacity-5 transition-opacity duration-500`} />
              
              {/* Icon */}
              <div className={`inline-flex p-3 rounded-xl bg-gradient-to-br ${feature.gradient} mb-6 shadow-lg`}>
                <feature.icon className="w-6 h-6 text-white" />
              </div>

              {/* Content */}
              <h3 className="text-xl font-semibold text-white mb-3 group-hover:text-white transition-colors">
                {feature.title}
              </h3>
              <p className="text-gray-400 leading-relaxed text-sm">
                {feature.description}
              </p>

              {/* Subtle arrow on hover */}
              <div className="mt-6 flex items-center gap-2 text-sm text-gray-500 group-hover:text-purple-400 transition-colors">
                <span>Learn more</span>
                <svg className="w-4 h-4 transform group-hover:translate-x-1 transition-transform" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                </svg>
              </div>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  );
}
