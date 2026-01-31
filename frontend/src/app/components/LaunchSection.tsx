import { motion } from "motion/react";

export function LaunchSection() {
  return (
    <footer className="px-6 lg:px-12 py-16 border-t border-[#1d1d1f]">
      <div className="max-w-6xl mx-auto">
        {/* Footer Grid */}
        <div className="grid md:grid-cols-4 gap-12 mb-16">
          {/* Brand */}
          <div className="md:col-span-1">
            <a href="/" className="flex items-center gap-3 mb-6">
              <div className="w-8 h-8 rounded-lg bg-white flex items-center justify-center">
                <span className="text-black font-semibold text-sm">A</span>
              </div>
              <span className="text-white font-medium text-lg tracking-tight">
                AgentAuth
              </span>
            </a>
            <p className="text-[#86868b] text-sm leading-relaxed">
              The authorization layer for AI agent payments.
            </p>
          </div>

          {/* Product */}
          <div>
            <h4 className="text-white text-sm font-medium mb-4">Product</h4>
            <ul className="space-y-3">
              <li><a href="/docs" className="text-[#86868b] hover:text-white text-sm transition-colors">Documentation</a></li>
              <li><a href="/demo" className="text-[#86868b] hover:text-white text-sm transition-colors">Demo</a></li>
              <li><a href="#pricing" className="text-[#86868b] hover:text-white text-sm transition-colors">Pricing</a></li>
              <li><a href="/portal" className="text-[#86868b] hover:text-white text-sm transition-colors">Dashboard</a></li>
            </ul>
          </div>

          {/* Company */}
          <div>
            <h4 className="text-white text-sm font-medium mb-4">Company</h4>
            <ul className="space-y-3">
              <li><a href="/contact" className="text-[#86868b] hover:text-white text-sm transition-colors">Contact</a></li>
              <li><a href="mailto:hello@agentauth.in" className="text-[#86868b] hover:text-white text-sm transition-colors">hello@agentauth.in</a></li>
            </ul>
          </div>

          {/* Legal */}
          <div>
            <h4 className="text-white text-sm font-medium mb-4">Legal</h4>
            <ul className="space-y-3">
              <li><a href="#" className="text-[#86868b] hover:text-white text-sm transition-colors">Privacy Policy</a></li>
              <li><a href="#" className="text-[#86868b] hover:text-white text-sm transition-colors">Terms of Service</a></li>
            </ul>
          </div>
        </div>

        {/* Bottom Bar */}
        <motion.div
          className="pt-8 border-t border-[#1d1d1f] flex flex-col sm:flex-row items-center justify-between gap-4"
          initial={{ opacity: 0 }}
          whileInView={{ opacity: 1 }}
          viewport={{ once: true }}
          transition={{ duration: 0.6 }}
        >
          <p className="text-[#86868b] text-sm">
            © {new Date().getFullYear()} AgentAuth. All rights reserved.
          </p>
          <div className="flex items-center gap-6">
            <a href="https://twitter.com" className="text-[#86868b] hover:text-white transition-colors">
              <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
                <path d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-5.214-6.817L4.99 21.75H1.68l7.73-8.835L1.254 2.25H8.08l4.713 6.231zm-1.161 17.52h1.833L7.084 4.126H5.117z"/>
              </svg>
            </a>
            <a href="https://github.com" className="text-[#86868b] hover:text-white transition-colors">
              <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
                <path d="M12 2C6.477 2 2 6.484 2 12.017c0 4.425 2.865 8.18 6.839 9.504.5.092.682-.217.682-.483 0-.237-.008-.868-.013-1.703-2.782.605-3.369-1.343-3.369-1.343-.454-1.158-1.11-1.466-1.11-1.466-.908-.62.069-.608.069-.608 1.003.07 1.531 1.032 1.531 1.032.892 1.53 2.341 1.088 2.91.832.092-.647.35-1.088.636-1.338-2.22-.253-4.555-1.113-4.555-4.951 0-1.093.39-1.988 1.029-2.688-.103-.253-.446-1.272.098-2.65 0 0 .84-.27 2.75 1.026A9.564 9.564 0 0112 6.844c.85.004 1.705.115 2.504.337 1.909-1.296 2.747-1.027 2.747-1.027.546 1.379.202 2.398.1 2.651.64.7 1.028 1.595 1.028 2.688 0 3.848-2.339 4.695-4.566 4.943.359.309.678.92.678 1.855 0 1.338-.012 2.419-.012 2.747 0 .268.18.58.688.482A10.019 10.019 0 0022 12.017C22 6.484 17.522 2 12 2z"/>
              </svg>
            </a>
          </div>
        </motion.div>
      </div>
    </footer>
  );
}
