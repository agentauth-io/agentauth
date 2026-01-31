import { motion } from "motion/react";
import { ArrowRight } from "lucide-react";

const features = [
  {
    title: "Human-in-the-Loop",
    description: "Every transaction requires cryptographic proof that a real person authorized the purchase.",
  },
  {
    title: "Instant Decisions",
    description: "Sub-100ms authorization responses. Your AI agents never wait.",
  },
  {
    title: "Spending Controls",
    description: "Set limits by amount, merchant category, or time period. You stay in control.",
  },
  {
    title: "Developer First",
    description: "Python SDK, REST API, and LangChain integration. Ship in minutes, not weeks.",
  },
];

export function Testimonials() {
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
            Why AgentAuth?
          </h2>
          <p className="text-lg text-[#86868b] leading-relaxed">
            Built for the AI commerce era.
          </p>
        </motion.div>

        {/* Features Grid - 2x2 */}
        <div className="grid md:grid-cols-2 gap-x-16 gap-y-12 lg:gap-y-16 mb-24">
          {features.map((feature, index) => (
            <motion.div
              key={index}
              className="border-l-2 border-[#1d1d1f] pl-6"
              initial={{ opacity: 0, x: -20 }}
              whileInView={{ opacity: 1, x: 0 }}
              viewport={{ once: true, margin: "-50px" }}
              transition={{ duration: 0.6, delay: index * 0.1 }}
            >
              <h3 className="text-xl font-medium text-white mb-2">
                {feature.title}
              </h3>
              <p className="text-[#86868b] leading-relaxed">
                {feature.description}
              </p>
            </motion.div>
          ))}
        </div>

        {/* Final CTA */}
        <motion.div
          className="text-center"
          initial={{ opacity: 0, y: 30 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true, margin: "-100px" }}
          transition={{ duration: 0.6 }}
        >
          <h3 className="text-3xl md:text-4xl font-semibold tracking-tight text-white mb-6">
            Ready to empower your AI agents?
          </h3>
          <p className="text-lg text-[#86868b] max-w-xl mx-auto mb-10">
            Join thousands of developers building the future of autonomous commerce.
          </p>
          <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
            <a
              href="/portal"
              className="px-8 py-3.5 bg-white hover:bg-[#f5f5f7] text-black rounded-full transition-colors duration-300 font-medium text-sm inline-flex items-center gap-2"
            >
              Get Started Free
              <ArrowRight className="w-4 h-4" />
            </a>
            <a
              href="/docs"
              className="px-8 py-3.5 border border-[#424245] hover:border-[#86868b] text-white rounded-full transition-colors duration-300 font-medium text-sm"
            >
              Read the Docs
            </a>
          </div>
        </motion.div>
      </div>
    </section>
  );
}
