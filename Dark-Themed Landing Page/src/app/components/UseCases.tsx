import { ShoppingCart, Calendar, Plane, Coffee } from "lucide-react";
import { motion } from "motion/react";

const useCases = [
  {
    icon: ShoppingCart,
    title: "E-commerce Agents",
    description: "Let AI assistants purchase products on behalf of users, from comparing prices to completing checkout.",
  },
  {
    icon: Calendar,
    title: "Subscription Management",
    description: "Autonomous agents that handle recurring payments, renewals, and service upgrades automatically.",
  },
  {
    icon: Plane,
    title: "Travel Booking",
    description: "AI agents that book flights, hotels, and experiences while staying within budget constraints.",
  },
  {
    icon: Coffee,
    title: "Daily Purchases",
    description: "Smart assistants that order coffee, groceries, or meals based on your preferences and schedule.",
  },
];

export function UseCases() {
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
          <h2 className="text-4xl mb-4 text-white">Built for the Future of Commerce</h2>
          <p className="text-xl text-gray-400 max-w-2xl mx-auto">
            Enable AI agents to handle transactions across any vertical
          </p>
        </motion.div>

        <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6">
          {useCases.map((useCase, index) => {
            const Icon = useCase.icon;
            return (
              <motion.div
                key={index}
                initial={{ opacity: 0, y: 30 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ duration: 0.5, delay: index * 0.1 }}
                whileHover={{ 
                  y: -10,
                  scale: 1.02,
                  transition: { duration: 0.3 }
                }}
              >
                <motion.div
                  className="p-6 rounded-xl border border-white/5 bg-white/[0.02] h-full relative overflow-hidden group"
                  style={{ transformStyle: 'preserve-3d' }}
                  whileHover="hover"
                >
                  {/* Animated background gradient */}
                  <motion.div
                    className="absolute inset-0 bg-gradient-to-br from-white/[0.08] to-transparent opacity-0"
                    variants={{
                      hover: { opacity: 1 }
                    }}
                    transition={{ duration: 0.3 }}
                  />

                  <div className="relative">
                    <motion.div 
                      className="inline-flex p-2.5 rounded-lg bg-white/5 mb-4"
                      whileHover={{ 
                        scale: 1.15,
                        rotate: 10,
                        transition: { duration: 0.3 }
                      }}
                    >
                      <Icon className="w-5 h-5 text-gray-300" />
                    </motion.div>
                    <h3 className="mb-2 text-white">{useCase.title}</h3>
                    <p className="text-sm text-gray-400 leading-relaxed">
                      {useCase.description}
                    </p>
                  </div>

                  {/* Corner accent */}
                  <motion.div
                    className="absolute top-0 right-0 w-20 h-20 bg-white/5 blur-xl"
                    initial={{ opacity: 0 }}
                    variants={{
                      hover: { opacity: 1 }
                    }}
                  />
                </motion.div>
              </motion.div>
            );
          })}
        </div>
      </div>
    </section>
  );
}