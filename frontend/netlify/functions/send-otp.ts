import { Handler, HandlerEvent } from "@netlify/functions";
import { createClient } from "@supabase/supabase-js";
import { Resend } from "resend";

const supabase = createClient(
    process.env.SUPABASE_URL || "",
    process.env.SUPABASE_SERVICE_KEY || ""
);

const resend = new Resend(process.env.RESEND_API_KEY);

// Generate a 6-digit OTP
function generateOTP(): string {
    return Math.floor(100000 + Math.random() * 900000).toString();
}

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
        const { email, phone, method, userId } = JSON.parse(event.body || "{}");

        if (!method || (method !== "email" && method !== "sms")) {
            return {
                statusCode: 400,
                headers,
                body: JSON.stringify({ error: "Invalid method. Must be 'email' or 'sms'" }),
            };
        }

        const destination = method === "email" ? email : phone;
        if (!destination) {
            return {
                statusCode: 400,
                headers,
                body: JSON.stringify({ error: `Missing ${method === "email" ? "email" : "phone"} address` }),
            };
        }

        // Generate OTP
        const code = generateOTP();
        const expiresAt = new Date(Date.now() + 10 * 60 * 1000); // 10 minutes

        // Store OTP in database
        const { error: dbError } = await supabase.from("otp_codes").insert({
            user_id: userId || null,
            code,
            type: method,
            destination,
            expires_at: expiresAt.toISOString(),
        });

        if (dbError) {
            console.error("Error storing OTP:", dbError);
            return {
                statusCode: 500,
                headers,
                body: JSON.stringify({ error: "Failed to generate verification code" }),
            };
        }

        // Send OTP via email
        if (method === "email") {
            try {
                await resend.emails.send({
                    from: "AgentAuth <noreply@agentauth.in>",
                    to: email,
                    subject: "Your AgentAuth Verification Code",
                    html: `
<!DOCTYPE html>
<html>
<head>
  <style>
    body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #0a0a0f; color: #ffffff; padding: 40px; }
    .container { max-width: 600px; margin: 0 auto; background: linear-gradient(180deg, rgba(255,255,255,0.08) 0%, rgba(255,255,255,0.02) 100%); border-radius: 16px; padding: 40px; border: 1px solid rgba(255,255,255,0.1); text-align: center; }
    h1 { margin: 0 0 20px 0; font-size: 24px; }
    .code { font-size: 36px; font-weight: bold; letter-spacing: 8px; background: linear-gradient(135deg, #4F46E5 0%, #7C3AED 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; padding: 20px 0; }
    p { color: #a0a0a0; line-height: 1.6; margin: 16px 0; }
    .warning { color: #fbbf24; font-size: 14px; }
    .footer { margin-top: 30px; padding-top: 20px; border-top: 1px solid rgba(255,255,255,0.1); font-size: 12px; color: #666; }
  </style>
</head>
<body>
  <div class="container">
    <h1>Verification Code</h1>
    <p>Use this code to verify your identity on AgentAuth:</p>
    <div class="code">${code}</div>
    <p>This code will expire in <strong>10 minutes</strong>.</p>
    <p class="warning">⚠️ If you didn't request this code, please ignore this email.</p>
    <div class="footer">
      <p>© 2026 AgentAuth. All rights reserved.</p>
    </div>
  </div>
</body>
</html>
          `,
                });
                console.log(`OTP email sent to ${email}`);
            } catch (emailError) {
                console.error("Error sending OTP email:", emailError);
                return {
                    statusCode: 500,
                    headers,
                    body: JSON.stringify({ error: "Failed to send verification email" }),
                };
            }
        }

        // Send OTP via SMS (Twilio)
        if (method === "sms") {
            const twilioSid = process.env.TWILIO_ACCOUNT_SID;
            const twilioToken = process.env.TWILIO_AUTH_TOKEN;
            const twilioPhone = process.env.TWILIO_PHONE_NUMBER;

            if (!twilioSid || !twilioToken || !twilioPhone) {
                return {
                    statusCode: 500,
                    headers,
                    body: JSON.stringify({ error: "SMS service not configured" }),
                };
            }

            try {
                const twilioUrl = `https://api.twilio.com/2010-04-01/Accounts/${twilioSid}/Messages.json`;
                const auth = Buffer.from(`${twilioSid}:${twilioToken}`).toString("base64");

                const response = await fetch(twilioUrl, {
                    method: "POST",
                    headers: {
                        Authorization: `Basic ${auth}`,
                        "Content-Type": "application/x-www-form-urlencoded",
                    },
                    body: new URLSearchParams({
                        From: twilioPhone,
                        To: phone,
                        Body: `Your AgentAuth verification code is: ${code}. Valid for 10 minutes.`,
                    }),
                });

                if (!response.ok) {
                    throw new Error(`Twilio error: ${response.statusText}`);
                }

                console.log(`OTP SMS sent to ${phone}`);
            } catch (smsError) {
                console.error("Error sending OTP SMS:", smsError);
                return {
                    statusCode: 500,
                    headers,
                    body: JSON.stringify({ error: "Failed to send verification SMS" }),
                };
            }
        }

        return {
            statusCode: 200,
            headers,
            body: JSON.stringify({
                success: true,
                message: `Verification code sent via ${method}`,
                expiresAt: expiresAt.toISOString(),
            }),
        };
    } catch (error) {
        console.error("Send OTP error:", error);
        return {
            statusCode: 500,
            headers,
            body: JSON.stringify({ error: "Internal server error" }),
        };
    }
};

export { handler };
