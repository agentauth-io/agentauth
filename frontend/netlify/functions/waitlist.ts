import type { Handler, HandlerEvent, HandlerContext } from "@netlify/functions";
import { createClient } from "@supabase/supabase-js";

// Environment variables
const RESEND_API_KEY = process.env.RESEND_API_KEY || "";
const SUPABASE_URL = process.env.SUPABASE_URL || process.env.VITE_SUPABASE_URL || "";
const SUPABASE_SERVICE_KEY = process.env.SUPABASE_SERVICE_ROLE_KEY || "";

// Create Supabase client with service role for server-side operations
const supabase = SUPABASE_URL && SUPABASE_SERVICE_KEY
  ? createClient(SUPABASE_URL, SUPABASE_SERVICE_KEY)
  : null;

interface WaitlistRequest {
  email: string;
  name?: string;
}

// Send "Thank you for joining" email (NOT beta access yet)
const sendWaitlistConfirmationEmail = async (email: string, position?: number): Promise<boolean> => {
  if (!RESEND_API_KEY) {
    console.log("RESEND_API_KEY not set, skipping email send");
    return false;
  }

  const emailHtml = `
<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
</head>
<body style="margin: 0; padding: 0; background-color: #08080a; font-family: 'Segoe UI', -apple-system, BlinkMacSystemFont, Roboto, Helvetica, Arial, sans-serif;">
  <table width="100%" cellpadding="0" cellspacing="0" style="background-color: #08080a; padding: 48px 20px;">
    <tr>
      <td align="center">
        <table width="560" cellpadding="0" cellspacing="0" style="background: #0d0d12; border-radius: 16px; border: 1px solid rgba(255,255,255,0.06);">
          
          <!-- Header -->
          <tr>
            <td style="padding: 28px 36px 20px 36px; border-bottom: 1px solid rgba(255,255,255,0.04);">
              <table width="100%" cellpadding="0" cellspacing="0">
                <tr>
                  <td>
                    <div style="font-family: 'Segoe UI', sans-serif; font-size: 20px; font-weight: 700; color: #e8e6e1; letter-spacing: -0.5px;">🛡️ AgentAuth</div>
                  </td>
                  <td align="right">
                    <div style="font-size: 11px; color: rgba(255,255,255,0.3); letter-spacing: 2px; text-transform: uppercase;">Waitlist</div>
                  </td>
                </tr>
              </table>
            </td>
          </tr>

          <!-- Main Content -->
          <tr>
            <td style="padding: 40px 36px 24px 36px; text-align: center;">
              <div style="font-size: 48px; margin-bottom: 16px;">🔐 → 🔓 → ✅</div>
              <h1 style="color: #e8e6e1; font-size: 28px; margin: 0 0 8px 0; font-weight: 700; letter-spacing: -0.5px;">You're on the list</h1>
              <p style="color: rgba(255,255,255,0.4); font-size: 15px; margin: 0; line-height: 1.6;">Welcome to the future of AI agent authorization</p>
            </td>
          </tr>

          <!-- What is AgentAuth -->
          <tr>
            <td style="padding: 0 36px 24px 36px;">
              <div style="background: rgba(255,255,255,0.02); border: 1px solid rgba(255,255,255,0.04); border-radius: 12px; padding: 24px;">
                <p style="color: rgba(255,255,255,0.6); font-size: 14px; line-height: 1.8; margin: 0;">
                  <strong style="color: #e8e6e1;">AgentAuth</strong> is the authorization layer for AI agent commerce. 
                  When an AI agent wants to buy something on your behalf, AgentAuth ensures:
                </p>
                <table width="100%" cellpadding="0" cellspacing="0" style="margin-top: 16px;">
                  <tr>
                    <td style="padding: 8px 0;">
                      <span style="color: #e8e6e1; font-size: 13px;">🔐 <strong>Consent</strong></span>
                      <span style="color: rgba(255,255,255,0.4); font-size: 13px;"> — Human sets spending limits + intent</span>
                    </td>
                  </tr>
                  <tr>
                    <td style="padding: 8px 0;">
                      <span style="color: #e8e6e1; font-size: 13px;">🔓 <strong>Authorize</strong></span>
                      <span style="color: rgba(255,255,255,0.4); font-size: 13px;"> — Agent purchases get verified in real-time</span>
                    </td>
                  </tr>
                  <tr>
                    <td style="padding: 8px 0;">
                      <span style="color: #e8e6e1; font-size: 13px;">✅ <strong>Verify</strong></span>
                      <span style="color: rgba(255,255,255,0.4); font-size: 13px;"> — Cryptographic proof for chargeback defense</span>
                    </td>
                  </tr>
                </table>
              </div>
            </td>
          </tr>

          <!-- Stats -->
          <tr>
            <td style="padding: 0 36px 24px 36px;">
              <table width="100%" cellpadding="0" cellspacing="0">
                <tr>
                  <td width="33%" style="text-align: center; padding: 16px 8px; background: rgba(255,255,255,0.02); border-radius: 8px 0 0 8px; border: 1px solid rgba(255,255,255,0.04); border-right: none;">
                    <div style="color: #e8e6e1; font-size: 20px; font-weight: 700;">&lt;5ms</div>
                    <div style="color: rgba(255,255,255,0.3); font-size: 10px; letter-spacing: 1px; text-transform: uppercase; margin-top: 4px;">Latency</div>
                  </td>
                  <td width="34%" style="text-align: center; padding: 16px 8px; background: rgba(255,255,255,0.02); border: 1px solid rgba(255,255,255,0.04); border-right: none;">
                    <div style="color: #e8e6e1; font-size: 20px; font-weight: 700;">3 calls</div>
                    <div style="color: rgba(255,255,255,0.3); font-size: 10px; letter-spacing: 1px; text-transform: uppercase; margin-top: 4px;">Full Flow</div>
                  </td>
                  <td width="33%" style="text-align: center; padding: 16px 8px; background: rgba(255,255,255,0.02); border-radius: 0 8px 8px 0; border: 1px solid rgba(255,255,255,0.04);">
                    <div style="color: #e8e6e1; font-size: 20px; font-weight: 700;">JWT</div>
                    <div style="color: rgba(255,255,255,0.3); font-size: 10px; letter-spacing: 1px; text-transform: uppercase; margin-top: 4px;">Crypto Proof</div>
                  </td>
                </tr>
              </table>
            </td>
          </tr>

          <!-- CTA -->
          <tr>
            <td style="padding: 0 36px 32px 36px; text-align: center;">
              <div style="background: rgba(255,255,255,0.02); border: 1px solid rgba(255,255,255,0.06); border-radius: 10px; padding: 20px;">
                <p style="color: rgba(255,255,255,0.4); font-size: 10px; letter-spacing: 2px; text-transform: uppercase; margin: 0 0 8px 0;">What's next</p>
                <p style="color: #e8e6e1; font-size: 15px; margin: 0; font-weight: 500;">
                  We're onboarding new users gradually. You'll receive your API key and access invite soon.
                </p>
              </div>
            </td>
          </tr>

          <!-- Try Demo Button -->
          <tr>
            <td style="padding: 0 36px 32px 36px; text-align: center;">
              <a href="https://agentauth.in/demo" style="display: inline-block; padding: 12px 28px; background: #e8e6e1; color: #08080a; text-decoration: none; border-radius: 8px; font-weight: 700; font-size: 13px; letter-spacing: 0.5px;">Try the Interactive Demo →</a>
            </td>
          </tr>

          <!-- Footer -->
          <tr>
            <td style="padding: 20px 36px; border-top: 1px solid rgba(255,255,255,0.04); text-align: center;">
              <p style="color: rgba(255,255,255,0.2); font-size: 11px; margin: 0; line-height: 1.6;">
                © 2026 AgentAuth · <a href="https://agentauth.in" style="color: rgba(255,255,255,0.3); text-decoration: none;">agentauth.in</a><br>
                Authorization infrastructure for AI agent commerce
              </p>
            </td>
          </tr>

        </table>
      </td>
    </tr>
  </table>
</body>
</html>
  `;

  const emailText = `🔐→🔓→✅ You're on the AgentAuth Waitlist!

Welcome to the future of AI agent authorization.

AgentAuth is the authorization layer for AI agent commerce. When an AI agent wants to buy something on your behalf, AgentAuth ensures:

🔐 Consent — Human sets spending limits + intent
🔓 Authorize — Agent purchases get verified in real-time
✅ Verify — Cryptographic proof for chargeback defense

We're onboarding new users gradually. You'll receive your API key and access invite soon.

Try the interactive demo: https://agentauth.in/demo

---
© 2026 AgentAuth
https://agentauth.in
`;

  try {
    const response = await fetch("https://api.resend.com/emails", {
      method: "POST",
      headers: {
        Authorization: `Bearer ${RESEND_API_KEY}`,
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        from: "AgentAuth <hello@agentauth.in>",
        to: [email],
        subject: "🔐→🔓→✅ You're in — AgentAuth Waitlist Confirmed",
        html: emailHtml,
        text: emailText,
      }),
    });

    if (!response.ok) {
      console.error("Resend API error:", await response.text());
      return false;
    }
    return true;
  } catch (error) {
    console.error("Error sending email:", error);
    return false;
  }
};

const ALLOWED_ORIGINS = [
  "https://agentauth.in",
  "https://www.agentauth.in",
  "https://agentauth.netlify.app",
];

const handler: Handler = async (event: HandlerEvent, context: HandlerContext) => {
  const origin = event.headers?.origin || "";
  const allowedOrigin = ALLOWED_ORIGINS.includes(origin) ? origin : ALLOWED_ORIGINS[0];

  const headers = {
    "Access-Control-Allow-Origin": allowedOrigin,
    "Access-Control-Allow-Headers": "Content-Type",
    "Access-Control-Allow-Methods": "POST, OPTIONS",
    "Content-Type": "application/json",
  };

  if (event.httpMethod === "OPTIONS") {
    return { statusCode: 200, headers, body: "" };
  }

  if (event.httpMethod !== "POST") {
    return { statusCode: 405, headers, body: JSON.stringify({ error: "Method not allowed" }) };
  }

  try {
    const { email, name } = JSON.parse(event.body || "{}") as WaitlistRequest;

    if (!email || !email.includes("@")) {
      return { statusCode: 400, headers, body: JSON.stringify({ error: "Valid email required" }) };
    }

    const normalizedEmail = email.toLowerCase().trim();
    let isNewSignup = true;
    let position: number | undefined;

    // Save to Supabase if configured
    if (supabase) {
      // Check if already on waitlist
      const { data: existing } = await supabase
        .from('waitlist')
        .select('id, status, beta_access')
        .eq('email', normalizedEmail)
        .single();

      if (existing) {
        // Already on waitlist
        if (existing.beta_access) {
          return {
            statusCode: 200,
            headers,
            body: JSON.stringify({
              success: true,
              message: "You already have beta access! Check your email for your invite code.",
              alreadyApproved: true,
            }),
          };
        }
        isNewSignup = false;
      } else {
        // New signup - add to waitlist with pending status
        const { data, error } = await supabase
          .from('waitlist')
          .insert({
            email: normalizedEmail,
            name: name?.trim() || null,
            status: 'pending',
            beta_access: false,
            created_at: new Date().toISOString()
          })
          .select('id')
          .single();

        if (error && error.code !== '23505') {
          console.error("Supabase error:", error);
        } else {
          console.log(`Waitlist signup saved: ${normalizedEmail}`);
        }

        // Get position in queue
        const { count } = await supabase
          .from('waitlist')
          .select('*', { count: 'exact', head: true })
          .eq('status', 'pending');

        position = count || undefined;
      }
    } else {
      console.log(`Waitlist signup (no DB): ${normalizedEmail}`);
    }

    // Send confirmation email (only for new signups)
    let emailSent = false;
    if (isNewSignup) {
      emailSent = await sendWaitlistConfirmationEmail(normalizedEmail, position);
    }

    return {
      statusCode: 200,
      headers,
      body: JSON.stringify({
        success: true,
        message: isNewSignup
          ? "Thanks for joining! We'll email you when a spot opens up."
          : "You're already on the waitlist! We'll notify you soon.",
        position: position,
        emailSent,
      }),
    };
  } catch (error) {
    console.error("Waitlist error:", error);
    return { statusCode: 500, headers, body: JSON.stringify({ error: "Internal server error" }) };
  }
};

export { handler };
