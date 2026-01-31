"use client";

import { motion } from "framer-motion";
import { ArrowRight, Check, Shield, Zap, Lock } from "lucide-react";
import { useState } from "react";
import { staggerContainer, staggerItem } from "@/lib/animations";

/**
 * HeroSection - Premium design with animated gradient background
 */

export function HeroSection() {
  const [email, setEmail] = useState("");
  const [status, setStatus] = useState<"idle" | "loading" | "success" | "error">("idle");

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!email) return;

    setStatus("loading");
    try {
      const response = await fetch("/api/waitlist", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email }),
      });
      if (response.ok) {
        setStatus("success");
        setEmail("");
        setTimeout(() => setStatus("idle"), 5000);
      } else {
        setStatus("error");
      }
    } catch {
      setStatus("error");
    }
  };

  return (
    <section className="relative min-h-screen flex items-center overflow-hidden bg-black">
      {/* Minimalistic video background */}
      <div className="absolute inset-0 -z-10">
        <video
          autoPlay
          loop
          muted
          playsInline
          className="w-full h-full object-cover object-center bg-black"
        >
          <source src="/hero_videos/240967.mp4" type="video/mp4" />
          <source src="/hero_videos/7050-198606709.mp4" type="video/mp4" />
          <source src="/hero-video.mp4" type="video/mp4" />
          <div style={{color: 'white', background: 'red', padding: 16, textAlign: 'center'}}>Video background failed to load.</div>
        </video>
      </div>

      <div className="w-full max-w-[1200px] mx-auto px-6 lg:px-8 py-32 lg:py-40 relative z-10">
        <motion.div 
          className="max-w-3xl mx-auto text-center"
          initial="hidden"
          animate="visible"
          variants={staggerContainer(0.15, 0.2)}
        >
          {/* Eyebrow */}
          <motion.div
            variants={staggerItem}
            className="mb-8"
          >
            <span className="inline-flex items-center gap-2 text-sm text-zinc-300 font-medium backdrop-blur-md bg-white/5 px-5 py-2.5 rounded-full border border-white/10">
              <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
              Now in private beta
            </span>
          </motion.div>

          {/* Headline */}
          <motion.h1
            variants={staggerItem}
            className="text-5xl sm:text-6xl lg:text-7xl font-semibold leading-[1.05] tracking-[-0.03em] text-white mb-8"
          >
            Let AI Agents
            <br />
            <span className="bg-gradient-to-r from-emerald-400 via-cyan-400 to-blue-400 bg-clip-text text-transparent">
              Buy For You
            </span>
          </motion.h1>

          {/* Subheadline */}
          <motion.p
            variants={staggerItem}
            className="text-xl text-zinc-400 leading-relaxed mb-12 max-w-xl mx-auto"
          >
            The authorization layer for AI agent payments. Set limits, control merchants, approve transactions in real-time.
          </motion.p>

          {/* Email Form */}
          <motion.form
            variants={staggerItem}
            onSubmit={handleSubmit}
            className="flex flex-col sm:flex-row gap-3 max-w-md mx-auto mb-8"
          >
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="Enter your email"
              className="flex-1 px-6 py-4 bg-white/5 backdrop-blur-xl border border-white/10 rounded-2xl text-white placeholder:text-zinc-500 focus:outline-none focus:border-emerald-500/50 focus:bg-white/10 transition-all duration-300 text-center sm:text-left"
              required
              disabled={status === "loading"}
            />
            <motion.button
              type="submit"
              className="inline-flex items-center justify-center gap-2 px-8 py-4 bg-gradient-to-r from-emerald-500 to-cyan-500 text-white font-semibold rounded-2xl hover:from-emerald-400 hover:to-cyan-400 transition-all duration-200 disabled:opacity-50 shadow-lg shadow-emerald-500/25"
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
              disabled={status === "loading"}
            >
              {status === "success" ? (
                <>
                  <Check className="w-5 h-5" />
                  You&apos;re in
                </>
              ) : status === "loading" ? (
                "Joining..."
              ) : (
                <>
                  Get Early Access
                  <ArrowRight className="w-5 h-5" />
                </>
              )}
            </motion.button>
          </motion.form>

          {/* Trust indicators */}
          <motion.div
            variants={staggerItem}
            className="flex flex-wrap items-center justify-center gap-6 text-sm text-zinc-500"
          >
            <span className="flex items-center gap-2">
              <Shield className="w-4 h-4 text-emerald-400" />
              SOC 2 Compliant
            </span>
            <span className="flex items-center gap-2">
              <Zap className="w-4 h-4 text-emerald-400" />
              &lt;100ms Latency
            </span>
            <span className="flex items-center gap-2">
              <Lock className="w-4 h-4 text-emerald-400" />
              Zero Custody
            </span>
          </motion.div>
        </motion.div>

        {/* Floating feature cards */}
        <motion.div 
          className="hidden lg:flex absolute top-1/2 -translate-y-1/2 left-8 flex-col gap-4"
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: 1, duration: 0.6 }}
        >
          <div className="px-4 py-3 bg-zinc-900/80 backdrop-blur-xl border border-zinc-800 rounded-xl text-sm">
            <p className="text-emerald-400 font-mono text-xs mb-1">✓ Approved</p>
            <p className="text-white">Amazon • $89.99</p>
          </div>
        </motion.div>

        <motion.div 
          className="hidden lg:flex absolute top-1/2 -translate-y-1/2 right-8 flex-col gap-4"
          initial={{ opacity: 0, x: 20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: 1.2, duration: 0.6 }}
        >
          <div className="px-4 py-3 bg-zinc-900/80 backdrop-blur-xl border border-red-500/30 rounded-xl text-sm">
            <p className="text-red-400 font-mono text-xs mb-1">✗ Denied</p>
            <p className="text-white">Unknown • $2,499</p>
          </div>
        </motion.div>
      </div>

      {/* Scroll indicator */}
      <motion.div 
        className="absolute bottom-8 left-1/2 -translate-x-1/2"
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 1.5 }}
      >
        <motion.div
          className="w-6 h-10 rounded-full border-2 border-white/20 flex items-start justify-center p-2"
          animate={{ y: [0, 8, 0] }}
          transition={{ duration: 1.5, repeat: Infinity }}
        >
          <div className="w-1 h-2 rounded-full bg-emerald-400/60" />
        </motion.div>
      </motion.div>
    </section>
  );
}
