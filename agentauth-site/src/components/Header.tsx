"use client";

import { motion } from "framer-motion";
import { useState, useEffect } from "react";
import Link from "next/link";

/**
 * Header - Sticky navigation with blur effect
 */

const navLinks = [
  { href: "#how-it-works", label: "How It Works" },
  { href: "#demo", label: "Demo" },
  { href: "#developers", label: "Developers" },
  { href: "/docs", label: "Docs" },
];

export function Header() {
  const [scrolled, setScrolled] = useState(false);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  useEffect(() => {
    const handleScroll = () => {
      setScrolled(window.scrollY > 20);
    };
    window.addEventListener("scroll", handleScroll, { passive: true });
    return () => window.removeEventListener("scroll", handleScroll);
  }, []);

  return (
    <motion.header
      className={`fixed top-0 left-0 right-0 z-50 transition-all duration-300 ${
        scrolled || mobileMenuOpen
          ? "bg-black/95 backdrop-blur-xl border-b border-white/10" 
          : "bg-black/50 backdrop-blur-md md:bg-transparent md:backdrop-blur-none"
      }`}
      initial={{ y: -100 }}
      animate={{ y: 0 }}
      transition={{ duration: 0.6, ease: [0.25, 0.1, 0.25, 1] }}
    >
      <nav className="max-w-[1200px] mx-auto px-6 lg:px-8">
        <div className="flex items-center justify-between h-16 lg:h-20">
          {/* Logo */}
          <Link href="/" className="flex items-center gap-3 group">
            <motion.div 
              className="w-9 h-9 rounded-xl bg-white flex items-center justify-center group-hover:bg-emerald-400 transition-colors duration-200"
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
            >
              <span className="text-black font-bold text-sm">A</span>
            </motion.div>
            <span className="text-white font-semibold text-lg hidden sm:block">
              AgentAuth
            </span>
          </Link>

          {/* Desktop Nav */}
          <div className="hidden md:flex items-center gap-8">
            {navLinks.map((link) => (
              <a
                key={link.href}
                href={link.href}
                className="text-sm text-zinc-400 hover:text-white transition-colors duration-200 font-medium"
              >
                {link.label}
              </a>
            ))}
          </div>

          {/* CTAs */}
          <div className="flex items-center gap-4">
            <a
              href="#waitlist"
              className="hidden sm:inline-flex items-center gap-2 px-5 py-2.5 bg-white text-black font-medium rounded-xl hover:bg-zinc-100 transition-colors duration-200 text-sm"
            >
              Join Waitlist
            </a>

            {/* Mobile menu button */}
            <button
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
              className="md:hidden p-2 text-zinc-400 hover:text-white transition-colors"
            >
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                {mobileMenuOpen ? (
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                ) : (
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
                )}
              </svg>
            </button>
          </div>
        </div>

        {/* Mobile Menu */}
        {mobileMenuOpen && (
          <motion.div
            className="md:hidden py-4 border-t border-white/10 bg-black/95"
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: "auto" }}
            exit={{ opacity: 0, height: 0 }}
          >
            <div className="flex flex-col gap-2">
              {navLinks.map((link) => (
                <a
                  key={link.href}
                  href={link.href}
                  onClick={() => setMobileMenuOpen(false)}
                  className="text-zinc-300 hover:text-white hover:bg-white/5 transition-colors py-3 px-4 rounded-lg"
                >
                  {link.label}
                </a>
              ))}
              <a
                href="#waitlist"
                onClick={() => setMobileMenuOpen(false)}
                className="inline-flex items-center justify-center gap-2 px-5 py-3 bg-white text-black font-medium rounded-xl text-center mt-2"
              >
                Join Waitlist
              </a>
            </div>
          </motion.div>
        )}
      </nav>
    </motion.header>
  );
}
