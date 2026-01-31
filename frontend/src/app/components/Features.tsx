import { motion } from "motion/react";

const features = [
  {
    title: "Spending Controls",
    description:
      "Set granular budgets, transaction limits, and merchant restrictions. Your agents operate within boundaries you define.",
  },
  {
    title: "Instant Authorization",
    description:
      "Real-time decision making in under 100ms. No delays, no bottlenecks — just fast, secure approvals.",
  },
  {
    title: "Merchant Protection",
    description:
      "Allowlist trusted merchants or block risky ones. Full audit trail and dispute resolution built-in.",
  },
];

export function Features() {
  return (
    <section className="px-6 lg:px-12 py-32 lg:py-40">
      <div className="max-w-6xl mx-auto">
        {/* Section Header */}
        <motion.div
          className="max-w-xl mb-20"
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true, margin: "-100px" }}
          transition={{ duration: 0.6 }}
        >
          <h2 className="text-4xl md:text-5xl font-semibold tracking-tight text-white mb-6">
            Built for AI-First Commerce
          </h2>
          <p className="text-lg text-[#86868b] leading-relaxed">
            Everything you need to let agents transact safely.
          </p>
        </motion.div>

        {/* Feature Grid - Simple, Clean */}
        <div className="grid md:grid-cols-3 gap-12 lg:gap-16">
          {features.map((feature, index) => (
            <motion.div
              key={index}
              initial={{ opacity: 0, y: 30 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true, margin: "-50px" }}
              transition={{ duration: 0.6, delay: index * 0.1 }}
            >
              {/* Number indicator - subtle */}
              <div className="text-[#3a3a3c] text-sm font-medium mb-4 tabular-nums">
                0{index + 1}
              </div>
              
              <h3 className="text-xl font-medium text-white mb-3">
                {feature.title}
              </h3>
              
              <p className="text-[#86868b] leading-relaxed">
                {feature.description}
              </p>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  );
}
