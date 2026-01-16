import { motion } from "motion/react";
import { Shield, Zap, Lock, Code } from "lucide-react";

const features = [
  {
    icon: Shield,
    title: "Human-in-the-Loop",
    description: "Every transaction requires cryptographic proof that a real person authorized the purchase.",
  },
  {
    icon: Zap,
    title: "Instant Decisions",
    description: "Sub-100ms authorization responses. Your AI agents never wait.",
  },
  {
    icon: Lock,
    title: "Spending Controls",
    description: "Set limits by amount, merchant category, or time period. You stay in control.",
  },
  {
    icon: Code,
    title: "Developer First",
    description: "Python SDK, REST API, and LangChain integration. Ship in minutes, not weeks.",
  },
];

export function Testimonials() {
  return (
    <section className="relative px-6 py-24 border-t border-white/5">
      <div className="max-w-6xl mx-auto">
        <motion.div
          className="text-center mb-16"
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.6 }}
        >
          <h2 className="text-4xl mb-4 text-white">Why AgentAuth?</h2>
          <p className="text-xl text-gray-400">
            Built for the AI commerce era
          </p>
        </motion.div>

        <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6">
          {features.map((feature, index) => (
            <motion.div
              key={index}
              initial={{ opacity: 0, y: 30 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.6, delay: index * 0.1 }}
              whileHover={{
                y: -10,
                transition: { duration: 0.3 }
              }}
            >
              <motion.div
                className="relative p-8 rounded-xl border border-white/5 bg-white/[0.02] h-full overflow-hidden group"
                whileHover="hover"
              >
                {/* Glow effect on hover */}
                <motion.div
                  className="absolute inset-0 bg-gradient-to-br from-white/10 via-transparent to-transparent opacity-0"
                  variants={{
                    hover: { opacity: 1 }
                  }}
                  transition={{ duration: 0.3 }}
                />

                <div className="relative">
                  <motion.div
                    className="mb-6 w-12 h-12 rounded-lg bg-white/10 flex items-center justify-center"
                    whileHover={{ scale: 1.1, rotate: 5, transition: { duration: 0.3 } }}
                  >
                    <feature.icon className="w-6 h-6 text-white" />
                  </motion.div>
                  <h3 className="text-xl text-white mb-3">{feature.title}</h3>
                  <p className="text-gray-400 leading-relaxed">
                    {feature.description}
                  </p>
                </div>

                {/* Corner glow */}
                <motion.div
                  className="absolute bottom-0 right-0 w-24 h-24 bg-white/5 blur-2xl"
                  initial={{ opacity: 0 }}
                  variants={{
                    hover: { opacity: 1 }
                  }}
                />
              </motion.div>
            </motion.div>
          ))}
        </div>

        {/* Final CTA */}
        <motion.div
          className="mt-24 text-center p-12 rounded-2xl border border-white/10 bg-gradient-to-b from-white/[0.05] to-transparent overflow-hidden relative"
          initial={{ opacity: 0, scale: 0.95 }}
          whileInView={{ opacity: 1, scale: 1 }}
          viewport={{ once: true }}
          transition={{ duration: 0.6 }}
          style={{ transformStyle: 'preserve-3d' }}
          whileHover={{
            scale: 1.02,
            transition: { duration: 0.3 }
          }}
        >
          {/* Animated gradient background */}
          <motion.div
            className="absolute inset-0 bg-gradient-to-br from-white/10 via-transparent to-transparent"
            animate={{
              opacity: [0.3, 0.6, 0.3],
            }}
            transition={{
              duration: 3,
              repeat: Infinity,
              ease: "easeInOut"
            }}
          />

          <div className="relative">
            <h2 className="text-3xl mb-4 text-white">Ready to Get Started?</h2>
            <p className="text-xl text-gray-400 mb-8 max-w-2xl mx-auto">
              Join the waitlist and be among the first to give your AI agents the power to transact safely.
            </p>
            <motion.button
              onClick={() => window.scrollTo({ top: 0, behavior: 'smooth' })}
              className="px-8 py-4 bg-white hover:bg-gray-200 text-black rounded-lg transition-all inline-flex items-center gap-2"
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
            >
              Join the Waitlist
              <motion.svg
                className="w-5 h-5"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
                animate={{ x: [0, 5, 0] }}
                transition={{ duration: 1.5, repeat: Infinity }}
              >
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7l5 5m0 0l-5 5m5-5H6" />
              </motion.svg>
            </motion.button>
          </div>
        </motion.div>
      </div>
    </section>
  );
}