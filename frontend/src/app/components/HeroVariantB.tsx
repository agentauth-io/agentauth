import { useState } from "react";
import { ArrowRight, Check, Loader2 } from "lucide-react";
import { motion } from "motion/react";

/**
 * VARIANT B: Split layout - Left text, Right video in device frame
 * Style: Stripe/Linear, sophisticated, professional
 */
export function HeroVariantB() {
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
    <section className="relative min-h-screen flex flex-col bg-black">
      {/* Navigation */}
      <motion.nav
        className="relative z-20 flex items-center justify-between px-6 lg:px-12 py-5"
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

        <a
          href="/portal"
          className="md:hidden px-4 py-2 bg-white text-black rounded-full text-sm font-medium"
        >
          Get Started
        </a>
      </motion.nav>

      {/* Hero Content - Split Layout */}
      <div className="flex-1 flex items-center px-6 lg:px-12 py-12">
        <div className="max-w-7xl mx-auto w-full grid lg:grid-cols-2 gap-12 lg:gap-20 items-center">
          {/* Left: Text Content */}
          <div>
            <motion.h1
              className="text-4xl sm:text-5xl md:text-6xl lg:text-7xl font-semibold tracking-tight leading-[1.05] mb-6"
              initial={{ opacity: 0, y: 30 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.8, delay: 0.3 }}
            >
              <span className="text-white">Let AI Agents</span>
              <br />
              <span className="text-[#86868b]">Buy For You.</span>
            </motion.h1>

            <motion.p
              className="text-lg text-[#86868b] mb-10 leading-relaxed max-w-lg"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.8, delay: 0.5 }}
            >
              The authorization layer for AI agent payments. Set spending limits,
              control merchants, and let autonomous systems transact with confidence.
            </motion.p>

            <motion.form
              onSubmit={handleSubmit}
              className="flex flex-col sm:flex-row gap-3 max-w-md mb-6"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.8, delay: 0.7 }}
            >
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="Enter your email"
                className="flex-1 px-5 py-3.5 bg-[#1d1d1f] border border-[#424245] rounded-full text-white placeholder:text-[#6e6e73] focus:outline-none focus:border-[#86868b] transition-colors duration-300 text-sm"
                required
                disabled={isLoading}
              />
              <motion.button
                type="submit"
                className="px-8 py-3.5 bg-white hover:bg-[#f5f5f7] text-black rounded-full transition-colors duration-300 inline-flex items-center justify-center gap-2 font-medium text-sm disabled:opacity-50 whitespace-nowrap"
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
              className="flex items-center gap-6"
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

          {/* Right: Video in Device Frame */}
          <motion.div
            className="relative"
            initial={{ opacity: 0, x: 40 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 1, delay: 0.4 }}
          >
            {/* Browser/Device Frame */}
            <div className="relative rounded-2xl overflow-hidden border border-[#2d2d2d] bg-[#1d1d1f] shadow-2xl">
              {/* Browser Chrome */}
              <div className="flex items-center gap-2 px-4 py-3 bg-[#1d1d1f] border-b border-[#2d2d2d]">
                <div className="flex items-center gap-1.5">
                  <div className="w-3 h-3 rounded-full bg-[#ff5f57]" />
                  <div className="w-3 h-3 rounded-full bg-[#febc2e]" />
                  <div className="w-3 h-3 rounded-full bg-[#28c840]" />
                </div>
                <div className="flex-1 flex justify-center">
                  <div className="px-4 py-1 rounded-md bg-[#2d2d2d] text-[#86868b] text-xs font-mono">
                    agentauth.in
                  </div>
                </div>
              </div>

              {/* Video Content */}
              <div className="aspect-video">
                <video
                  autoPlay
                  muted
                  loop
                  playsInline
                  className="w-full h-full object-cover"
                >
                  <source src="/7050-198606709.mp4" type="video/mp4" />
                </video>
              </div>
            </div>

            {/* Floating Stats Card */}
            <motion.div
              className="absolute -bottom-6 -left-6 p-4 rounded-xl bg-[#1d1d1f] border border-[#2d2d2d] shadow-xl"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.8, delay: 1.2 }}
            >
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-full bg-[#30d158]/20 flex items-center justify-center">
                  <Check className="w-5 h-5 text-[#30d158]" />
                </div>
                <div>
                  <div className="text-white font-medium text-sm">Transaction Approved</div>
                  <div className="text-[#86868b] text-xs">$49.99 • amazon.com</div>
                </div>
              </div>
            </motion.div>

            {/* Floating Authorization Card */}
            <motion.div
              className="absolute -top-4 -right-4 p-3 rounded-xl bg-white shadow-xl"
              initial={{ opacity: 0, y: -20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.8, delay: 1.4 }}
            >
              <div className="text-black font-medium text-sm">&lt;100ms</div>
              <div className="text-black/60 text-xs">Auth time</div>
            </motion.div>
          </motion.div>
        </div>
      </div>
    </section>
  );
}
