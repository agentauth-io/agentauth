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
    } catch (err) {
      setError("Network error. Please try again.");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <section className="relative px-6 pt-32 pb-24 overflow-hidden">
      {/* Animated grid background */}
      <div className="absolute inset-0 opacity-20">
        <div
          className="absolute inset-0"
          style={{
            backgroundImage: `linear-gradient(to right, rgba(255,255,255,0.05) 1px, transparent 1px),
                            linear-gradient(to bottom, rgba(255,255,255,0.05) 1px, transparent 1px)`,
            backgroundSize: '80px 80px',
          }}
        />
      </div>

      <div className="max-w-6xl mx-auto relative">
        {/* Header Navigation */}
        <motion.nav
          className="flex items-center justify-between mb-20"
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6 }}
        >
          <a href="/">
            <img src="/agentauth-logo-dark.svg" alt="AgentAuth" className="h-8" />
          </a>
          <div className="flex items-center gap-8">
            <a href="/docs" className="text-gray-400 hover:text-white transition-colors">
              Docs
            </a>
            <a href="/demo" className="text-gray-400 hover:text-white transition-colors">
              Demo
            </a>
            <a href="#pricing" className="text-gray-400 hover:text-white transition-colors">
              Pricing
            </a>
          </div>
        </motion.nav>


        <div className="grid lg:grid-cols-2 gap-16 items-center">
          {/* Left Column - Hero Content */}
          <div>
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6, delay: 0.2 }}
            >
              <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full border border-white/20 bg-white/5 mb-8 backdrop-blur-sm">
                <span className="relative flex h-2 w-2">
                  <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-white opacity-75"></span>
                  <span className="relative inline-flex rounded-full h-2 w-2 bg-white"></span>
                </span>
                <span className="text-sm text-gray-300">Now in Private Beta</span>
              </div>
            </motion.div>

            <motion.h1
              className="text-6xl md:text-7xl mb-6 leading-tight"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6, delay: 0.3 }}
            >
              <span className="bg-gradient-to-b from-white to-white/80 bg-clip-text text-transparent">
                Let AI Agents Buy For You
              </span>
              <br />
              <span className="text-white/60">— Safely</span>
            </motion.h1>

            <motion.p
              className="text-xl text-gray-400 mb-4 leading-relaxed"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6, delay: 0.4 }}
            >
              The authorization layer for AI agent payments. Set spending limits,
              control merchants, and let autonomous systems transact with confidence.
            </motion.p>

            <motion.p
              className="text-sm text-gray-500 mb-8"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6, delay: 0.45 }}
            >
              Stripe handles checkout. <span className="text-white/70">AgentAuth handles whether checkout should happen.</span>
            </motion.p>

            <motion.form
              onSubmit={handleSubmit}
              className="flex gap-3 mb-8"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6, delay: 0.5 }}
            >
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="Enter your email"
                className="flex-1 px-6 py-4 bg-white/5 border border-white/10 rounded-lg text-white placeholder:text-gray-500 focus:outline-none focus:border-white/30 backdrop-blur-sm transition-all disabled:opacity-50"
                required
                disabled={isLoading}
              />
              <motion.button
                type="submit"
                className="px-8 py-4 bg-white hover:bg-gray-200 text-black rounded-lg transition-all inline-flex items-center gap-2 whitespace-nowrap disabled:opacity-50 disabled:cursor-not-allowed"
                whileHover={{ scale: isLoading ? 1 : 1.02 }}
                whileTap={{ scale: isLoading ? 1 : 0.98 }}
                disabled={isLoading}
              >
                {isSubmitted ? (
                  <>
                    <Check className="w-5 h-5 text-green-600" />
                    You're in!
                  </>
                ) : isLoading ? (
                  <>
                    <Loader2 className="w-5 h-5 animate-spin" />
                    Joining...
                  </>
                ) : (
                  <>
                    Join Waitlist
                    <ArrowRight className="w-5 h-5" />
                  </>
                )}
              </motion.button>
            </motion.form>

            {/* Demo CTA Button */}
            <motion.div
              className="mb-8"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6, delay: 0.55 }}
            >
              <a
                href="/demo"
                className="inline-flex items-center gap-2 px-6 py-3 bg-gradient-to-r from-purple-500/20 to-cyan-500/20 border border-purple-500/40 text-white rounded-lg hover:from-purple-500/30 hover:to-cyan-500/30 transition-all group"
              >
                <span className="relative flex h-2 w-2">
                  <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-green-400 opacity-75"></span>
                  <span className="relative inline-flex rounded-full h-2 w-2 bg-green-400"></span>
                </span>
                Try Live Demo
                <ArrowRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
              </a>
              <span className="text-gray-500 text-sm ml-3">No signup required</span>
            </motion.div>

            {error && (
              <motion.p
                className="text-red-400 text-sm mb-4"
                initial={{ opacity: 0, y: -10 }}
                animate={{ opacity: 1, y: 0 }}
              >
                {error}
              </motion.p>
            )}

            <motion.p
              className="text-sm text-gray-500"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ duration: 0.6, delay: 0.6 }}
            >
              Join 2,000+ developers building the future of autonomous commerce
            </motion.p>
          </div>

          {/* Right Column - Code Preview */}
          <motion.div
            className="relative"
            initial={{ opacity: 0, x: 40 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.8, delay: 0.4 }}
          >
            <motion.div
              className="relative rounded-2xl border border-white/10 bg-black/40 backdrop-blur-xl p-8 overflow-hidden"
              style={{
                transformStyle: 'preserve-3d',
                perspective: '1000px'
              }}
              whileHover={{
                rotateY: 2,
                rotateX: -2,
                transition: { duration: 0.3 }
              }}
            >
              {/* Glow effect */}
              <div className="absolute inset-0 bg-gradient-to-br from-white/5 via-transparent to-transparent opacity-0 group-hover:opacity-100 transition-opacity" />

              <div className="flex items-center gap-2 mb-6">
                <div className="w-3 h-3 rounded-full bg-white/20" />
                <div className="w-3 h-3 rounded-full bg-white/20" />
                <div className="w-3 h-3 rounded-full bg-white/20" />
              </div>

              <pre className="text-sm text-gray-300 leading-relaxed font-mono">
                <code>
                  {`const auth = await agentauth.authorize({
  agentId: "agent_123",
  amount: 49.99,
  merchant: "stripe.com",
  category: "saas"
});

if (auth.approved) {
  await processPurchase(auth.token);
}`}
                </code>
              </pre>

              {/* Floating badges */}
              <motion.div
                className="absolute -top-4 -right-4 px-4 py-2 rounded-lg bg-white/10 backdrop-blur-sm border border-white/10"
                animate={{
                  y: [0, -10, 0],
                }}
                transition={{
                  duration: 3,
                  repeat: Infinity,
                  ease: "easeInOut"
                }}
              >
                <div className="text-sm text-white">✓ Approved</div>
              </motion.div>
            </motion.div>
          </motion.div>
        </div>
      </div>
    </section>
  );
}