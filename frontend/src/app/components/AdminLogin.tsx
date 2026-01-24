import { useState } from "react";
import { motion } from "motion/react";
import { Lock, Eye, EyeOff, AlertCircle, Loader2 } from "lucide-react";

// Version: 1.0.2 (Cache Busting)
const API_BASE = window.location.hostname === "localhost"
    ? "http://localhost:8000"
    : window.location.origin;

interface AdminLoginProps {
    onLoginSuccess?: (token: string) => void;
    onAuthenticated?: (authenticated: boolean) => void;
    onBack?: () => void;
}

export function AdminLogin({ onLoginSuccess, onAuthenticated, onBack }: AdminLoginProps) {
    const [password, setPassword] = useState("");
    const [showPassword, setShowPassword] = useState(false);
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState("");

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setError("");
        setIsLoading(true);

        try {
            const fetchUrl = `${API_BASE}/.netlify/functions/admin-login`;
            console.log(`Authenticating with: ${fetchUrl}`);

            const response = await fetch(fetchUrl, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                },
                body: JSON.stringify({ password }),
            });

            if (!response.ok) {
                const data = await response.json();
                throw new Error(data.detail || "Authentication failed");
            }

            const data = await response.json();

            // Store token
            localStorage.setItem("admin_token", data.token);
            localStorage.setItem("admin_expires", data.expires_at);

            // Call the appropriate callback
            if (onLoginSuccess) onLoginSuccess(data.token);
            if (onAuthenticated) onAuthenticated(true);
        } catch (err) {
            setError(err instanceof Error ? err.message : "Login failed");
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <div className="min-h-screen flex items-center justify-center px-4">
            <motion.div
                className="w-full max-w-md"
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.4 }}
            >
                {/* Logo/Brand */}
                <div className="text-center mb-8">
                    <motion.div
                        className="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-white/10 mb-4"
                        whileHover={{ scale: 1.05, rotate: 5 }}
                    >
                        <Lock className="w-8 h-8 text-white" />
                    </motion.div>
                    <h1 className="text-2xl font-bold text-white">Nucleus</h1>
                    <p className="text-gray-400 text-sm mt-1">Control Center Access</p>
                </div>

                {/* Login Card */}
                <motion.div
                    className="bg-[#0a0a0f] border border-white/10 rounded-2xl p-8"
                    initial={{ opacity: 0, scale: 0.98 }}
                    animate={{ opacity: 1, scale: 1 }}
                    transition={{ delay: 0.1 }}
                >
                    <form onSubmit={handleSubmit} className="space-y-6">
                        {/* Password Input */}
                        <div>
                            <label className="block text-sm font-medium text-gray-300 mb-2">
                                Access Password
                            </label>
                            <div className="relative">
                                <input
                                    type={showPassword ? "text" : "password"}
                                    value={password}
                                    onChange={(e) => setPassword(e.target.value)}
                                    required
                                    className="w-full px-4 py-3 bg-white/5 border border-white/10 rounded-xl text-white placeholder-gray-500 focus:outline-none focus:border-white/30 transition-colors pr-12"
                                    placeholder="Enter access password"
                                    disabled={isLoading}
                                    autoFocus
                                />
                                <button
                                    type="button"
                                    onClick={() => setShowPassword(!showPassword)}
                                    className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-white transition-colors"
                                >
                                    {showPassword ? (
                                        <EyeOff className="w-5 h-5" />
                                    ) : (
                                        <Eye className="w-5 h-5" />
                                    )}
                                </button>
                            </div>
                        </div>

                        {/* Error Message */}
                        {error && (
                            <motion.div
                                initial={{ opacity: 0, y: -10 }}
                                animate={{ opacity: 1, y: 0 }}
                                className="flex items-center gap-2 p-3 bg-red-500/10 border border-red-500/20 rounded-lg text-red-400 text-sm"
                            >
                                <AlertCircle className="w-4 h-4 flex-shrink-0" />
                                {error}
                            </motion.div>
                        )}

                        {/* Submit Button */}
                        <motion.button
                            type="submit"
                            disabled={isLoading || !password}
                            className="w-full py-3 px-6 bg-white text-black rounded-xl font-semibold hover:bg-gray-100 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
                            whileHover={{ scale: 1.01 }}
                            whileTap={{ scale: 0.99 }}
                        >
                            {isLoading ? (
                                <>
                                    <Loader2 className="w-5 h-5 animate-spin" />
                                    Authenticating...
                                </>
                            ) : (
                                "Access Control Panel"
                            )}
                        </motion.button>
                    </form>

                    {/* Security Note */}
                    <p className="text-center text-gray-500 text-xs mt-6">
                        🔒 Secured with JWT · Session expires in 1 hour
                    </p>
                </motion.div>

                {/* Back Link */}
                <div className="text-center mt-6">
                    <a
                        href="#"
                        className="text-gray-400 hover:text-white text-sm transition-colors"
                    >
                        ← Return to main site
                    </a>
                </div>
            </motion.div>
        </div>
    );
}
