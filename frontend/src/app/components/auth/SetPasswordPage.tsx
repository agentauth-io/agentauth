import { useState, useEffect } from "react";
import { motion } from "motion/react";
import { Lock, Loader2, Eye, EyeOff, CheckCircle2, AlertCircle } from "lucide-react";
import { supabase } from "../../../lib/supabase";

export function SetPasswordPage() {
    const [password, setPassword] = useState("");
    const [confirmPassword, setConfirmPassword] = useState("");
    const [showPassword, setShowPassword] = useState(false);
    const [showConfirmPassword, setShowConfirmPassword] = useState(false);
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState("");
    const [success, setSuccess] = useState(false);
    const [isValidSession, setIsValidSession] = useState<boolean | null>(null);

    useEffect(() => {
        // Check if we have a valid session from the reset link
        const checkSession = async () => {
            const { data: { session } } = await supabase.auth.getSession();

            // Also check for hash parameters (Supabase uses hash for reset tokens)
            const hash = window.location.hash;
            const hasResetToken = hash.includes("type=recovery") || hash.includes("access_token");

            if (session || hasResetToken) {
                setIsValidSession(true);
            } else {
                setIsValidSession(false);
            }
        };

        // Handle the auth callback from Supabase
        supabase.auth.onAuthStateChange((event: string) => {
            if (event === "PASSWORD_RECOVERY") {
                setIsValidSession(true);
            }
        });

        checkSession();
    }, []);

    const validatePassword = (pwd: string): string[] => {
        const errors: string[] = [];
        if (pwd.length < 8) errors.push("At least 8 characters");
        if (!/[A-Z]/.test(pwd)) errors.push("One uppercase letter");
        if (!/[a-z]/.test(pwd)) errors.push("One lowercase letter");
        if (!/[0-9]/.test(pwd)) errors.push("One number");
        return errors;
    };

    const passwordErrors = validatePassword(password);
    const isPasswordValid = passwordErrors.length === 0;
    const passwordsMatch = password === confirmPassword && confirmPassword.length > 0;

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setError("");

        if (!isPasswordValid) {
            setError("Please meet all password requirements");
            return;
        }

        if (!passwordsMatch) {
            setError("Passwords do not match");
            return;
        }

        setIsLoading(true);
        try {
            const { error } = await supabase.auth.updateUser({ password });

            if (error) {
                setError(error.message);
            } else {
                setSuccess(true);
                // Clear URL hash
                window.history.replaceState(null, "", "/set-password");
                // Redirect to portal after 2 seconds
                setTimeout(() => {
                    window.location.href = "/portal";
                }, 2000);
            }
        } catch (err) {
            setError("Failed to update password. Please try again.");
        }
        setIsLoading(false);
    };

    // Loading state while checking session
    if (isValidSession === null) {
        return (
            <section className="min-h-screen flex items-center justify-center bg-gradient-to-br from-[#0A0A0F] via-[#12121A] to-[#0A0A0F]">
                <div className="text-center">
                    <Loader2 className="w-8 h-8 text-purple-500 animate-spin mx-auto mb-4" />
                    <p className="text-gray-400">Verifying reset link...</p>
                </div>
            </section>
        );
    }

    // Invalid or expired link
    if (isValidSession === false) {
        return (
            <section className="min-h-screen flex items-center justify-center px-4 py-12 bg-gradient-to-br from-[#0A0A0F] via-[#12121A] to-[#0A0A0F]">
                <motion.div
                    className="w-full max-w-md text-center"
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                >
                    <div className="bg-gradient-to-br from-red-500/10 to-orange-500/10 border border-red-500/20 rounded-3xl p-8 backdrop-blur-xl">
                        <div className="w-16 h-16 bg-gradient-to-br from-red-500/20 to-orange-500/20 border border-red-500/30 rounded-full flex items-center justify-center mx-auto mb-6">
                            <AlertCircle className="w-8 h-8 text-red-400" />
                        </div>
                        <h2 className="text-2xl font-bold text-white mb-2">Invalid or Expired Link</h2>
                        <p className="text-gray-400 mb-6">
                            This password reset link is invalid or has expired. Please request a new one.
                        </p>
                        <a
                            href="/reset-password"
                            className="inline-block bg-gradient-to-r from-purple-600 to-blue-600 text-white px-6 py-3 rounded-xl font-medium hover:opacity-90 transition-opacity"
                        >
                            Request New Link
                        </a>
                    </div>
                </motion.div>
            </section>
        );
    }

    // Success state
    if (success) {
        return (
            <section className="min-h-screen flex items-center justify-center px-4 py-12 bg-gradient-to-br from-[#0A0A0F] via-[#12121A] to-[#0A0A0F]">
                <motion.div
                    className="w-full max-w-md text-center"
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                >
                    <div className="bg-gradient-to-br from-green-500/10 to-emerald-500/10 border border-green-500/20 rounded-3xl p-8 backdrop-blur-xl">
                        <div className="w-16 h-16 bg-gradient-to-br from-green-500/20 to-emerald-500/20 border border-green-500/30 rounded-full flex items-center justify-center mx-auto mb-6">
                            <CheckCircle2 className="w-8 h-8 text-green-400" />
                        </div>
                        <h2 className="text-2xl font-bold text-white mb-2">Password Updated!</h2>
                        <p className="text-gray-400 mb-4">
                            Your password has been successfully changed.
                        </p>
                        <p className="text-gray-500 text-sm">
                            Redirecting to dashboard...
                        </p>
                    </div>
                </motion.div>
            </section>
        );
    }

    return (
        <section className="min-h-screen flex items-center justify-center px-4 py-12 bg-gradient-to-br from-[#0A0A0F] via-[#12121A] to-[#0A0A0F]">
            <motion.div
                className="w-full max-w-md"
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
            >
                <div className="text-center mb-8">
                    <div className="inline-flex items-center gap-2 px-4 py-2 bg-gradient-to-r from-purple-500/20 to-blue-500/20 border border-purple-500/30 rounded-full mb-4">
                        <Lock className="w-4 h-4 text-purple-400" />
                        <span className="text-purple-300 text-sm font-medium">Set New Password</span>
                    </div>
                    <h1 className="text-3xl font-bold bg-gradient-to-r from-white to-gray-400 bg-clip-text text-transparent mb-2">
                        Create New Password
                    </h1>
                    <p className="text-gray-400">
                        Choose a strong password for your account
                    </p>
                </div>

                <div className="bg-gradient-to-br from-white/5 to-white/[0.02] border border-white/10 rounded-3xl p-8 backdrop-blur-xl shadow-2xl">
                    {error && (
                        <div className="mb-4 p-3 bg-red-500/10 border border-red-500/20 rounded-xl text-red-400 text-sm">
                            ⚠️ {error}
                        </div>
                    )}

                    <form onSubmit={handleSubmit}>
                        <div className="space-y-4">
                            {/* New Password */}
                            <div>
                                <label className="block text-sm text-gray-400 mb-2">New Password</label>
                                <div className="relative">
                                    <input
                                        type={showPassword ? "text" : "password"}
                                        value={password}
                                        onChange={(e) => setPassword(e.target.value)}
                                        className="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-3 text-white placeholder-gray-500 focus:border-purple-500 focus:outline-none transition-colors pr-12"
                                        placeholder="••••••••"
                                        required
                                        autoFocus
                                    />
                                    <button
                                        type="button"
                                        onClick={() => setShowPassword(!showPassword)}
                                        className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-500 hover:text-gray-300 transition-colors"
                                    >
                                        {showPassword ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
                                    </button>
                                </div>

                                {/* Password requirements */}
                                {password.length > 0 && (
                                    <div className="mt-3 space-y-1">
                                        {["At least 8 characters", "One uppercase letter", "One lowercase letter", "One number"].map((req, i) => {
                                            const isMet = !passwordErrors.includes(req);
                                            return (
                                                <div key={i} className={`flex items-center gap-2 text-xs ${isMet ? "text-green-400" : "text-gray-500"}`}>
                                                    {isMet ? <CheckCircle2 className="w-3 h-3" /> : <div className="w-3 h-3 rounded-full border border-gray-500" />}
                                                    {req}
                                                </div>
                                            );
                                        })}
                                    </div>
                                )}
                            </div>

                            {/* Confirm Password */}
                            <div>
                                <label className="block text-sm text-gray-400 mb-2">Confirm Password</label>
                                <div className="relative">
                                    <input
                                        type={showConfirmPassword ? "text" : "password"}
                                        value={confirmPassword}
                                        onChange={(e) => setConfirmPassword(e.target.value)}
                                        className={`w-full bg-white/5 border rounded-xl px-4 py-3 text-white placeholder-gray-500 focus:outline-none transition-colors pr-12 ${confirmPassword.length > 0
                                            ? passwordsMatch
                                                ? "border-green-500/50 focus:border-green-500"
                                                : "border-red-500/50 focus:border-red-500"
                                            : "border-white/10 focus:border-purple-500"
                                            }`}
                                        placeholder="••••••••"
                                        required
                                    />
                                    <button
                                        type="button"
                                        onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                                        className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-500 hover:text-gray-300 transition-colors"
                                    >
                                        {showConfirmPassword ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
                                    </button>
                                </div>
                                {confirmPassword.length > 0 && !passwordsMatch && (
                                    <p className="text-red-400 text-xs mt-1">Passwords do not match</p>
                                )}
                            </div>

                            <button
                                type="submit"
                                disabled={isLoading || !isPasswordValid || !passwordsMatch}
                                className="w-full bg-gradient-to-r from-purple-600 to-blue-600 text-white py-3.5 rounded-xl font-semibold hover:opacity-90 transition-opacity disabled:opacity-50 flex items-center justify-center gap-2"
                            >
                                {isLoading ? (
                                    <Loader2 className="w-5 h-5 animate-spin" />
                                ) : (
                                    <>
                                        <Lock className="w-5 h-5" />
                                        Set New Password
                                    </>
                                )}
                            </button>
                        </div>
                    </form>
                </div>
            </motion.div>
        </section>
    );
}
