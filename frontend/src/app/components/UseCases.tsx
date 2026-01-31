import { motion } from "motion/react";

const useCases = [
  {
    title: "E-commerce Agents",
    description: "Let AI assistants purchase products on behalf of users, from comparing prices to completing checkout.",
  },
  {
    title: "Subscription Management",
    description: "Autonomous agents that handle recurring payments, renewals, and service upgrades automatically.",
  },
  {
    title: "Travel Booking",
    description: "AI agents that book flights, hotels, and experiences while staying within budget constraints.",
  },
  {
    title: "Daily Purchases",
    description: "Smart assistants that order coffee, groceries, or meals based on your preferences and schedule.",
  },
];

export function UseCases() {
  return (
    <section className="px-6 lg:px-12 py-32 lg:py-40 border-t border-[#1d1d1f]">
      <div className="max-w-6xl mx-auto">
        {/* Section Header */}
        <motion.div
          className="text-center max-w-2xl mx-auto mb-20"
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true, margin: "-100px" }}
          transition={{ duration: 0.6 }}
        >
          <h2 className="text-4xl md:text-5xl font-semibold tracking-tight text-white mb-6">
            Built for the Future of Commerce
          </h2>
          <p className="text-lg text-[#86868b] leading-relaxed">
            Enable AI agents to handle transactions across any vertical.
          </p>
        </motion.div>

        {/* Use Cases Grid - 2x2 */}
        <div className="grid md:grid-cols-2 gap-8 lg:gap-12">
          {useCases.map((useCase, index) => (
            <motion.div
              key={index}
              className="p-8 lg:p-10 rounded-2xl bg-[#1d1d1f]/50"
              initial={{ opacity: 0, y: 30 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true, margin: "-50px" }}
              transition={{ duration: 0.6, delay: index * 0.1 }}
            >
              <h3 className="text-xl font-medium text-white mb-3">
                {useCase.title}
              </h3>
              <p className="text-[#86868b] leading-relaxed">
                {useCase.description}
              </p>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  );
}
