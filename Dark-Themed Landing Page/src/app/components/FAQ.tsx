import { useState } from "react";
import { Plus, Minus } from "lucide-react";
import { motion, AnimatePresence } from "motion/react";

const faqs = [
  {
    question: "How does AgentAuth ensure transaction security?",
    answer: "AgentAuth uses bank-grade encryption, multi-factor verification, and real-time fraud detection. Every transaction is validated against your custom spending rules before authorization. We're SOC 2 compliant and maintain PCI DSS standards.",
  },
  {
    question: "Can I set limits on what my AI agent can purchase?",
    answer: "Absolutely. You have granular control over spending limits, merchant allowlists/blocklists, transaction frequency, and category restrictions. Set daily, weekly, or monthly budgets that automatically reset.",
  },
  {
    question: "What happens if an agent tries to exceed its limits?",
    answer: "The transaction is immediately declined, and you receive a webhook notification. Your agent gets a clear error response explaining why the authorization failed, allowing it to adjust or seek user approval.",
  },
  {
    question: "How fast are authorization responses?",
    answer: "Authorization decisions are made in under 100ms on average. Our infrastructure is built for real-time AI agent interactions with sub-second latency globally.",
  },
  {
    question: "Which payment methods are supported?",
    answer: "We support all major credit cards, debit cards, and ACH transfers. Support for cryptocurrency and international payment methods is coming soon.",
  },
  {
    question: "Is there a test environment for development?",
    answer: "Yes! Every account includes a full-featured sandbox environment with test cards and mock merchants. Build and test your integration without processing real transactions.",
  },
];

export function FAQ() {
  const [openIndex, setOpenIndex] = useState<number | null>(0);

  const toggleQuestion = (index: number) => {
    setOpenIndex(openIndex === index ? null : index);
  };

  return (
    <section className="relative px-6 py-24 border-t border-white/5">
      <div className="max-w-3xl mx-auto">
        <motion.div 
          className="text-center mb-16"
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.6 }}
        >
          <h2 className="text-4xl mb-4 text-white">Frequently Asked Questions</h2>
          <p className="text-xl text-gray-400">
            Everything you need to know about AgentAuth
          </p>
        </motion.div>

        <div className="space-y-4">
          {faqs.map((faq, index) => (
            <motion.div
              key={index}
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.5, delay: index * 0.05 }}
            >
              <motion.div
                className="border border-white/5 rounded-xl bg-white/[0.02] overflow-hidden transition-all"
                whileHover={{ 
                  borderColor: "rgba(255, 255, 255, 0.1)",
                  transition: { duration: 0.2 }
                }}
              >
                <motion.button
                  onClick={() => toggleQuestion(index)}
                  className="w-full p-6 flex items-start justify-between gap-4 text-left hover:bg-white/[0.02] transition-all"
                  whileTap={{ scale: 0.99 }}
                >
                  <span className="text-lg text-white pr-8">{faq.question}</span>
                  <motion.div 
                    className="flex-shrink-0 w-6 h-6 rounded-full bg-white/5 flex items-center justify-center"
                    animate={{ 
                      rotate: openIndex === index ? 180 : 0,
                      backgroundColor: openIndex === index ? "rgba(255, 255, 255, 0.1)" : "rgba(255, 255, 255, 0.05)"
                    }}
                    transition={{ duration: 0.3 }}
                  >
                    {openIndex === index ? (
                      <Minus className="w-4 h-4 text-white" />
                    ) : (
                      <Plus className="w-4 h-4 text-white" />
                    )}
                  </motion.div>
                </motion.button>
                
                <AnimatePresence>
                  {openIndex === index && (
                    <motion.div
                      initial={{ height: 0, opacity: 0 }}
                      animate={{ height: "auto", opacity: 1 }}
                      exit={{ height: 0, opacity: 0 }}
                      transition={{ duration: 0.3, ease: "easeInOut" }}
                    >
                      <div className="px-6 pb-6 pt-0">
                        <motion.p 
                          className="text-gray-400 leading-relaxed"
                          initial={{ y: -10 }}
                          animate={{ y: 0 }}
                          transition={{ duration: 0.3 }}
                        >
                          {faq.answer}
                        </motion.p>
                      </div>
                    </motion.div>
                  )}
                </AnimatePresence>
              </motion.div>
            </motion.div>
          ))}
        </div>

        <motion.div 
          className="mt-12 text-center p-8 rounded-xl border border-white/5 bg-white/[0.02] relative overflow-hidden group"
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.6 }}
          whileHover={{ scale: 1.02 }}
        >
          <motion.div
            className="absolute inset-0 bg-gradient-to-br from-white/5 via-transparent to-transparent opacity-0"
            whileHover={{ opacity: 1 }}
            transition={{ duration: 0.3 }}
          />
          
          <div className="relative">
            <p className="text-gray-400 mb-4">Still have questions?</p>
            <motion.a
              href="#"
              className="inline-flex items-center gap-2 text-white hover:text-gray-300 transition-colors"
              whileHover={{ x: 5 }}
            >
              Contact our team
              <motion.svg 
                className="w-4 h-4" 
                fill="none" 
                viewBox="0 0 24 24" 
                stroke="currentColor"
                animate={{ x: [0, 3, 0] }}
                transition={{ duration: 1.5, repeat: Infinity }}
              >
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
              </motion.svg>
            </motion.a>
          </div>
        </motion.div>
      </div>
    </section>
  );
}