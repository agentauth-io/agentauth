import { motion } from "motion/react";

// Partner/Integration logos - using text placeholders since we don't have actual logos
const partners = [
  { name: "OpenAI", category: "AI" },
  { name: "Anthropic", category: "AI" },
  { name: "LangChain", category: "Framework" },
  { name: "Stripe", category: "Payments" },
  { name: "AWS", category: "Cloud" },
  { name: "Vercel", category: "Platform" },
];

export function TrustLogos() {
  return (
    <section className="relative py-16 px-6 lg:px-12 overflow-hidden">
      {/* Background */}
      <div className="absolute inset-0 bg-[#0f0f1a]" />

      <div className="relative z-10 max-w-6xl mx-auto">
        {/* Header */}
        <motion.p
          className="text-center text-gray-500 text-sm mb-10"
          initial={{ opacity: 0 }}
          whileInView={{ opacity: 1 }}
          viewport={{ once: true }}
          transition={{ duration: 0.6 }}
        >
          Trusted by teams building with leading AI platforms
        </motion.p>

        {/* Logo Grid */}
        <motion.div
          className="flex flex-wrap items-center justify-center gap-x-12 gap-y-8"
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.6, delay: 0.1 }}
        >
          {partners.map((partner, index) => (
            <motion.div
              key={partner.name}
              className="group flex items-center gap-2 px-4 py-2 rounded-lg hover:bg-white/5 transition-colors cursor-pointer"
              initial={{ opacity: 0, y: 10 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.4, delay: 0.1 + index * 0.05 }}
            >
              {/* Placeholder logo */}
              <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-white/10 to-white/5 flex items-center justify-center">
                <span className="text-white/60 text-xs font-bold">
                  {partner.name.charAt(0)}
                </span>
              </div>
              <span className="text-gray-500 group-hover:text-gray-300 font-medium text-sm transition-colors">
                {partner.name}
              </span>
            </motion.div>
          ))}
        </motion.div>

        {/* Divider line */}
        <div className="mt-16 h-px bg-gradient-to-r from-transparent via-white/10 to-transparent" />
      </div>
    </section>
  );
}
