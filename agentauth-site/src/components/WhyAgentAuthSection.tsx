"use client";

import { motion } from "framer-motion";
import { staggerContainer, staggerItem, viewportOnce } from "@/lib/animations";
import { Shield, Zap, FileText, Lock, Fingerprint, Eye, Server, Globe } from "lucide-react";

/**
 * WhyAgentAuthSection - Premium feature showcase with glassmorphism cards
 */

const features = [
  {
    icon: Zap,
    title: "Real-time Authorization",
    description: "Every transaction evaluated against your policies in under 100 milliseconds. No delays, no bottlenecks.",
    metric: "<100ms",
    gradient: "from-yellow-500/20 to-orange-500/20",
    iconColor: "text-yellow-400",
    borderColor: "border-yellow-500/20",
  },
  {
    icon: Shield,
    title: "Granular Policies",
    description: "Control by agent, merchant, category, time window, or transaction amount. Full programmatic control via API.",
    metric: "Unlimited Rules",
    gradient: "from-emerald-500/20 to-cyan-500/20",
    iconColor: "text-emerald-400",
    borderColor: "border-emerald-500/20",
  },
  {
    icon: FileText,
    title: "Complete Audit Trail",
    description: "Every decision logged with full context. Export anytime for compliance reviews and forensic analysis.",
    metric: "100% Logged",
    gradient: "from-blue-500/20 to-indigo-500/20",
    iconColor: "text-blue-400",
    borderColor: "border-blue-500/20",
  },
  {
    icon: Lock,
    title: "Zero Custody",
    description: "We authorize, you execute. Your funds stay with your payment processor. Zero counterparty risk.",
    metric: "No Risk",
    gradient: "from-purple-500/20 to-pink-500/20",
    iconColor: "text-purple-400",
    borderColor: "border-purple-500/20",
  },
];

export function WhyAgentAuthSection() {
  return (
    <section className="py-32 bg-black relative overflow-hidden">
      {/* Gradient background */}
      <div className="absolute inset-0 bg-gradient-to-t from-zinc-950 via-black to-black" />
      
      <div className="max-w-[1200px] mx-auto px-6 lg:px-8 relative z-10">
        {/* Header */}
        <motion.div
          className="text-center mb-20"
          initial="hidden"
          whileInView="visible"
          viewport={viewportOnce}
          variants={staggerContainer(0.1)}
        >
          <motion.p
            variants={staggerItem}
            className="text-emerald-400 font-medium mb-4 tracking-wide"
          >
            Why AgentAuth
          </motion.p>
          <motion.h2
            variants={staggerItem}
            className="text-4xl lg:text-5xl font-semibold text-white tracking-tight mb-6"
          >
            Built for autonomous agents
          </motion.h2>
          <motion.p
            variants={staggerItem}
            className="text-lg text-zinc-400 max-w-xl mx-auto"
          >
            The authorization layer designed specifically for AI agents making financial decisions.
          </motion.p>
        </motion.div>

        {/* Features grid */}
        <motion.div 
          className="grid md:grid-cols-2 gap-6"
          initial="hidden"
          whileInView="visible"
          viewport={viewportOnce}
          variants={staggerContainer(0.1)}
        >
          {features.map((feature) => (
            <motion.div
              key={feature.title}
              variants={staggerItem}
              className="group relative p-8 rounded-3xl bg-zinc-900/50 backdrop-blur-xl border border-zinc-800/50 hover:border-zinc-700 transition-all duration-500 overflow-hidden"
              whileHover={{ y: -4, transition: { duration: 0.2 } }}
            >
              {/* Gradient background on hover */}
              <div className={`absolute inset-0 bg-gradient-to-br ${feature.gradient} opacity-0 group-hover:opacity-100 transition-opacity duration-500`} />
              
              <div className="relative z-10 flex items-start gap-6">
                {/* Icon */}
                <div className={`flex-shrink-0 w-14 h-14 rounded-2xl bg-zinc-800/80 border ${feature.borderColor} flex items-center justify-center ${feature.iconColor} group-hover:scale-110 transition-transform duration-300`}>
                  <feature.icon className="w-7 h-7" />
                </div>

                {/* Content */}
                <div className="flex-1">
                  <h3 className="text-xl font-semibold text-white mb-3 tracking-tight">
                    {feature.title}
                  </h3>
                  <p className="text-zinc-400 leading-relaxed mb-4">
                    {feature.description}
                  </p>
                  <span className={`inline-flex items-center px-3 py-1.5 rounded-full text-sm font-medium bg-black/30 ${feature.iconColor} border ${feature.borderColor}`}>
                    {feature.metric}
                  </span>
                </div>
              </div>
            </motion.div>
          ))}
        </motion.div>

        {/* Additional trust badges */}
        <motion.div 
          className="mt-16 flex flex-wrap justify-center gap-8"
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={viewportOnce}
          transition={{ delay: 0.4 }}
        >
          {[
            { icon: Globe, label: "Global Coverage" },
            { icon: Server, label: "Multi-Region" },
            { icon: Eye, label: "Real-time Monitoring" },
            { icon: Fingerprint, label: "Biometric Ready" },
          ].map((badge) => (
            <div key={badge.label} className="flex items-center gap-2 text-zinc-500 text-sm">
              <badge.icon className="w-4 h-4 text-emerald-500" />
              <span>{badge.label}</span>
            </div>
          ))}
        </motion.div>
      </div>
    </section>
  );
}
