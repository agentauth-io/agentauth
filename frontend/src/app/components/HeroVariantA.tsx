import { useState } from "react";
import { ArrowRight, Check, Loader2 } from "lucide-react";
import { motion } from "motion/react";

/**
 * VARIANT A: Full-screen video background with centered text overlay
 * Style: Cinematic, immersive, Apple product launch feel
 */
export function HeroVariantA() {
  const [email, setEmail] = useState("");
  const [isSubmitted, setIsSubmitted] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState("");

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!email) return;

    setIsLoading(true);
    setError("");

    try {
      const response = await fetch("/.netlify/functions/waitlist", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email }),
      });

      const data = await response.json();

      if (response.ok && data.success) {
        setIsSubmitted(true);
        setEmail("");
        setTimeout(() => setIsSubmitted(false), 5000);
      } else {
        setError(data.error || "Something went wrong. Please try again.");
      }
    } catch {
      setError("Network error. Please try again.");
    } finally {
      setIsLoading(false);
    }
  };

  const navLinks = [
    { href: "/docs", label: "Docs" },
    { href: "/demo", label: "Demo" },
    { href: "#pricing", label: "Pricing" },
    { href: "/contact", label: "Contact" },
  ];

  return (
    <section className="relative min-h-screen flex flex-col overflow-hidden">
      {/* Full-screen Video Background */}
      <div className="absolute inset-0 z-0">
        <video
          autoPlay
          muted
          loop
          playsInline
          className="absolute inset-0 w-full h-full object-cover"
        >
          <source src="/240967.mp4" type="video/mp4" />
        </video>
        {/* Dark overlay for text readability */}
        <div className="absolute inset-0 bg-black/70" />
        {/* Gradient fade at bottom */}
        <div className="absolute bottom-0 left-0 right-0 h-48 bg-gradient-to-t from-black to-transparent" />
      </div>

      {/* Navigation - Floating */}
      <motion.nav
        className="relative z-20 flex items-center justify-between px-6 lg:px-12 py-5"
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.8, delay: 0.2 }}
      >
        <a href="/" className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-lg bg-white flex items-center justify-center">
            <span className="text-black font-semibold text-sm">A</span>
          </div>
          <span className="text-white font-medium text-lg tracking-tight hidden sm:block">
            AgentAuth
          </span>
        </a>

        <div className="hidden md:flex items-center gap-8">
          {navLinks.map((link) => (
            <a
              key={link.href}
              href={link.href}
              className="text-white/70 hover:text-white transition-colors duration-300 text-sm font-medium"
            >
              {link.label}
            </a>
          ))}
        </div>

        <div className="hidden md:flex items-center gap-6">
          <a
            href="/nucleus"
            className="text-white/70 hover:text-white transition-colors duration-300 text-sm font-medium"
          >
            Sign In
          </a>
          <a
            href="/portal"
            className="px-5 py-2 bg-white text-black rounded-full text-sm font-medium hover:bg-white/90 transition-colors duration-300"
          >
            Get Started
          </a>
        </div>

        <a
          href="/portal"
          className="md:hidden px-4 py-2 bg-white text-black rounded-full text-sm font-medium"
        >
          Get Started
        </a>
      </motion.nav>

      {/* Hero Content - Centered over video */}
      <div className="relative z-10 flex-1 flex flex-col items-center justify-center px-6 lg:px-12 pb-32 pt-12">
        <div className="max-w-4xl mx-auto text-center">
          <motion.h1
            className="text-5xl sm:text-6xl md:text-7xl lg:text-8xl font-semibold tracking-tight leading-[0.95] mb-8"
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8, delay: 0.3 }}
          >
            <span className="text-white">Let AI Agents</span>
            <br />
            <span className="text-white/60">Buy For You.</span>
          </motion.h1>

          <motion.p
            className="text-lg md:text-xl text-white/60 max-w-2xl mx-auto mb-12 leading-relaxed font-normal"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8, delay: 0.5 }}
          >
            The authorization layer for AI agent payments. Set spending limits,
            control merchants, and let autonomous systems transact with confidence.
          </motion.p>

          <motion.form
            onSubmit={handleSubmit}
            className="flex flex-col sm:flex-row items-center justify-center gap-3 max-w-md mx-auto mb-8"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8, delay: 0.7 }}
          >
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="Enter your email"
              className="w-full sm:w-auto flex-1 px-5 py-3.5 bg-white/10 backdrop-blur-sm border border-white/20 rounded-full text-white placeholder:text-white/40 focus:outline-none focus:border-white/40 transition-colors duration-300 text-sm"
              required
              disabled={isLoading}
            />
            <motion.button
              type="submit"
              className="w-full sm:w-auto px-8 py-3.5 bg-white hover:bg-white/90 text-black rounded-full transition-colors duration-300 inline-flex items-center justify-center gap-2 font-medium text-sm disabled:opacity-50"
              whileTap={{ scale: 0.98 }}
              disabled={isLoading}
            >
              {isSubmitted ? (
                <>
                  <Check className="w-4 h-4" />
                  You're in
                </>
              ) : isLoading ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  Joining...
                </>
              ) : (
                <>
                  Join Waitlist
                  <ArrowRight className="w-4 h-4" />
                </>
              )}
            </motion.button>
          </motion.form>

          {error && (
            <motion.p
              className="text-red-400 text-sm mb-4"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
            >
              {error}
            </motion.p>
          )}

          <motion.div
            className="flex items-center justify-center gap-6"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ duration: 0.8, delay: 0.9 }}
          >
            <a
              href="/demo"
              className="text-white/80 hover:text-white text-sm font-medium inline-flex items-center gap-1 underline underline-offset-4"
            >
              Try Live Demo
              <ArrowRight className="w-3.5 h-3.5" />
            </a>
          </motion.div>
        </div>
      </div>

      {/* Scroll indicator */}
      <motion.div
        className="absolute bottom-8 left-1/2 -translate-x-1/2 z-10"
        initial={{ opacity: 0 }}
        animate={{ opacity: 1, y: [0, 8, 0] }}
        transition={{ opacity: { delay: 1.2 }, y: { duration: 1.5, repeat: Infinity } }}
      >
        <div className="w-6 h-10 rounded-full border-2 border-white/30 flex items-start justify-center p-2">
          <div className="w-1 h-2 rounded-full bg-white/60" />
        </div>
      </motion.div>
    </section>
  );
}
