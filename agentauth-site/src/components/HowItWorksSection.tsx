"use client";

import { motion } from "framer-motion";
import { staggerContainer, staggerItem, viewportOnce } from "@/lib/animations";
import { Settings, MessageSquare, CheckCircle, ArrowRight } from "lucide-react";

/**
 * HowItWorksSection - Visual step-based flow with connection lines
 */

const steps = [
  {
    number: "01",
    icon: Settings,
    title: "Define Policies",
    description: "Set spending limits, merchant restrictions, and approval thresholds through our intuitive dashboard or API.",
    color: "from-blue-500 to-cyan-500",
  },
  {
    number: "02", 
    icon: MessageSquare,
    title: "Agent Requests",
    description: "Your AI agent calls AgentAuth before any transaction, sending the purchase details for real-time evaluation.",
    color: "from-purple-500 to-pink-500",
  },
  {
    number: "03",
    icon: CheckCircle,
    title: "Instant Decision",
    description: "We return approve or deny in under 100ms. Your agent proceeds or blocks based on the response.",
    color: "from-emerald-500 to-teal-500",
  },
];

export function HowItWorksSection() {
  return (
    <section className="py-32 bg-black relative overflow-hidden" id="how-it-works">
      {/* Background gradient */}
      <div className="absolute inset-0">
        <div className="absolute inset-0 bg-gradient-to-br from-emerald-950/20 via-black to-black" />
        <div className="absolute bottom-0 left-1/4 w-[600px] h-[600px] bg-emerald-500/5 rounded-full blur-[120px]" />
      </div>
      
      <div className="max-w-[1200px] mx-auto px-6 lg:px-8 relative z-10">
        {/* Section header */}
        <motion.div
          className="text-center mb-20"
          initial="hidden"
          whileInView="visible"
          viewport={viewportOnce}
          variants={staggerContainer(0.1)}
        >
          <motion.div
            variants={staggerItem}
            className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-emerald-500/10 border border-emerald-500/20 mb-6"
          >
            <span className="text-emerald-400 font-medium text-sm">How It Works</span>
          </motion.div>
          <motion.h2
            variants={staggerItem}
            className="text-4xl lg:text-5xl font-semibold text-white tracking-tight max-w-2xl mx-auto"
          >
            Simple integration,
            <br />
            <span className="bg-gradient-to-r from-emerald-400 to-cyan-400 bg-clip-text text-transparent">powerful control.</span>
          </motion.h2>
        </motion.div>

        {/* Horizontal steps for larger screens */}
        <motion.div 
          className="hidden lg:grid grid-cols-3 gap-8 mb-20"
          initial="hidden"
          whileInView="visible"
          viewport={viewportOnce}
          variants={staggerContainer(0.2)}
        >
          {steps.map((step, index) => (
            <motion.div
              key={step.number}
              variants={staggerItem}
              className="relative group"
            >
              {/* Connection line */}
              {index < steps.length - 1 && (
                <div className="absolute top-12 left-1/2 w-full h-0.5 bg-gradient-to-r from-zinc-800 to-zinc-800 group-hover:from-emerald-500/50 group-hover:to-zinc-800 transition-all" />
              )}
              
              <div className="relative bg-zinc-900/50 backdrop-blur border border-zinc-800 rounded-3xl p-8 hover:border-zinc-700 transition-all">
                {/* Icon */}
                <div className={`w-16 h-16 rounded-2xl bg-gradient-to-br ${step.color} p-0.5 mb-6`}>
                  <div className="w-full h-full bg-zinc-900 rounded-2xl flex items-center justify-center">
                    <step.icon className="w-7 h-7 text-white" />
                  </div>
                </div>
                
                <span className="text-xs text-zinc-500 font-mono mb-2 block">
                  STEP {step.number}
                </span>
                <h3 className="text-xl font-semibold text-white mb-3 tracking-tight">
                  {step.title}
                </h3>
                <p className="text-zinc-400 text-sm leading-relaxed">
                  {step.description}
                </p>
              </div>
            </motion.div>
          ))}
        </motion.div>

        {/* Vertical steps for mobile */}
        <motion.div 
          className="lg:hidden space-y-6"
          initial="hidden"
          whileInView="visible"
          viewport={viewportOnce}
          variants={staggerContainer(0.15)}
        >
          {steps.map((step, index) => (
            <motion.div
              key={step.number}
              variants={staggerItem}
              className="flex gap-6 items-start"
            >
              <div className={`flex-shrink-0 w-14 h-14 rounded-xl bg-gradient-to-br ${step.color} p-0.5`}>
                <div className="w-full h-full bg-zinc-900 rounded-xl flex items-center justify-center">
                  <step.icon className="w-6 h-6 text-white" />
                </div>
              </div>
              <div className="flex-1">
                <span className="text-xs text-zinc-500 font-mono mb-1 block">STEP {step.number}</span>
                <h3 className="text-lg font-semibold text-white mb-2">{step.title}</h3>
                <p className="text-zinc-400 text-sm leading-relaxed">{step.description}</p>
              </div>
            </motion.div>
          ))}
        </motion.div>

        {/* Bottom metrics */}
        <motion.div 
          className="mt-20 pt-12 border-t border-zinc-800/50 grid grid-cols-3 gap-8"
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={viewportOnce}
          transition={{ delay: 0.3 }}
        >
          {[
            { value: "<100ms", label: "Response time", icon: "⚡" },
            { value: "99.99%", label: "Uptime SLA", icon: "🛡️" },
            { value: "10M+", label: "API calls/day", icon: "📊" },
          ].map((metric) => (
            <div key={metric.label} className="text-center">
              <div className="text-4xl mb-2">{metric.icon}</div>
              <div className="text-2xl lg:text-3xl font-bold text-white mb-1">{metric.value}</div>
              <div className="text-sm text-zinc-500">{metric.label}</div>
            </div>
          ))}
        </motion.div>
      </div>
    </section>
  );
}
