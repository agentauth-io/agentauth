"use client";

import { motion } from "framer-motion";
import { staggerContainer, staggerItem, viewportOnce } from "@/lib/animations";
import { AlertTriangle, TrendingUp, ShieldOff, Bot } from "lucide-react";

/**
 * ProblemSection - Compelling problem statement with visual impact
 */

const problems = [
  {
    stat: "$4.2B",
    icon: TrendingUp,
    label: "Lost to AI fraud yearly",
    description: "Autonomous agents making uncontrolled purchases with no oversight.",
    color: "text-red-400",
  },
  {
    stat: "0%",
    icon: ShieldOff,
    label: "Standard auth coverage",
    description: "Traditional payment systems weren't designed for AI decision-makers.",
    color: "text-orange-400",
  },
  {
    stat: "∞",
    icon: AlertTriangle,
    label: "Liability exposure",
    description: "One rogue agent can drain accounts before anyone notices.",
    color: "text-yellow-400",
  },
];

export function ProblemSection() {
  return (
    <section className="py-32 bg-black relative overflow-hidden">
      {/* Animated background */}
      <div className="absolute inset-0">
        <div className="absolute inset-0 bg-gradient-to-b from-black via-red-950/10 to-black" />
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[800px] h-[800px] bg-red-500/5 rounded-full blur-[150px]" />
      </div>
      
      <div className="max-w-[1200px] mx-auto px-6 lg:px-8 relative z-10">
        <div className="grid lg:grid-cols-2 gap-16 items-center">
          {/* Left: Content */}
          <motion.div
            initial="hidden"
            whileInView="visible"
            viewport={viewportOnce}
            variants={staggerContainer(0.15)}
          >
            <motion.div
              variants={staggerItem}
              className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-red-500/10 border border-red-500/20 mb-6"
            >
              <AlertTriangle className="w-4 h-4 text-red-400" />
              <span className="text-red-400 font-medium text-sm">The Problem</span>
            </motion.div>
            
            <motion.h2
              variants={staggerItem}
              className="text-4xl lg:text-5xl font-semibold text-white tracking-tight mb-6 leading-tight"
            >
              AI agents are spending
              <br />
              <span className="bg-gradient-to-r from-red-400 to-orange-400 bg-clip-text text-transparent">without guardrails.</span>
            </motion.h2>
            
            <motion.p
              variants={staggerItem}
              className="text-lg text-zinc-400 leading-relaxed mb-12"
            >
              Autonomous agents are making purchases, booking services, and executing transactions 
              with no real-time controls. One misconfiguration can mean thousands lost.
            </motion.p>

            {/* Stats with icons */}
            <motion.div 
              className="space-y-6"
              variants={staggerContainer(0.1)}
            >
              {problems.map((problem, index) => (
                <motion.div
                  key={index}
                  variants={staggerItem}
                  className="flex items-start gap-5 p-4 rounded-2xl bg-zinc-900/50 border border-zinc-800/50 hover:border-zinc-700 transition-all group"
                >
                  <div className={`flex-shrink-0 w-12 h-12 rounded-xl bg-zinc-800 flex items-center justify-center ${problem.color}`}>
                    <problem.icon className="w-6 h-6" />
                  </div>
                  <div className="flex-1">
                    <div className="flex items-baseline gap-3 mb-1">
                      <span className={`text-2xl font-bold ${problem.color}`}>
                        {problem.stat}
                      </span>
                      <span className="font-medium text-white">{problem.label}</span>
                    </div>
                    <p className="text-sm text-zinc-500">{problem.description}</p>
                  </div>
                </motion.div>
              ))}
            </motion.div>
          </motion.div>

          {/* Right: Visual representation */}
          <motion.div
            className="relative h-[500px] lg:h-[600px]"
            initial={{ opacity: 0, scale: 0.9 }}
            whileInView={{ opacity: 1, scale: 1 }}
            viewport={viewportOnce}
            transition={{ duration: 0.8 }}
          >
            {/* Abstract danger visualization */}
            <div className="absolute inset-0 flex items-center justify-center">
              <div className="relative w-80 h-80">
                {/* Animated rings */}
                <motion.div 
                  className="absolute inset-0 rounded-full border-2 border-red-500/20"
                  animate={{ scale: [1, 1.2, 1], opacity: [0.5, 0.2, 0.5] }}
                  transition={{ duration: 3, repeat: Infinity }}
                />
                <motion.div 
                  className="absolute inset-8 rounded-full border-2 border-orange-500/30"
                  animate={{ scale: [1, 1.15, 1], opacity: [0.6, 0.3, 0.6] }}
                  transition={{ duration: 2.5, repeat: Infinity, delay: 0.5 }}
                />
                <motion.div 
                  className="absolute inset-16 rounded-full border-2 border-yellow-500/40"
                  animate={{ scale: [1, 1.1, 1], opacity: [0.7, 0.4, 0.7] }}
                  transition={{ duration: 2, repeat: Infinity, delay: 1 }}
                />
                
                {/* Center icon */}
                <div className="absolute inset-0 flex items-center justify-center">
                  <motion.div 
                    className="w-24 h-24 rounded-full bg-gradient-to-br from-red-500/20 to-orange-500/20 border border-red-500/30 flex items-center justify-center"
                    animate={{ boxShadow: ['0 0 40px rgba(239,68,68,0.2)', '0 0 80px rgba(239,68,68,0.4)', '0 0 40px rgba(239,68,68,0.2)'] }}
                    transition={{ duration: 2, repeat: Infinity }}
                  >
                    <Bot className="w-12 h-12 text-red-400" />
                  </motion.div>
                </div>

                {/* Floating warning cards */}
                <motion.div 
                  className="absolute -top-4 -right-8 px-3 py-2 bg-zinc-900/90 backdrop-blur border border-red-500/30 rounded-lg text-xs"
                  animate={{ y: [0, -10, 0] }}
                  transition={{ duration: 3, repeat: Infinity }}
                >
                  <span className="text-red-400">⚠ Unauthorized</span>
                </motion.div>
                
                <motion.div 
                  className="absolute -bottom-4 -left-8 px-3 py-2 bg-zinc-900/90 backdrop-blur border border-orange-500/30 rounded-lg text-xs"
                  animate={{ y: [0, 10, 0] }}
                  transition={{ duration: 2.5, repeat: Infinity, delay: 0.5 }}
                >
                  <span className="text-orange-400">💸 $12,450 spent</span>
                </motion.div>

                <motion.div 
                  className="absolute top-1/2 -right-16 px-3 py-2 bg-zinc-900/90 backdrop-blur border border-yellow-500/30 rounded-lg text-xs"
                  animate={{ x: [0, 5, 0] }}
                  transition={{ duration: 2, repeat: Infinity, delay: 1 }}
                >
                  <span className="text-yellow-400">🤖 No limits set</span>
                </motion.div>
              </div>
            </div>
          </motion.div>
        </div>
      </div>
    </section>
  );
}
