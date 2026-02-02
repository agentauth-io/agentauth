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
<body style="margin: 0; padding: 0; background-color: #000; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;">
  <table width="100%" cellpadding="0" cellspacing="0" style="background-color: #000; padding: 48px 20px;">
    <tr>
      <td align="center">
        <table width="560" cellpadding="0" cellspacing="0" style="background: #0a0a0f; border-radius: 20px; border: 1px solid rgba(255,255,255,0.08);">
          
          <tr>
            <td style="padding: 32px 40px 24px 40px; border-bottom: 1px solid rgba(255,255,255,0.05);">
              <div style="font-size: 24px; font-weight: 500; color: #fff;">AgentAuth</div>
            </td>
          </tr>

          <tr>
            <td style="padding: 48px 40px 32px 40px; text-align: center;">
              <div style="display: inline-block; padding: 6px 14px; background: linear-gradient(135deg, rgba(59,130,246,0.2), rgba(168,85,247,0.2)); border-radius: 100px; margin-bottom: 24px; border: 1px solid rgba(59,130,246,0.3);">
                <span style="color: #3b82f6; font-size: 13px; font-weight: 600;">⏳ Waitlist Confirmed</span>
              </div>
              <h1 style="color: #ffffff; font-size: 36px; margin: 0 0 12px 0; font-weight: 600;">You're on the list!</h1>
              <p style="color: rgba(255,255,255,0.5); font-size: 17px; margin: 0;">Thank you for your interest in AgentAuth</p>
            </td>
          </tr>

          <tr>
            <td style="padding: 0 40px 32px 40px;">
              <div style="background: linear-gradient(135deg, rgba(59,130,246,0.1), rgba(168,85,247,0.1)); border-radius: 12px; padding: 24px; border: 1px solid rgba(59,130,246,0.2); text-align: center; margin-bottom: 24px;">
                <p style="color: rgba(255,255,255,0.7); font-size: 15px; line-height: 1.7; margin: 0;">
                  We're currently in private beta and adding new users gradually. 
                  We'll send you an email with your access code as soon as a spot opens up!
                </p>
              </div>
              
              <div style="text-align: center; padding: 16px; background: rgba(168,85,247,0.1); border-radius: 8px; border: 1px solid rgba(168,85,247,0.2);">
                <p style="color: rgba(255,255,255,0.5); font-size: 13px; margin: 0 0 4px 0;">WHAT'S NEXT?</p>
                <p style="color: #a855f7; font-size: 15px; margin: 0; font-weight: 500;">
                  📬 Watch your inbox for your beta access invite
                </p>
              </div>
            </td>
          </tr>

          <tr>
            <td style="padding: 8px 40px 40px 40px; text-align: center;">
              <a href="https://agentauth.in" style="display: inline-block; padding: 14px 28px; background: transparent; color: rgba(255,255,255,0.6); text-decoration: none; border-radius: 10px; font-weight: 500; font-size: 14px; border: 1px solid rgba(255,255,255,0.2);">
                Learn More About AgentAuth
              </a>
            </td>
          </tr>

          <tr>
            <td style="padding: 24px 40px; border-top: 1px solid rgba(255,255,255,0.05); text-align: center;">
              <p style="color: rgba(255,255,255,0.3); font-size: 12px; margin: 0;">
                © 2026 AgentAuth<br>
                <a href="https://agentauth.in" style="color: rgba(255,255,255,0.4); text-decoration: none;">agentauth.in</a>
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

  const emailText = `You're on the Waitlist!

Thank you for your interest in AgentAuth.

We're currently in private beta and adding new users gradually. We'll send you an email with your access code as soon as a spot opens up!

What's next?
Watch your inbox for your beta access invite.

---
AgentAuth
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
        subject: "⏳ You're on the AgentAuth Waitlist!",
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
            status: 'pending',           // NOT approved yet
            beta_access: false,           // NO beta access yet
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
