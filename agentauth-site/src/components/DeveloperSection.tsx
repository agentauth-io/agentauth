"use client";

import { motion } from "framer-motion";
import { ArrowRight, Terminal, Copy, Check, Code2, Cpu, Zap, Globe } from "lucide-react";
import { staggerContainer, staggerItem, viewportOnce } from "@/lib/animations";
import { useState } from "react";

/**
 * DeveloperSection - Premium developer experience with live code preview
 */

const codeSnippet = `import { AgentAuth } from '@agentauth/sdk';

const auth = new AgentAuth({ apiKey: process.env.AGENTAUTH_KEY });

// Authorize any AI agent transaction
const result = await auth.authorize({
  agent: 'shopping-assistant',
  merchant: 'amazon.com',
  amount: 149.99,
  currency: 'USD'
});

if (result.approved) {
  await processPayment(result.token);
}`;

export function DeveloperSection() {
  const [copied, setCopied] = useState(false);

  const handleCopy = () => {
    navigator.clipboard.writeText(codeSnippet);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <section className="py-32 bg-black relative overflow-hidden" id="developers">
      {/* Background gradient */}
      <div className="absolute inset-0 bg-[radial-gradient(ellipse_60%_50%_at_50%_100%,rgba(16,185,129,0.08),transparent)]" />
      
      <div className="max-w-[1200px] mx-auto px-6 lg:px-8 relative z-10">
        <div className="grid lg:grid-cols-2 gap-16 items-center">
          {/* Left: Code Editor */}
          <motion.div
            className="relative order-2 lg:order-1"
            initial={{ opacity: 0, x: -40 }}
            whileInView={{ opacity: 1, x: 0 }}
            viewport={viewportOnce}
            transition={{ duration: 0.8 }}
          >
            {/* Code window */}
            <div className="rounded-2xl bg-zinc-950 border border-zinc-800 overflow-hidden shadow-2xl shadow-black/50">
              {/* Window header */}
              <div className="flex items-center justify-between px-4 py-3 bg-zinc-900/80 border-b border-zinc-800">
                <div className="flex items-center gap-2">
                  <div className="w-3 h-3 rounded-full bg-red-500/80" />
                  <div className="w-3 h-3 rounded-full bg-yellow-500/80" />
                  <div className="w-3 h-3 rounded-full bg-green-500/80" />
                </div>
                <div className="flex items-center gap-2 text-xs text-zinc-500">
                  <Terminal className="w-3.5 h-3.5" />
                  <span>authorize.ts</span>
                </div>
                <button
                  onClick={handleCopy}
                  className="flex items-center gap-1.5 text-xs text-zinc-500 hover:text-white transition-colors px-2 py-1 rounded hover:bg-white/5"
                >
                  {copied ? (
                    <><Check className="w-3.5 h-3.5 text-emerald-400" /><span className="text-emerald-400">Copied</span></>
                  ) : (
                    <><Copy className="w-3.5 h-3.5" /><span>Copy</span></>
                  )}
                </button>
              </div>
              {/* Code content */}
              <div className="p-6 font-mono text-sm leading-relaxed overflow-x-auto">
                <pre className="text-zinc-300">
                  <code>
                    <span className="text-purple-400">import</span> <span className="text-zinc-100">{'{'} AgentAuth {'}'}</span> <span className="text-purple-400">from</span> <span className="text-emerald-400">&apos;@agentauth/sdk&apos;</span>;
                    {"\n\n"}
                    <span className="text-purple-400">const</span> <span className="text-blue-400">auth</span> = <span className="text-purple-400">new</span> <span className="text-yellow-300">AgentAuth</span>({'{'} <span className="text-zinc-100">apiKey:</span> process.env.<span className="text-orange-400">AGENTAUTH_KEY</span> {'}'});
                    {"\n\n"}
                    <span className="text-zinc-600">// Authorize any AI agent transaction</span>
                    {"\n"}
                    <span className="text-purple-400">const</span> <span className="text-blue-400">result</span> = <span className="text-purple-400">await</span> auth.<span className="text-yellow-300">authorize</span>({'{'}{
                      "\n"}
                    {'  '}<span className="text-zinc-100">agent:</span> <span className="text-emerald-400">&apos;shopping-assistant&apos;</span>,{"\n"}
                    {'  '}<span className="text-zinc-100">merchant:</span> <span className="text-emerald-400">&apos;amazon.com&apos;</span>,{"\n"}
                    {'  '}<span className="text-zinc-100">amount:</span> <span className="text-orange-400">149.99</span>,{"\n"}
                    {'  '}<span className="text-zinc-100">currency:</span> <span className="text-emerald-400">&apos;USD&apos;</span>{"\n"}
                    {'}'});
                    {"\n\n"}
                    <span className="text-purple-400">if</span> (result.<span className="text-blue-400">approved</span>) {'{'}{"\n"}
                    {'  '}<span className="text-purple-400">await</span> <span className="text-yellow-300">processPayment</span>(result.<span className="text-blue-400">token</span>);{"\n"}
                    {'}'}
                  </code>
                </pre>
              </div>
            </div>

            {/* Floating badges */}
            <motion.div 
              className="absolute -top-4 -right-4 px-3 py-1.5 bg-emerald-500/10 border border-emerald-500/30 rounded-full text-xs text-emerald-400 font-medium backdrop-blur-sm"
              initial={{ opacity: 0, scale: 0.8 }}
              whileInView={{ opacity: 1, scale: 1 }}
              transition={{ delay: 0.5 }}
            >
              TypeScript Ready
            </motion.div>
          </motion.div>

          {/* Right: Content */}
          <motion.div
            className="order-1 lg:order-2"
            initial="hidden"
            whileInView="visible"
            viewport={viewportOnce}
            variants={staggerContainer(0.15)}
          >
            <motion.div
              variants={staggerItem}
              className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-emerald-500/10 border border-emerald-500/20 mb-6"
            >
              <Code2 className="w-4 h-4 text-emerald-400" />
              <span className="text-emerald-400 font-medium text-sm">For Developers</span>
            </motion.div>
            
            <motion.h2
              variants={staggerItem}
              className="text-4xl lg:text-5xl font-semibold text-white tracking-tight mb-6 leading-tight"
            >
              Ship in minutes,
              <br />
              <span className="text-zinc-500">not weeks.</span>
            </motion.h2>
            
            <motion.p
              variants={staggerItem}
              className="text-lg text-zinc-400 leading-relaxed mb-8"
            >
              First-class SDKs for Python, TypeScript, and Go. RESTful API with OpenAPI spec. 
              Comprehensive docs to get you from zero to production in under an hour.
            </motion.p>

            {/* SDK badges */}
            <motion.div 
              variants={staggerItem}
              className="flex flex-wrap gap-3 mb-8"
            >
              {[
                { name: "Python", icon: "🐍" },
                { name: "TypeScript", icon: "📘" },
                { name: "Go", icon: "🔷" },
                { name: "REST API", icon: "🔌" },
              ].map((sdk) => (
                <span key={sdk.name} className="inline-flex items-center gap-2 px-4 py-2 bg-zinc-900 border border-zinc-800 rounded-xl text-sm text-zinc-300">
                  <span>{sdk.icon}</span>
                  {sdk.name}
                </span>
              ))}
            </motion.div>

            {/* Stats grid */}
            <motion.div 
              variants={staggerItem}
              className="grid grid-cols-3 gap-4 mb-10"
            >
              {[
                { icon: Zap, value: "<100ms", label: "Latency" },
                { icon: Globe, value: "99.99%", label: "Uptime" },
                { icon: Cpu, value: "<1hr", label: "Integration" },
              ].map((stat) => (
                <div key={stat.label} className="text-center p-4 rounded-xl bg-zinc-900/30 border border-zinc-800/50">
                  <stat.icon className="w-5 h-5 text-emerald-400 mx-auto mb-2" />
                  <p className="text-xl font-bold text-white">{stat.value}</p>
                  <p className="text-xs text-zinc-500">{stat.label}</p>
                </div>
              ))}
            </motion.div>

            {/* CTAs */}
            <motion.div variants={staggerItem} className="flex flex-wrap gap-4">
              <motion.a
                href="/docs"
                className="inline-flex items-center gap-2 px-8 py-4 bg-white text-black font-semibold rounded-2xl hover:bg-zinc-100 transition-all"
                whileHover={{ scale: 1.02 }}
                whileTap={{ scale: 0.98 }}
              >
                Read the Docs
                <ArrowRight className="w-5 h-5" />
              </motion.a>
              <motion.a
                href="https://github.com/agentauth-io/agentauth"
                className="inline-flex items-center gap-2 px-8 py-4 text-white font-semibold rounded-2xl border border-zinc-700 hover:border-zinc-500 hover:bg-white/5 transition-all"
                whileHover={{ scale: 1.02 }}
                whileTap={{ scale: 0.98 }}
              >
                <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24"><path d="M12 0C5.37 0 0 5.37 0 12c0 5.31 3.435 9.795 8.205 11.385.6.105.825-.255.825-.57 0-.285-.015-1.23-.015-2.235-3.015.555-3.795-.735-4.035-1.41-.135-.345-.72-1.41-1.23-1.695-.42-.225-1.02-.78-.015-.795.945-.015 1.62.87 1.845 1.23 1.08 1.815 2.805 1.305 3.495.99.105-.78.42-1.305.765-1.605-2.67-.3-5.46-1.335-5.46-5.925 0-1.305.465-2.385 1.23-3.225-.12-.3-.54-1.53.12-3.18 0 0 1.005-.315 3.3 1.23.96-.27 1.98-.405 3-.405s2.04.135 3 .405c2.295-1.56 3.3-1.23 3.3-1.23.66 1.65.24 2.88.12 3.18.765.84 1.23 1.905 1.23 3.225 0 4.605-2.805 5.625-5.475 5.925.435.375.81 1.095.81 2.22 0 1.605-.015 2.895-.015 3.3 0 .315.225.69.825.57A12.02 12.02 0 0024 12c0-6.63-5.37-12-12-12z"/></svg>
                View on GitHub
              </motion.a>
            </motion.div>
          </motion.div>
        </div>
      </div>
    </section>
  );
}
