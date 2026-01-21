import { useState, useEffect } from "react";
import { motion } from "motion/react";
import { Shield, Mail, Phone, Loader2, CheckCircle2, AlertCircle, ArrowLeft, ToggleLeft, ToggleRight } from "lucide-react";
import { supabase } from "../../../lib/supabase";

interface SecuritySettingsProps {
    user: { id: string; email: string; phone?: string };
    onBack: () => void;
}

interface SecuritySettings {
    twoFactorEnabled: boolean;
    twoFactorMethod: "email" | "sms" | null;
    phoneNumber: string | null;
    phoneVerified: boolean;
}

export function SecuritySettings({ user, onBack }: SecuritySettingsProps) {
    const [settings, setSettings] = useState<SecuritySettings>({
        twoFactorEnabled: false,
        twoFactorMethod: null,
        phoneNumber: null,
        phoneVerified: false,
    });
    const [isLoading, setIsLoading] = useState(true);
    const [isSaving, setIsSaving] = useState(false);
    const [error, setError] = useState("");
    const [success, setSuccess] = useState("");
    const [showPhoneInput, setShowPhoneInput] = useState(false);
    const [phoneInput, setPhoneInput] = useState("");
    const [showOtpVerify, setShowOtpVerify] = useState(false);
    const [otpCode, setOtpCode] = useState("");
    const [otpSending, setOtpSending] = useState(false);

    useEffect(() => {
        loadSecuritySettings();
    }, [user.id]);

    const loadSecuritySettings = async () => {
        try {
            const { data, error } = await supabase
                .from("user_security_settings")
                .select("*")
                .eq("user_id", user.id)
                .single();

            if (data) {
                setSettings({
                    twoFactorEnabled: data.two_factor_enabled || false,
                    twoFactorMethod: data.two_factor_method || null,
                    phoneNumber: data.phone_number || null,
                    phoneVerified: data.phone_verified || false,
                });
            }
        } catch (err) {
            // No settings yet - that's fine
        }
        setIsLoading(false);
    };

    const toggleTwoFactor = async () => {
        if (!settings.twoFactorEnabled && !settings.twoFactorMethod) {
            // Need to set up 2FA first - default to email
            await updateSettings({ twoFactorEnabled: true, twoFactorMethod: "email" });
        } else {
            await updateSettings({ twoFactorEnabled: !settings.twoFactorEnabled });
        }
    };

    const setTwoFactorMethod = async (method: "email" | "sms") => {
        if (method === "sms" && !settings.phoneVerified) {
            setShowPhoneInput(true);
            return;
        }
        await updateSettings({ twoFactorMethod: method });
    };

    const updateSettings = async (updates: Partial<SecuritySettings>) => {
        setIsSaving(true);
        setError("");
        setSuccess("");

        try {
            const newSettings = { ...settings, ...updates };

            const { error } = await supabase
                .from("user_security_settings")
                .upsert({
                    user_id: user.id,
                    two_factor_enabled: newSettings.twoFactorEnabled,
                    two_factor_method: newSettings.twoFactorMethod,
                    phone_number: newSettings.phoneNumber,
                    phone_verified: newSettings.phoneVerified,
                    updated_at: new Date().toISOString(),
                });

            if (error) throw error;

            setSettings(newSettings);
            setSuccess("Settings updated successfully");
            setTimeout(() => setSuccess(""), 3000);
        } catch (err) {
            setError("Failed to update settings");
        }
        setIsSaving(false);
    };

    const sendPhoneVerification = async () => {
        if (!phoneInput || phoneInput.length < 10) {
            setError("Please enter a valid phone number");
            return;
        }

        setOtpSending(true);
        setError("");

        try {
            const response = await fetch("/.netlify/functions/send-otp", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    phone: phoneInput,
                    method: "sms",
                    userId: user.id,
                }),
            });

            const data = await response.json();

            if (data.success) {
                setShowOtpVerify(true);
                setShowPhoneInput(false);
            } else {
                setError(data.error || "Failed to send verification code");
            }
        } catch (err) {
            setError("Failed to send verification code");
        }
        setOtpSending(false);
    };

    const verifyPhoneOtp = async () => {
        if (otpCode.length !== 6) {
            setError("Please enter the 6-digit code");
            return;
        }

        setOtpSending(true);
        setError("");

        try {
            const response = await fetch("/.netlify/functions/verify-otp", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    code: otpCode,
                    destination: phoneInput,
                    method: "sms",
                    userId: user.id,
                }),
            });

            const data = await response.json();

            if (data.success) {
                await updateSettings({
                    phoneNumber: phoneInput,
                    phoneVerified: true,
                    twoFactorMethod: "sms",
                });
                setShowOtpVerify(false);
                setOtpCode("");
                setPhoneInput("");
            } else {
                setError(data.error || "Invalid verification code");
            }
        } catch (err) {
            setError("Verification failed");
        }
        setOtpSending(false);
    };

    if (isLoading) {
        return (
            <section className="min-h-screen flex items-center justify-center bg-gradient-to-br from-[#0A0A0F] via-[#12121A] to-[#0A0A0F]">
                <div className="text-center">
                    <Loader2 className="w-8 h-8 text-purple-500 animate-spin mx-auto mb-4" />
                    <p className="text-gray-400">Loading security settings...</p>
                </div>
            </section>
        );
    }

    return (
        <section className="min-h-screen px-4 py-12 bg-gradient-to-br from-[#0A0A0F] via-[#12121A] to-[#0A0A0F]">
            <div className="max-w-2xl mx-auto">
                {/* Header */}
                <div className="flex items-center gap-4 mb-8">
                    <button
                        onClick={onBack}
                        className="p-2 text-gray-400 hover:text-white hover:bg-white/10 rounded-xl transition-colors"
                    >
                        <ArrowLeft className="w-5 h-5" />
                    </button>
                    <div>
                        <h1 className="text-3xl font-bold text-white">Security Settings</h1>
                        <p className="text-gray-400">Manage your account security</p>
                    </div>
                </div>

                {/* Alerts */}
                {error && (
                    <motion.div
                        initial={{ opacity: 0, y: -10 }}
                        animate={{ opacity: 1, y: 0 }}
                        className="mb-6 p-4 bg-red-500/10 border border-red-500/20 rounded-xl text-red-400 flex items-center gap-3"
                    >
                        <AlertCircle className="w-5 h-5 flex-shrink-0" />
                        {error}
                    </motion.div>
                )}

                {success && (
                    <motion.div
                        initial={{ opacity: 0, y: -10 }}
                        animate={{ opacity: 1, y: 0 }}
                        className="mb-6 p-4 bg-green-500/10 border border-green-500/20 rounded-xl text-green-400 flex items-center gap-3"
                    >
                        <CheckCircle2 className="w-5 h-5 flex-shrink-0" />
                        {success}
                    </motion.div>
                )}

                {/* Two-Factor Authentication Section */}
                <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    className="bg-gradient-to-br from-white/5 to-white/[0.02] border border-white/10 rounded-2xl p-6 mb-6"
                >
                    <div className="flex items-start justify-between mb-6">
                        <div className="flex items-center gap-3">
                            <div className="w-12 h-12 bg-gradient-to-br from-purple-500/20 to-blue-500/20 border border-purple-500/30 rounded-xl flex items-center justify-center">
                                <Shield className="w-6 h-6 text-purple-400" />
                            </div>
                            <div>
                                <h2 className="text-xl font-semibold text-white">Two-Factor Authentication</h2>
                                <p className="text-gray-400 text-sm">Add an extra layer of security to your account</p>
                            </div>
                        </div>
                        <button
                            onClick={toggleTwoFactor}
                            disabled={isSaving}
                            className="flex items-center gap-2"
                        >
                            {settings.twoFactorEnabled ? (
                                <ToggleRight className="w-10 h-10 text-green-400" />
                            ) : (
                                <ToggleLeft className="w-10 h-10 text-gray-500" />
                            )}
                        </button>
                    </div>

                    {settings.twoFactorEnabled && (
                        <div className="space-y-4 pt-4 border-t border-white/10">
                            <p className="text-gray-400 text-sm">Choose how you want to receive verification codes:</p>

                            {/* Email Option */}
                            <button
                                onClick={() => setTwoFactorMethod("email")}
                                className={`w-full flex items-center gap-4 p-4 rounded-xl border transition-all ${settings.twoFactorMethod === "email"
                                        ? "bg-purple-500/10 border-purple-500/30"
                                        : "bg-white/5 border-white/10 hover:border-white/20"
                                    }`}
                            >
                                <div className={`w-10 h-10 rounded-lg flex items-center justify-center ${settings.twoFactorMethod === "email" ? "bg-purple-500/20" : "bg-white/10"
                                    }`}>
                                    <Mail className={`w-5 h-5 ${settings.twoFactorMethod === "email" ? "text-purple-400" : "text-gray-400"}`} />
                                </div>
                                <div className="text-left flex-1">
                                    <p className={`font-medium ${settings.twoFactorMethod === "email" ? "text-white" : "text-gray-300"}`}>
                                        Email
                                    </p>
                                    <p className="text-gray-500 text-sm">{user.email}</p>
                                </div>
                                {settings.twoFactorMethod === "email" && (
                                    <CheckCircle2 className="w-5 h-5 text-green-400" />
                                )}
                            </button>

                            {/* Phone Option */}
                            <button
                                onClick={() => setTwoFactorMethod("sms")}
                                className={`w-full flex items-center gap-4 p-4 rounded-xl border transition-all ${settings.twoFactorMethod === "sms"
                                        ? "bg-purple-500/10 border-purple-500/30"
                                        : "bg-white/5 border-white/10 hover:border-white/20"
                                    }`}
                            >
                                <div className={`w-10 h-10 rounded-lg flex items-center justify-center ${settings.twoFactorMethod === "sms" ? "bg-purple-500/20" : "bg-white/10"
                                    }`}>
                                    <Phone className={`w-5 h-5 ${settings.twoFactorMethod === "sms" ? "text-purple-400" : "text-gray-400"}`} />
                                </div>
                                <div className="text-left flex-1">
                                    <p className={`font-medium ${settings.twoFactorMethod === "sms" ? "text-white" : "text-gray-300"}`}>
                                        SMS
                                    </p>
                                    <p className="text-gray-500 text-sm">
                                        {settings.phoneVerified ? settings.phoneNumber : "Not configured"}
                                    </p>
                                </div>
                                {settings.twoFactorMethod === "sms" && settings.phoneVerified && (
                                    <CheckCircle2 className="w-5 h-5 text-green-400" />
                                )}
                            </button>
                        </div>
                    )}
                </motion.div>

                {/* Phone Input Modal */}
                {showPhoneInput && (
                    <motion.div
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50 p-4"
                    >
                        <motion.div
                            initial={{ scale: 0.95 }}
                            animate={{ scale: 1 }}
                            className="bg-[#0a0a0f] border border-white/10 rounded-2xl p-6 max-w-md w-full"
                        >
                            <h3 className="text-xl font-semibold text-white mb-4">Add Phone Number</h3>
                            <p className="text-gray-400 text-sm mb-4">
                                Enter your phone number to receive verification codes via SMS.
                            </p>
                            <input
                                type="tel"
                                value={phoneInput}
                                onChange={(e) => setPhoneInput(e.target.value)}
                                placeholder="+1 (555) 000-0000"
                                className="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-3 text-white placeholder-gray-500 focus:border-purple-500 focus:outline-none mb-4"
                            />
                            <div className="flex gap-3">
                                <button
                                    onClick={() => setShowPhoneInput(false)}
                                    className="flex-1 bg-white/5 text-white py-3 rounded-xl hover:bg-white/10 transition-colors"
                                >
                                    Cancel
                                </button>
                                <button
                                    onClick={sendPhoneVerification}
                                    disabled={otpSending}
                                    className="flex-1 bg-gradient-to-r from-purple-600 to-blue-600 text-white py-3 rounded-xl flex items-center justify-center gap-2"
                                >
                                    {otpSending ? <Loader2 className="w-5 h-5 animate-spin" /> : "Send Code"}
                                </button>
                            </div>
                        </motion.div>
                    </motion.div>
                )}

                {/* OTP Verification Modal */}
                {showOtpVerify && (
                    <motion.div
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50 p-4"
                    >
                        <motion.div
                            initial={{ scale: 0.95 }}
                            animate={{ scale: 1 }}
                            className="bg-[#0a0a0f] border border-white/10 rounded-2xl p-6 max-w-md w-full"
                        >
                            <h3 className="text-xl font-semibold text-white mb-4">Verify Phone</h3>
                            <p className="text-gray-400 text-sm mb-4">
                                Enter the 6-digit code sent to {phoneInput}
                            </p>
                            <input
                                type="text"
                                value={otpCode}
                                onChange={(e) => setOtpCode(e.target.value.replace(/\D/g, "").slice(0, 6))}
                                placeholder="000000"
                                className="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-3 text-white text-center text-2xl tracking-widest placeholder-gray-500 focus:border-purple-500 focus:outline-none mb-4"
                            />
                            <div className="flex gap-3">
                                <button
                                    onClick={() => {
                                        setShowOtpVerify(false);
                                        setOtpCode("");
                                    }}
                                    className="flex-1 bg-white/5 text-white py-3 rounded-xl hover:bg-white/10 transition-colors"
                                >
                                    Cancel
                                </button>
                                <button
                                    onClick={verifyPhoneOtp}
                                    disabled={otpSending || otpCode.length !== 6}
                                    className="flex-1 bg-gradient-to-r from-purple-600 to-blue-600 text-white py-3 rounded-xl flex items-center justify-center gap-2 disabled:opacity-50"
                                >
                                    {otpSending ? <Loader2 className="w-5 h-5 animate-spin" /> : "Verify"}
                                </button>
                            </div>
                        </motion.div>
                    </motion.div>
                )}

                {/* Info Card */}
                <div className="bg-gradient-to-br from-blue-500/10 to-purple-500/10 border border-blue-500/20 rounded-2xl p-6">
                    <div className="flex gap-4">
                        <Shield className="w-6 h-6 text-blue-400 flex-shrink-0" />
                        <div>
                            <h3 className="text-white font-medium mb-1">Why use 2FA?</h3>
                            <p className="text-gray-400 text-sm">
                                Two-factor authentication adds an extra layer of security by requiring a verification code
                                in addition to your password. This helps protect your account even if your password is compromised.
                            </p>
                        </div>
                    </div>
                </div>
            </div>
        </section>
    );
}
