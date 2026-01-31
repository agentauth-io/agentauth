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
    <section className="px-6 lg:px-12 py-32 lg:py-40 border-t border-[#1d1d1f]">
      <div className="max-w-3xl mx-auto">
        {/* Section Header */}
        <motion.div
          className="text-center mb-16"
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true, margin: "-100px" }}
          transition={{ duration: 0.6 }}
        >
          <h2 className="text-4xl md:text-5xl font-semibold tracking-tight text-white mb-6">
            Frequently Asked Questions
          </h2>
          <p className="text-lg text-[#86868b] leading-relaxed">
            Everything you need to know about AgentAuth.
          </p>
        </motion.div>

        {/* FAQ Items */}
        <div className="divide-y divide-[#1d1d1f]">
          {faqs.map((faq, index) => (
            <motion.div
              key={index}
              initial={{ opacity: 0 }}
              whileInView={{ opacity: 1 }}
              viewport={{ once: true }}
              transition={{ duration: 0.4, delay: index * 0.05 }}
            >
              <button
                onClick={() => toggleQuestion(index)}
                className="w-full py-6 flex items-start justify-between gap-4 text-left"
              >
                <span className="text-lg text-white font-medium pr-8">
                  {faq.question}
                </span>
                <div className="flex-shrink-0 w-6 h-6 flex items-center justify-center text-[#86868b]">
                  {openIndex === index ? (
                    <Minus className="w-5 h-5" />
                  ) : (
                    <Plus className="w-5 h-5" />
                  )}
                </div>
              </button>

              <AnimatePresence>
                {openIndex === index && (
                  <motion.div
                    initial={{ height: 0, opacity: 0 }}
                    animate={{ height: "auto", opacity: 1 }}
                    exit={{ height: 0, opacity: 0 }}
                    transition={{ duration: 0.3, ease: "easeInOut" }}
                    className="overflow-hidden"
                  >
                    <p className="pb-6 text-[#86868b] leading-relaxed pr-12">
                      {faq.answer}
                    </p>
                  </motion.div>
                )}
              </AnimatePresence>
            </motion.div>
          ))}
        </div>

        {/* Contact CTA */}
        <motion.div
          className="mt-16 text-center"
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.6 }}
        >
          <p className="text-[#86868b] mb-4">Still have questions?</p>
          <a
            href="/contact"
            className="text-[#2997ff] hover:underline text-sm font-medium"
          >
            Contact our team →
          </a>
        </motion.div>
      </div>
    </section>
  );
}
