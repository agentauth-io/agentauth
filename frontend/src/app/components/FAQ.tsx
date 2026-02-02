import { useState } from "react";
import { ChevronDown, HelpCircle } from "lucide-react";
import { motion, AnimatePresence } from "motion/react";

const faqs = [
  {
    question: "What exactly is AgentAuth?",
    answer:
      "AgentAuth is a secure authorization layer for AI agents that need to perform real-world actions like making purchases, signing documents, or accessing sensitive data. We provide cryptographic verification, spending limits, and complete audit trails so businesses can deploy autonomous AI safely.",
  },
  {
    question: "How is this different from regular API authentication?",
    answer:
      "Traditional auth verifies who you are once, then trusts all subsequent actions. AgentAuth continuously validates every AI action against your policies—spending limits, time windows, approved vendors, and more. Every transaction is cryptographically signed with Ed25519 and logged to an immutable audit trail.",
  },
  {
    question: "Which AI frameworks do you support?",
    answer:
      "We have official SDKs for LangChain, LlamaIndex, AutoGPT, CrewAI, and any custom agent framework. Our REST API works with any language or platform. Integration typically takes less than 10 lines of code.",
  },
  {
    question: "What payment providers can AgentAuth authorize?",
    answer:
      "AgentAuth integrates with Stripe, PayPal, Brex, Ramp, Mercury, and major banking APIs. We're also adding crypto wallet support. For enterprise customers, we can build custom integrations with your existing treasury systems.",
  },
  {
    question: "How do you ensure security?",
    answer:
      "Every authorization request is cryptographically signed using Ed25519. We use X25519 for key exchange, support Hardware Security Modules (HSM) for enterprise deployments, and maintain SOC2 Type II compliance. All audit logs are tamper-proof and exportable.",
  },
  {
    question: "What's the latency impact on my AI agents?",
    answer:
      "Our median authorization latency is under 50ms globally. We run on edge infrastructure across 50+ locations. For time-sensitive applications, we offer pre-authorization workflows that validate policies before the AI agent even requests a transaction.",
  },
  {
    question: "Can I set custom spending limits and policies?",
    answer:
      "Absolutely. You can define per-agent limits, per-transaction caps, daily/weekly/monthly budgets, approved vendor lists, time-of-day restrictions, and custom risk scoring rules. Policies can be updated in real-time without redeploying your agents.",
  },
  {
    question: "Is there a free tier?",
    answer:
      "Yes! Our free tier includes 1,000 authorizations per month, core API access, and 7-day audit log retention. It's perfect for prototyping and small projects. No credit card required to start.",
  },
];

interface FAQItemProps {
  question: string;
  answer: string;
  isOpen: boolean;
  onClick: () => void;
  index: number;
}

function FAQItem({ question, answer, isOpen, onClick, index }: FAQItemProps) {
  return (
    <motion.div
      className={`border-b border-white/[0.05] last:border-none ${
        isOpen ? "bg-white/[0.02]" : ""
      }`}
      initial={{ opacity: 0, y: 20 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true }}
      transition={{ duration: 0.5, delay: index * 0.05 }}
    >
      <button
        onClick={onClick}
        className="w-full py-6 px-6 flex items-center justify-between text-left gap-4 hover:bg-white/[0.02] transition-colors"
      >
        <span className="text-white font-medium text-lg">{question}</span>
        <motion.div
          animate={{ rotate: isOpen ? 180 : 0 }}
          transition={{ duration: 0.2 }}
        >
          <ChevronDown className="w-5 h-5 text-gray-500 flex-shrink-0" />
        </motion.div>
      </button>

      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: "auto", opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.3 }}
            className="overflow-hidden"
          >
            <p className="px-6 pb-6 text-gray-400 leading-relaxed">
              {answer}
            </p>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  );
}

export function FAQ() {
  const [openIndex, setOpenIndex] = useState<number | null>(0);

  const handleClick = (index: number) => {
    setOpenIndex(openIndex === index ? null : index);
  };

  return (
    <section id="faq" className="relative px-6 lg:px-12 py-24 lg:py-32 overflow-hidden">
      {/* Background */}
      <div className="absolute inset-0 bg-[#0f0f1a]" />
      
      {/* Decorative gradient */}
      <div className="absolute bottom-0 left-1/2 -translate-x-1/2 w-[800px] h-[400px] bg-gradient-to-t from-purple-600/10 to-transparent blur-3xl" />

      <div className="relative z-10 max-w-3xl mx-auto">
        {/* Section Header */}
        <motion.div
          className="text-center mb-16"
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.6 }}
        >
          <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-white/5 border border-white/10 mb-6">
            <HelpCircle className="w-4 h-4 text-purple-400" />
            <span className="text-sm text-gray-400">FAQ</span>
          </div>
          <h2 className="text-3xl md:text-4xl lg:text-5xl font-bold text-white mb-6">
            Got
            <span className="bg-gradient-to-r from-purple-400 to-blue-400 bg-clip-text text-transparent"> Questions?</span>
          </h2>
          <p className="text-lg text-gray-400 leading-relaxed">
            Everything you need to know about securing your AI agents.
          </p>
        </motion.div>

        {/* FAQ List */}
        <motion.div
          className="rounded-2xl border border-white/[0.05] bg-white/[0.01] overflow-hidden"
          initial={{ opacity: 0, y: 30 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.6, delay: 0.2 }}
        >
          {faqs.map((faq, index) => (
            <FAQItem
              key={index}
              question={faq.question}
              answer={faq.answer}
              isOpen={openIndex === index}
              onClick={() => handleClick(index)}
              index={index}
            />
          ))}
        </motion.div>

        {/* Contact CTA */}
        <motion.div
          className="text-center mt-12"
          initial={{ opacity: 0 }}
          whileInView={{ opacity: 1 }}
          viewport={{ once: true }}
          transition={{ duration: 0.6, delay: 0.4 }}
        >
          <p className="text-gray-400 mb-4">
            Still have questions?
          </p>
          <a
            href="mailto:hello@agentauth.in"
            className="inline-flex items-center gap-2 px-6 py-3 rounded-xl bg-white/5 border border-white/10 text-white font-medium hover:bg-white/10 transition-all"
          >
            Contact Us
          </a>
        </motion.div>
      </div>
    </section>
  );
}
