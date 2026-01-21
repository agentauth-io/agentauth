import { Handler, HandlerEvent } from "@netlify/functions";
import { createClient } from "@supabase/supabase-js";

const supabase = createClient(
    process.env.SUPABASE_URL || "",
    process.env.SUPABASE_SERVICE_KEY || ""
);

const handler: Handler = async (event: HandlerEvent) => {
    // CORS headers
    const headers = {
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Headers": "Content-Type",
        "Content-Type": "application/json",
    };

    if (event.httpMethod === "OPTIONS") {
        return { statusCode: 200, headers, body: "" };
    }

    if (event.httpMethod !== "POST") {
        return { statusCode: 405, headers, body: JSON.stringify({ error: "Method not allowed" }) };
    }

    try {
        const { code, destination, method, userId } = JSON.parse(event.body || "{}");

        if (!code || code.length !== 6) {
            return {
                statusCode: 400,
                headers,
                body: JSON.stringify({ error: "Invalid verification code format" }),
            };
        }

        if (!destination) {
            return {
                statusCode: 400,
                headers,
                body: JSON.stringify({ error: "Missing destination" }),
            };
        }

        // Find matching OTP in database
        const { data: otpRecord, error: fetchError } = await supabase
            .from("otp_codes")
            .select("*")
            .eq("code", code)
            .eq("destination", destination)
            .is("used_at", null)
            .gte("expires_at", new Date().toISOString())
            .order("created_at", { ascending: false })
            .limit(1)
            .single();

        if (fetchError || !otpRecord) {
            console.log("OTP verification failed:", fetchError?.message || "No matching OTP found");
            return {
                statusCode: 400,
                headers,
                body: JSON.stringify({
                    success: false,
                    error: "Invalid or expired verification code"
                }),
            };
        }

        // Mark OTP as used
        const { error: updateError } = await supabase
            .from("otp_codes")
            .update({ used_at: new Date().toISOString() })
            .eq("id", otpRecord.id);

        if (updateError) {
            console.error("Error marking OTP as used:", updateError);
        }

        // If userId is provided, update user's 2FA verification status
        if (userId || otpRecord.user_id) {
            const targetUserId = userId || otpRecord.user_id;

            // Update security settings to mark as verified
            await supabase
                .from("user_security_settings")
                .upsert({
                    user_id: targetUserId,
                    two_factor_enabled: true,
                    two_factor_method: method || otpRecord.type,
                    updated_at: new Date().toISOString(),
                });
        }

        // Clean up old/expired OTPs for this destination
        await supabase
            .from("otp_codes")
            .delete()
            .eq("destination", destination)
            .lt("expires_at", new Date().toISOString());

        return {
            statusCode: 200,
            headers,
            body: JSON.stringify({
                success: true,
                message: "Verification successful",
                userId: otpRecord.user_id,
            }),
        };
    } catch (error) {
        console.error("Verify OTP error:", error);
        return {
            statusCode: 500,
            headers,
            body: JSON.stringify({ error: "Internal server error" }),
        };
    }
};

export { handler };
