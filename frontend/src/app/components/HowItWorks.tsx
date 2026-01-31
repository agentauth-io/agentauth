import { motion } from "motion/react";

const steps = [
  {
    number: "01",
    title: "Connect Your Agent",
    description: "Integrate our SDK with your AI agent in minutes. Simple REST API or Python SDK.",
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
    description: "Payment is processed securely. You get instant webhooks and detailed logs.",
  },
];

const stats = [
  { value: "<100ms", label: "Authorization Time" },
  { value: "99.99%", label: "Uptime SLA" },
  { value: "24/7", label: "Support" },
];

export function HowItWorks() {
  return (
    <section className="px-6 lg:px-12 py-32 lg:py-40 border-t border-[#1d1d1f]">
      <div className="max-w-6xl mx-auto">
        {/* Section Header */}
        <motion.div
          className="text-center max-w-2xl mx-auto mb-24"
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true, margin: "-100px" }}
          transition={{ duration: 0.6 }}
        >
          <h2 className="text-4xl md:text-5xl font-semibold tracking-tight text-white mb-6">
            How It Works
          </h2>
          <p className="text-lg text-[#86868b] leading-relaxed">
            Four simple steps to empower your AI agents.
          </p>
        </motion.div>

        {/* Steps - Horizontal Timeline */}
        <div className="grid md:grid-cols-4 gap-8 lg:gap-12 mb-32">
          {steps.map((step, index) => (
            <motion.div
              key={index}
              className="relative"
              initial={{ opacity: 0, y: 30 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true, margin: "-50px" }}
              transition={{ duration: 0.6, delay: index * 0.1 }}
            >
              {/* Step Number - Large, Faded */}
              <div className="text-6xl lg:text-7xl font-semibold text-[#1d1d1f] mb-6 tracking-tight">
                {step.number}
              </div>
              
              <h3 className="text-lg font-medium text-white mb-2">
                {step.title}
              </h3>
              
              <p className="text-[#86868b] text-sm leading-relaxed">
                {step.description}
              </p>
            </motion.div>
          ))}
        </div>

        {/* Stats - Clean Grid */}
        <motion.div
          className="grid md:grid-cols-3 divide-x divide-[#1d1d1f]"
          initial={{ opacity: 0, y: 30 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true, margin: "-100px" }}
          transition={{ duration: 0.6 }}
        >
          {stats.map((stat, index) => (
            <div key={index} className="text-center py-8 first:pl-0 last:pr-0 px-8">
              <div className="text-4xl md:text-5xl font-semibold text-white tracking-tight mb-2">
                {stat.value}
              </div>
              <div className="text-[#86868b] text-sm">
                {stat.label}
              </div>
            </div>
          ))}
        </motion.div>
      </div>
    </section>
  );
}
