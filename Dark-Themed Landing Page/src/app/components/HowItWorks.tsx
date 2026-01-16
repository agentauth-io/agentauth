import { ArrowRight } from "lucide-react";
import { motion } from "motion/react";

const steps = [
  {
    number: "01",
    title: "Connect Your Agent",
    description: "Integrate our SDK with your AI agent in minutes. Simple REST API or JavaScript SDK.",
  },
  {
    number: "02",
    title: "Set Spending Rules",
    description: "Define budgets, merchant allowlists, and transaction limits through our dashboard or API.",
  },
  {
    number: "03",
    title: "Agent Makes Purchase",
    description: "Your agent requests authorization. We validate against your rules in real-time.",
  },
  {
    number: "04",
    title: "Transaction Complete",
    description: "Payment is processed securely. You get instant webhooks and detailed transaction logs.",
  },
];

export function HowItWorks() {
  return (
    <section className="relative px-6 py-24">
      <div className="max-w-6xl mx-auto">
        <motion.div 
          className="text-center mb-16"
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.6 }}
        >
          <h2 className="text-4xl mb-4 text-white">How It Works</h2>
          <p className="text-xl text-gray-400">
            Four simple steps to empower your AI agents
          </p>
        </motion.div>

        <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-8">
          {steps.map((step, index) => (
            <motion.div 
              key={index} 
              className="relative"
              initial={{ opacity: 0, x: -30 }}
              whileInView={{ opacity: 1, x: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.6, delay: index * 0.1 }}
            >
              {/* Connector line */}
              {index < steps.length - 1 && (
                <motion.div 
                  className="hidden lg:block absolute top-12 left-full w-full h-[1px] bg-gradient-to-r from-white/20 to-transparent"
                  initial={{ scaleX: 0 }}
                  whileInView={{ scaleX: 1 }}
                  viewport={{ once: true }}
                  transition={{ duration: 0.8, delay: index * 0.2 }}
                  style={{ transformOrigin: 'left' }}
                >
                  <ArrowRight className="absolute right-0 top-1/2 -translate-y-1/2 w-4 h-4 text-white/20" />
                </motion.div>
              )}

              <motion.div 
                className="relative"
                whileHover={{ 
                  y: -5,
                  transition: { duration: 0.3 }
                }}
              >
                <motion.div 
                  className="text-5xl mb-6 bg-gradient-to-b from-white to-white/40 bg-clip-text text-transparent"
                  whileHover={{ 
                    scale: 1.1,
                    transition: { duration: 0.3 }
                  }}
                >
                  {step.number}
                </motion.div>
                <h3 className="text-xl mb-3 text-white">{step.title}</h3>
                <p className="text-gray-400 leading-relaxed">
                  {step.description}
                </p>
              </motion.div>
            </motion.div>
          ))}
        </div>

        {/* Stats */}
        <motion.div 
          className="mt-24 grid md:grid-cols-3 gap-8 p-8 rounded-2xl border border-white/5 bg-white/[0.02] overflow-hidden relative"
          initial={{ opacity: 0, y: 30 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.6 }}
          style={{ transformStyle: 'preserve-3d' }}
          whileHover={{ 
            rotateX: 2,
            transition: { duration: 0.3 }
          }}
        >
          {/* Glow effect */}
          <div className="absolute inset-0 bg-gradient-to-br from-white/5 via-transparent to-transparent opacity-0 hover:opacity-100 transition-opacity duration-500" />

          <motion.div 
            className="text-center relative z-10"
            whileHover={{ scale: 1.05 }}
            transition={{ duration: 0.3 }}
          >
            <motion.div 
              className="text-4xl mb-2 text-white"
              initial={{ scale: 0.8 }}
              whileInView={{ scale: 1 }}
              viewport={{ once: true }}
              transition={{ duration: 0.5, delay: 0.2 }}
            >
              &lt;100ms
            </motion.div>
            <div className="text-gray-400">Authorization Time</div>
          </motion.div>

          <motion.div 
            className="text-center border-l border-r border-white/5 relative z-10"
            whileHover={{ scale: 1.05 }}
            transition={{ duration: 0.3 }}
          >
            <motion.div 
              className="text-4xl mb-2 text-white"
              initial={{ scale: 0.8 }}
              whileInView={{ scale: 1 }}
              viewport={{ once: true }}
              transition={{ duration: 0.5, delay: 0.3 }}
            >
              99.99%
            </motion.div>
            <div className="text-gray-400">Uptime SLA</div>
          </motion.div>

          <motion.div 
            className="text-center relative z-10"
            whileHover={{ scale: 1.05 }}
            transition={{ duration: 0.3 }}
          >
            <motion.div 
              className="text-4xl mb-2 text-white"
              initial={{ scale: 0.8 }}
              whileInView={{ scale: 1 }}
              viewport={{ once: true }}
              transition={{ duration: 0.5, delay: 0.4 }}
            >
              24/7
            </motion.div>
            <div className="text-gray-400">Developer Support</div>
          </motion.div>
        </motion.div>
      </div>
    </section>
  );
}