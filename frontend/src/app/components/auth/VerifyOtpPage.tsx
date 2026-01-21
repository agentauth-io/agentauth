import { useState, useEffect, useRef } from "react";
import { motion } from "motion/react";
import { Shield, Loader2, ArrowLeft, Mail, Phone, RefreshCw } from "lucide-react";

interface VerifyOtpPageProps {
    email?: string;
    phone?: string;
    method: "email" | "sms";
    onVerified: () => void;
    onBack: () => void;
}

export function VerifyOtpPage({ email, phone, method, onVerified, onBack }: VerifyOtpPageProps) {
    const [otp, setOtp] = useState(["", "", "", "", "", ""]);
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState("");
    const [resendCooldown, setResendCooldown] = useState(0);
    const inputRefs = useRef<(HTMLInputElement | null)[]>([]);

    const destination = method === "email" ? email : phone;
    const maskedDestination = method === "email"
        ? email?.replace(/(.{2})(.*)(@.*)/, "$1***$3")
        : phone?.replace(/(.{3})(.*)(.{2})/, "$1****$3");

    useEffect(() => {
        // Focus first input on mount
        inputRefs.current[0]?.focus();

        // Start resend cooldown
        setResendCooldown(60);
        const timer = setInterval(() => {
            setResendCooldown((prev) => (prev > 0 ? prev - 1 : 0));
        }, 1000);

        return () => clearInterval(timer);
    }, []);

    const handleChange = (index: number, value: string) => {
        if (!/^\d*$/.test(value)) return; // Only allow digits

        const newOtp = [...otp];
        newOtp[index] = value.slice(-1); // Only keep last digit
        setOtp(newOtp);
        setError("");

        // Auto-focus next input
        if (value && index < 5) {
            inputRefs.current[index + 1]?.focus();
        }

        // Auto-submit when all digits entered
        if (newOtp.every((digit) => digit) && newOtp.join("").length === 6) {
            handleVerify(newOtp.join(""));
        }
    };

    const handleKeyDown = (index: number, e: React.KeyboardEvent) => {
        if (e.key === "Backspace" && !otp[index] && index > 0) {
            inputRefs.current[index - 1]?.focus();
        }
    };

    const handlePaste = (e: React.ClipboardEvent) => {
        e.preventDefault();
        const pastedData = e.clipboardData.getData("text").slice(0, 6);
        if (!/^\d+$/.test(pastedData)) return;

        const newOtp = [...otp];
        pastedData.split("").forEach((digit, i) => {
            if (i < 6) newOtp[i] = digit;
        });
        setOtp(newOtp);

        // Focus last filled input or first empty
        const lastIndex = Math.min(pastedData.length - 1, 5);
        inputRefs.current[lastIndex]?.focus();

        // Auto-submit if complete
        if (pastedData.length === 6) {
            handleVerify(pastedData);
        }
    };

    const handleVerify = async (code: string) => {
        setIsLoading(true);
        setError("");

        try {
            const response = await fetch("/.netlify/functions/verify-otp", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    code,
                    destination,
                    method,
                }),
            });

            const data = await response.json();

            if (data.success) {
                onVerified();
            } else {
                setError(data.error || "Invalid verification code");
                setOtp(["", "", "", "", "", ""]);
                inputRefs.current[0]?.focus();
            }
        } catch (err) {
            setError("Verification failed. Please try again.");
        }
        setIsLoading(false);
    };

    const handleResend = async () => {
        if (resendCooldown > 0) return;

        setIsLoading(true);
        setError("");

        try {
            const response = await fetch("/.netlify/functions/send-otp", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    destination,
                    method,
                }),
            });

            const data = await response.json();

            if (data.success) {
                setResendCooldown(60);
                setOtp(["", "", "", "", "", ""]);
                inputRefs.current[0]?.focus();
            } else {
                setError(data.error || "Failed to resend code");
            }
        } catch (err) {
            setError("Failed to resend code. Please try again.");
        }
        setIsLoading(false);
    };

    return (
        <section className="min-h-screen flex items-center justify-center px-4 py-12 bg-gradient-to-br from-[#0A0A0F] via-[#12121A] to-[#0A0A0F]">
            <motion.div
                className="w-full max-w-md"
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
            >
                <div className="text-center mb-8">
                    <div className="inline-flex items-center gap-2 px-4 py-2 bg-gradient-to-r from-purple-500/20 to-blue-500/20 border border-purple-500/30 rounded-full mb-4">
                        <Shield className="w-4 h-4 text-purple-400" />
                        <span className="text-purple-300 text-sm font-medium">Two-Factor Authentication</span>
                    </div>
                    <h1 className="text-3xl font-bold bg-gradient-to-r from-white to-gray-400 bg-clip-text text-transparent mb-2">
                        Enter Verification Code
                    </h1>
                    <p className="text-gray-400">
                        We sent a 6-digit code to{" "}
                        <span className="text-purple-400">{maskedDestination}</span>
                    </p>
                </div>

                <div className="bg-gradient-to-br from-white/5 to-white/[0.02] border border-white/10 rounded-3xl p-8 backdrop-blur-xl shadow-2xl">
                    {error && (
                        <div className="mb-6 p-3 bg-red-500/10 border border-red-500/20 rounded-xl text-red-400 text-sm text-center">
                            ⚠️ {error}
                        </div>
                    )}

                    {/* OTP Input Grid */}
                    <div className="flex justify-center gap-3 mb-6">
                        {otp.map((digit, index) => (
                            <input
                                key={index}
                                ref={(el) => (inputRefs.current[index] = el)}
                                type="text"
                                inputMode="numeric"
                                maxLength={1}
                                value={digit}
                                onChange={(e) => handleChange(index, e.target.value)}
                                onKeyDown={(e) => handleKeyDown(index, e)}
                                onPaste={index === 0 ? handlePaste : undefined}
                                disabled={isLoading}
                                className={`w-12 h-14 text-center text-2xl font-bold bg-white/5 border rounded-xl text-white focus:outline-none transition-all ${digit
                                        ? "border-purple-500/50"
                                        : "border-white/10 focus:border-purple-500"
                                    } disabled:opacity-50`}
                            />
                        ))}
                    </div>

                    {/* Verify Button */}
                    <button
                        onClick={() => handleVerify(otp.join(""))}
                        disabled={isLoading || otp.some((d) => !d)}
                        className="w-full bg-gradient-to-r from-purple-600 to-blue-600 text-white py-3.5 rounded-xl font-semibold hover:opacity-90 transition-opacity disabled:opacity-50 flex items-center justify-center gap-2 mb-4"
                    >
                        {isLoading ? (
                            <Loader2 className="w-5 h-5 animate-spin" />
                        ) : (
                            <>
                                <Shield className="w-5 h-5" />
                                Verify Code
                            </>
                        )}
                    </button>

                    {/* Resend Code */}
                    <div className="text-center">
                        <p className="text-gray-500 text-sm mb-2">Didn't receive the code?</p>
                        <button
                            onClick={handleResend}
                            disabled={resendCooldown > 0 || isLoading}
                            className="inline-flex items-center gap-2 text-purple-400 hover:text-purple-300 disabled:text-gray-500 disabled:cursor-not-allowed transition-colors text-sm"
                        >
                            <RefreshCw className={`w-4 h-4 ${isLoading ? "animate-spin" : ""}`} />
                            {resendCooldown > 0 ? `Resend in ${resendCooldown}s` : "Resend Code"}
                        </button>
                    </div>

                    {/* Method indicator */}
                    <div className="mt-6 pt-6 border-t border-white/10 flex items-center justify-center gap-2 text-gray-500 text-sm">
                        {method === "email" ? (
                            <>
                                <Mail className="w-4 h-4" />
                                Sent via Email
                            </>
                        ) : (
                            <>
                                <Phone className="w-4 h-4" />
                                Sent via SMS
                            </>
                        )}
                    </div>
                </div>

                {/* Back button */}
                <div className="mt-6 text-center">
                    <button
                        onClick={onBack}
                        className="inline-flex items-center gap-2 text-gray-400 hover:text-white transition-colors text-sm"
                    >
                        <ArrowLeft className="w-4 h-4" />
                        Back to Login
                    </button>
                </div>
            </motion.div>
        </section>
    );
}
