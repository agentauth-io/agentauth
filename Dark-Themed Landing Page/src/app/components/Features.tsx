import { Shield, Zap, Lock } from "lucide-react";
import { motion } from "motion/react";

const features = [
  {
    icon: Shield,
    title: "Spending Controls",
    description:
      "Set granular budgets, transaction limits, and merchant restrictions. Your agents operate within boundaries you define.",
  },
  {
    icon: Zap,
    title: "Instant Authorization",
    description:
      "Real-time decision making in under 100ms. No delays, no bottlenecks—just fast, secure approvals.",
  },
  {
    icon: Lock,
    title: "Merchant Protection",
    description:
      "Allowlist trusted merchants or block risky ones. Full audit trail and dispute resolution built-in.",
  },
];

const containerVariants = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: {
      staggerChildren: 0.2,
    },
  },
};

const cardVariants = {
  hidden: { opacity: 0, y: 30 },
  visible: {
    opacity: 1,
    y: 0,
    transition: {
      duration: 0.6,
      ease: "easeOut",
    },
  },
};

export function Features() {
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
          <h2 className="text-4xl mb-4 text-white">
            Built for AI-First Commerce
          </h2>
          <p className="text-xl text-gray-400">
            Everything you need to let agents transact safely
          </p>
        </motion.div>

        <motion.div
          className="grid md:grid-cols-3 gap-6"
          variants={containerVariants}
          initial="hidden"
          whileInView="visible"
          viewport={{ once: true }}
        >
          {features.map((feature, index) => {
            const Icon = feature.icon;
            return (
              <motion.div
                key={index}
                variants={cardVariants}
                whileHover={{
                  y: -8,
                  rotateX: 5,
                  transition: { duration: 0.3 },
                }}
                style={{ transformStyle: "preserve-3d" }}
              >
                <motion.div
                  className="relative p-8 rounded-2xl border border-white/10 bg-gradient-to-b from-white/[0.05] to-transparent backdrop-blur-sm overflow-hidden group h-full"
                  whileHover="hover"
                >
                  {/* Animated gradient on hover */}
                  <motion.div
                    className="absolute inset-0 bg-gradient-to-br from-white/10 via-white/5 to-transparent opacity-0"
                    variants={{
                      hover: { opacity: 1 },
                    }}
                    transition={{ duration: 0.3 }}
                  />

                  {/* Glow effect */}
                  <div className="absolute inset-0 opacity-0 group-hover:opacity-100 transition-opacity duration-300">
                    <div className="absolute top-0 left-1/2 -translate-x-1/2 w-3/4 h-1/2 bg-white/5 blur-2xl" />
                  </div>

                  <div className="relative">
                    <motion.div
                      className="inline-flex p-3 rounded-xl bg-white/10 mb-6"
                      whileHover={{
                        scale: 1.1,
                        rotate: 5,
                        transition: { duration: 0.3 },
                      }}
                    >
                      <Icon className="w-6 h-6 text-white" />
                    </motion.div>

                    <h3 className="text-xl mb-3 text-white">{feature.title}</h3>
                    <p className="text-gray-400 leading-relaxed">
                      {feature.description}
                    </p>
                  </div>

                  {/* Bottom accent line */}
                  <motion.div
                    className="absolute bottom-0 left-0 h-[2px] bg-gradient-to-r from-white/50 to-transparent"
                    initial={{ width: 0 }}
                    whileInView={{ width: "100%" }}
                    viewport={{ once: true }}
                    transition={{ duration: 0.8, delay: index * 0.2 }}
                  />
                </motion.div>
              </motion.div>
            );
          })}
        </motion.div>
      </div>
    </section>
  );
}