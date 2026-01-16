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

const sendWelcomeEmail = async (email: string, inviteCode: string): Promise<boolean> => {
  if (!RESEND_API_KEY) {
    console.log("RESEND_API_KEY not set, skipping email send");
    return false;
  }

  const dashboardUrl = `https://agentauth.in/#portal`;

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
              <div style="display: inline-block; padding: 6px 14px; background: linear-gradient(135deg, rgba(168,85,247,0.2), rgba(59,130,246,0.2)); border-radius: 100px; margin-bottom: 24px; border: 1px solid rgba(168,85,247,0.3);">
                <span style="color: #a855f7; font-size: 13px; font-weight: 600;">🎉 Beta Access Granted</span>
              </div>
              <h1 style="color: #ffffff; font-size: 36px; margin: 0 0 12px 0; font-weight: 600;">You're In!</h1>
              <p style="color: rgba(255,255,255,0.5); font-size: 17px; margin: 0;">Your beta access is now active</p>
            </td>
          </tr>

          <tr>
            <td style="padding: 0 40px 32px 40px;">
              <div style="background: linear-gradient(135deg, rgba(168,85,247,0.1), rgba(59,130,246,0.1)); border-radius: 12px; padding: 20px; border: 1px solid rgba(168,85,247,0.2); text-align: center; margin-bottom: 24px;">
                <div style="color: rgba(255,255,255,0.5); font-size: 12px; margin-bottom: 8px; text-transform: uppercase;">Your Invite Code</div>
                <div style="color: #a855f7; font-size: 24px; font-weight: 600; letter-spacing: 2px;">${inviteCode}</div>
              </div>
              <p style="color: rgba(255,255,255,0.7); font-size: 15px; line-height: 1.7; margin: 0 0 24px 0;">
                You now have full access to the Developer Dashboard. Create API keys, integrate with your AI agents, and start building with AgentAuth.
              </p>
            </td>
          </tr>

          <tr>
            <td style="padding: 8px 40px 40px 40px; text-align: center;">
              <a href="${dashboardUrl}" style="display: inline-block; padding: 16px 32px; background: linear-gradient(135deg, #a855f7, #3b82f6); color: #fff; text-decoration: none; border-radius: 12px; font-weight: 600; font-size: 15px;">
                Access Dashboard →
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

  const emailText = `You're In! Beta Access Granted

Your invite code: ${inviteCode}

You now have full access to the Developer Dashboard. Create API keys, integrate with your AI agents, and start building with AgentAuth.

Access Dashboard: ${dashboardUrl}

---
AgentAuth
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
        subject: "�� Your AgentAuth Beta Access is Ready!",
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

const generateInviteCode = (): string => {
  const chars = 'ABCDEFGHJKLMNPQRSTUVWXYZ23456789';
  let code = 'AA-';
  for (let i = 0; i < 8; i++) {
    code += chars.charAt(Math.floor(Math.random() * chars.length));
  }
  return code;
};

const handler: Handler = async (event: HandlerEvent, context: HandlerContext) => {
  const headers = {
    "Access-Control-Allow-Origin": "*",
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

    const inviteCode = generateInviteCode();

    // Save to Supabase if configured
    if (supabase) {
      const { data, error } = await supabase
        .from('waitlist')
        .upsert({ 
          email: email.toLowerCase().trim(),
          name,
          invite_code: inviteCode,
          status: 'approved',
          beta_access: true,
          approved_at: new Date().toISOString()
        }, { 
          onConflict: 'email',
          ignoreDuplicates: false 
        })
        .select()
        .single();

      if (error && error.code !== '23505') { // Ignore duplicate key errors
        console.error("Supabase error:", error);
      } else {
        console.log(`Waitlist signup saved: ${email}`);
      }
    } else {
      console.log(`Waitlist signup (no DB): ${email}`);
    }

    // Send welcome email with beta access
    const emailSent = await sendWelcomeEmail(email, inviteCode);

    return {
      statusCode: 200,
      headers,
      body: JSON.stringify({
        success: true,
        message: "You're in! Check your email for beta access.",
        inviteCode,
        emailSent,
      }),
    };
  } catch (error) {
    console.error("Waitlist error:", error);
    return { statusCode: 500, headers, body: JSON.stringify({ error: "Internal server error" }) };
  }
};

export { handler };
