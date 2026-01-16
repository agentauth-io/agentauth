import { Calendar, Users, Rocket } from "lucide-react";
import { motion } from "motion/react";

export function LaunchSection() {
  return (
    <section className="relative px-6 py-32 border-t border-white/5">
      <div className="max-w-5xl mx-auto">
        {/* Launch Announcement */}
        <div className="text-center mb-16">
          <motion.div
            className="inline-flex items-center gap-2 px-4 py-2 rounded-full border border-white/20 bg-white/5 mb-8"
            initial={{ opacity: 0, scale: 0.9 }}
            whileInView={{ opacity: 1, scale: 1 }}
            viewport={{ once: true }}
            transition={{ duration: 0.5 }}
            whileHover={{ scale: 1.05 }}
          >
            <motion.div
              animate={{ rotate: [0, 10, -10, 0] }}
              transition={{ duration: 2, repeat: Infinity, repeatDelay: 3 }}
            >
              <Rocket className="w-4 h-4 text-white" />
            </motion.div>
            <span className="text-sm text-gray-300">Public Beta Launching Soon</span>
          </motion.div>

          <motion.h2
            className="text-5xl md:text-6xl mb-6 bg-gradient-to-b from-white to-white/60 bg-clip-text text-transparent"
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.6, delay: 0.1 }}
          >
            Join the Waitlist
          </motion.h2>

          <motion.p
            className="text-xl text-gray-400 mb-8 max-w-2xl mx-auto"
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.6, delay: 0.2 }}
          >
            Be among the first to access our platform. Early adopters get exclusive benefits and lifetime discounts.
          </motion.p>

          <motion.button
            onClick={() => window.scrollTo({ top: 0, behavior: 'smooth' })}
            className="px-8 py-4 bg-white hover:bg-gray-200 text-black rounded-lg transition-all inline-flex items-center gap-2 text-lg relative overflow-hidden group"
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.6, delay: 0.3 }}
            whileHover={{ scale: 1.05, y: -2 }}
            whileTap={{ scale: 0.98 }}
          >
            {/* Button shimmer effect */}
            <motion.div
              className="absolute inset-0 bg-gradient-to-r from-transparent via-white/20 to-transparent"
              animate={{ x: ["-200%", "200%"] }}
              transition={{ duration: 2, repeat: Infinity, repeatDelay: 1 }}
            />
            <span className="relative">Reserve Your Spot</span>
            <motion.svg
              className="w-5 h-5 relative"
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

        {/* Launch Benefits */}
        <div className="grid md:grid-cols-3 gap-6 mt-20">
          {[
            { icon: Calendar, title: "Early Access", desc: "Get your API keys before the public launch" },
            { icon: Users, title: "Founding Member", desc: "Join our community and shape the product roadmap" },
            {
              icon: () => (
                <svg className="w-6 h-6 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1" />
                </svg>
              ),
              title: "Special Pricing",
              desc: "Lock in discounted rates for the first year"
            }
          ].map((benefit, index) => {
            const Icon = benefit.icon;
            return (
              <motion.div
                key={index}
                className="text-center p-6 relative group"
                initial={{ opacity: 0, y: 30 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ duration: 0.5, delay: index * 0.1 }}
                whileHover={{
                  y: -10,
                  transition: { duration: 0.3 }
                }}
              >
                <motion.div
                  className="inline-flex p-3 rounded-xl bg-white/5 mb-4 relative"
                  whileHover={{
                    scale: 1.15,
                    rotate: 10,
                    backgroundColor: "rgba(255, 255, 255, 0.1)",
                    transition: { duration: 0.3 }
                  }}
                >
                  <Icon />

                  {/* Glow effect */}
                  <motion.div
                    className="absolute inset-0 bg-white/20 rounded-xl blur-xl"
                    initial={{ opacity: 0 }}
                    whileHover={{ opacity: 1 }}
                    transition={{ duration: 0.3 }}
                  />
                </motion.div>
                <h3 className="text-lg mb-2 text-white">{benefit.title}</h3>
                <p className="text-sm text-gray-400">{benefit.desc}</p>
              </motion.div>
            );
          })}
        </div>

        {/* Footer */}
        <motion.div
          className="mt-20 pt-12 border-t border-white/5 text-center text-sm text-gray-500"
          initial={{ opacity: 0 }}
          whileInView={{ opacity: 1 }}
          viewport={{ once: true }}
          transition={{ duration: 0.6, delay: 0.4 }}
        >
          <p>© 2026 AgentAuth, Inc. All rights reserved.</p>
        </motion.div>
      </div>
    </section>
  );
}