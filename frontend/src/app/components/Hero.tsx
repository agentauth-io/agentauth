import { useState } from "react";
import { ArrowRight, Check, Loader2 } from "lucide-react";
import { motion } from "motion/react";

export function Hero() {
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
    <section className="relative min-h-screen flex flex-col">
      {/* Navigation - Minimal Apple Style */}
      <motion.nav
        className="relative z-10 flex items-center justify-between px-6 lg:px-12 py-5"
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
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

        {/* Desktop Navigation */}
        <div className="hidden md:flex items-center gap-8">
          {navLinks.map((link) => (
            <a
              key={link.href}
              href={link.href}
              className="text-[#86868b] hover:text-white transition-colors duration-300 text-sm font-medium"
            >
              {link.label}
            </a>
          ))}
        </div>

        {/* Auth Buttons */}
        <div className="hidden md:flex items-center gap-6">
          <a
            href="/nucleus"
            className="text-[#86868b] hover:text-white transition-colors duration-300 text-sm font-medium"
          >
            Sign In
          </a>
          <a
            href="/portal"
            className="px-5 py-2 bg-white text-black rounded-full text-sm font-medium hover:bg-[#f5f5f7] transition-colors duration-300"
          >
            Get Started
          </a>
        </div>

        {/* Mobile Menu Toggle - simplified */}
        <a
          href="/portal"
          className="md:hidden px-4 py-2 bg-white text-black rounded-full text-sm font-medium"
        >
          Get Started
        </a>
      </motion.nav>

      {/* Hero Content - Centered, Dramatic */}
      <div className="flex-1 flex flex-col items-center justify-center px-6 lg:px-12 pb-24 pt-12">
        <div className="max-w-4xl mx-auto text-center">
          {/* Headline - Apple-scale typography */}
          <motion.h1
            className="text-5xl sm:text-6xl md:text-7xl lg:text-8xl font-semibold tracking-tight leading-[0.95] mb-8"
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8, delay: 0.3 }}
          >
            <span className="text-white">Let AI Agents</span>
            <br />
            <span className="text-[#86868b]">Buy For You.</span>
          </motion.h1>

          {/* Subheadline - Restrained */}
          <motion.p
            className="text-lg md:text-xl text-[#86868b] max-w-2xl mx-auto mb-12 leading-relaxed font-normal"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8, delay: 0.5 }}
          >
            The authorization layer for AI agent payments. Set spending limits,
            control merchants, and let autonomous systems transact with confidence.
          </motion.p>

          {/* CTA - Single Focus */}
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
              className="w-full sm:w-auto flex-1 px-5 py-3.5 bg-[#1d1d1f] border border-[#424245] rounded-full text-white placeholder:text-[#6e6e73] focus:outline-none focus:border-[#86868b] transition-colors duration-300 text-sm"
              required
              disabled={isLoading}
            />
            <motion.button
              type="submit"
              className="w-full sm:w-auto px-8 py-3.5 bg-white hover:bg-[#f5f5f7] text-black rounded-full transition-colors duration-300 inline-flex items-center justify-center gap-2 font-medium text-sm disabled:opacity-50"
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

          {/* Secondary CTA - Subtle */}
          <motion.div
            className="flex items-center justify-center gap-6"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ duration: 0.8, delay: 0.9 }}
          >
            <a
              href="/demo"
              className="text-[#2997ff] hover:underline text-sm font-medium inline-flex items-center gap-1"
            >
              Try Live Demo
              <ArrowRight className="w-3.5 h-3.5" />
            </a>
            <a
              href="/docs"
              className="text-[#2997ff] hover:underline text-sm font-medium inline-flex items-center gap-1"
            >
              Read the Docs
              <ArrowRight className="w-3.5 h-3.5" />
            </a>
          </motion.div>
        </div>

        {/* Code Preview - Clean, Minimal */}
        <motion.div
          className="mt-20 w-full max-w-2xl mx-auto"
          initial={{ opacity: 0, y: 40 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 1, delay: 1 }}
        >
          <div className="relative rounded-2xl border border-[#424245] bg-[#1d1d1f] p-6 overflow-hidden">
            {/* Window Controls */}
            <div className="flex items-center gap-2 mb-5">
              <div className="w-3 h-3 rounded-full bg-[#3a3a3c]" />
              <div className="w-3 h-3 rounded-full bg-[#3a3a3c]" />
              <div className="w-3 h-3 rounded-full bg-[#3a3a3c]" />
            </div>

            <pre className="text-sm text-[#86868b] leading-relaxed font-mono overflow-x-auto">
              <code>
                <span className="text-[#ff7b72]">const</span>{" "}
                <span className="text-[#d2a8ff]">auth</span>{" "}
                <span className="text-white">=</span>{" "}
                <span className="text-[#ff7b72]">await</span>{" "}
                <span className="text-[#79c0ff]">agentauth</span>
                <span className="text-white">.</span>
                <span className="text-[#d2a8ff]">authorize</span>
                <span className="text-white">({"{"}</span>
                {"\n"}
                {"  "}
                <span className="text-[#79c0ff]">agentId</span>
                <span className="text-white">:</span>{" "}
                <span className="text-[#a5d6ff]">"agent_123"</span>
                <span className="text-white">,</span>
                {"\n"}
                {"  "}
                <span className="text-[#79c0ff]">amount</span>
                <span className="text-white">:</span>{" "}
                <span className="text-[#79c0ff]">49.99</span>
                <span className="text-white">,</span>
                {"\n"}
                {"  "}
                <span className="text-[#79c0ff]">merchant</span>
                <span className="text-white">:</span>{" "}
                <span className="text-[#a5d6ff]">"stripe.com"</span>
                {"\n"}
                <span className="text-white">{"})"}</span>
                <span className="text-white">;</span>
                {"\n\n"}
                <span className="text-[#ff7b72]">if</span>{" "}
                <span className="text-white">(</span>
                <span className="text-[#d2a8ff]">auth</span>
                <span className="text-white">.</span>
                <span className="text-[#79c0ff]">approved</span>
                <span className="text-white">)</span>{" "}
                <span className="text-white">{"{"}</span>
                {"\n"}
                {"  "}
                <span className="text-[#8b949e]">// Transaction authorized</span>
                {"\n"}
                <span className="text-white">{"}"}</span>
              </code>
            </pre>

            {/* Subtle approved indicator */}
            <div className="absolute top-6 right-6 px-3 py-1.5 rounded-full bg-[#30d158]/10 border border-[#30d158]/20">
              <span className="text-[#30d158] text-xs font-medium">✓ Approved</span>
            </div>
          </div>
        </motion.div>
      </div>
    </section>
  );
}
