import type { Handler, HandlerEvent, HandlerContext } from "@netlify/functions";
import { createClient } from "@supabase/supabase-js";

// Environment variables
const RESEND_API_KEY = process.env.RESEND_API_KEY || "";
const SUPABASE_URL = process.env.SUPABASE_URL || process.env.VITE_SUPABASE_URL || "";
const SUPABASE_SERVICE_KEY = process.env.SUPABASE_SERVICE_ROLE_KEY || "";
const NOTIFICATION_EMAIL = "hello@agentauth.in";

// Create Supabase client with service role for server-side operations
const supabase = SUPABASE_URL && SUPABASE_SERVICE_KEY
    ? createClient(SUPABASE_URL, SUPABASE_SERVICE_KEY)
    : null;

interface ContactRequest {
    name: string;
    email: string;
    company?: string;
    subject: string;
    message: string;
}

const sendNotificationEmail = async (contact: ContactRequest): Promise<boolean> => {
    if (!RESEND_API_KEY) {
        console.log("RESEND_API_KEY not set, skipping notification email");
        return false;
    }

    const subjectLabels: Record<string, string> = {
        general: "General Inquiry",
        sales: "Sales & Pricing",
        partnership: "Partnership",
        support: "Technical Support",
        enterprise: "Enterprise Plan"
    };

    const emailHtml = `
<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
</head>
<body style="margin: 0; padding: 20px; background-color: #f5f5f5; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;">
  <div style="max-width: 600px; margin: 0 auto; background: #fff; border-radius: 12px; padding: 32px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
    <h2 style="color: #1a1a1a; margin: 0 0 24px 0; border-bottom: 2px solid #a855f7; padding-bottom: 12px;">
      📬 New Contact Form Submission
    </h2>
    
    <table style="width: 100%; border-collapse: collapse;">
      <tr>
        <td style="padding: 12px 0; border-bottom: 1px solid #eee; color: #666; width: 120px;">Name:</td>
        <td style="padding: 12px 0; border-bottom: 1px solid #eee; color: #1a1a1a; font-weight: 500;">${contact.name}</td>
      </tr>
      <tr>
        <td style="padding: 12px 0; border-bottom: 1px solid #eee; color: #666;">Email:</td>
        <td style="padding: 12px 0; border-bottom: 1px solid #eee;">
          <a href="mailto:${contact.email}" style="color: #a855f7; text-decoration: none;">${contact.email}</a>
        </td>
      </tr>
      <tr>
        <td style="padding: 12px 0; border-bottom: 1px solid #eee; color: #666;">Company:</td>
        <td style="padding: 12px 0; border-bottom: 1px solid #eee; color: #1a1a1a;">${contact.company || "Not provided"}</td>
      </tr>
      <tr>
        <td style="padding: 12px 0; border-bottom: 1px solid #eee; color: #666;">Subject:</td>
        <td style="padding: 12px 0; border-bottom: 1px solid #eee;">
          <span style="display: inline-block; padding: 4px 12px; background: #f0e6ff; color: #7c3aed; border-radius: 20px; font-size: 13px;">
            ${subjectLabels[contact.subject] || contact.subject}
          </span>
        </td>
      </tr>
    </table>
    
    <div style="margin-top: 24px;">
      <p style="color: #666; margin: 0 0 8px 0; font-weight: 500;">Message:</p>
      <div style="background: #f9f9f9; padding: 16px; border-radius: 8px; color: #1a1a1a; line-height: 1.6; white-space: pre-wrap;">${contact.message}</div>
    </div>
    
    <div style="margin-top: 24px; padding-top: 16px; border-top: 1px solid #eee;">
      <a href="mailto:${contact.email}?subject=Re: ${subjectLabels[contact.subject] || contact.subject}" 
         style="display: inline-block; padding: 12px 24px; background: linear-gradient(135deg, #a855f7, #3b82f6); color: #fff; text-decoration: none; border-radius: 8px; font-weight: 500;">
        Reply to ${contact.name}
      </a>
    </div>
    
    <p style="color: #999; font-size: 12px; margin-top: 24px;">
      Submitted at ${new Date().toLocaleString("en-US", { timeZone: "Asia/Kolkata" })} IST
    </p>
  </div>
</body>
</html>
  `;

    const emailText = `
New Contact Form Submission

Name: ${contact.name}
Email: ${contact.email}
Company: ${contact.company || "Not provided"}
Subject: ${subjectLabels[contact.subject] || contact.subject}

Message:
${contact.message}

---
Reply to: ${contact.email}
Submitted at: ${new Date().toISOString()}
  `;

    try {
        const response = await fetch("https://api.resend.com/emails", {
            method: "POST",
            headers: {
                Authorization: `Bearer ${RESEND_API_KEY}`,
                "Content-Type": "application/json",
            },
            body: JSON.stringify({
                from: "AgentAuth Contact <hello@agentauth.in>",
                to: [NOTIFICATION_EMAIL],
                reply_to: contact.email,
                subject: `[Contact] ${subjectLabels[contact.subject] || contact.subject} - ${contact.name}`,
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
        console.error("Error sending notification email:", error);
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
        const contact = JSON.parse(event.body || "{}") as ContactRequest;

        // Validate required fields
        if (!contact.name || !contact.email || !contact.message) {
            return {
                statusCode: 400,
                headers,
                body: JSON.stringify({ error: "Name, email, and message are required" })
            };
        }

        if (!contact.email.includes("@")) {
            return {
                statusCode: 400,
                headers,
                body: JSON.stringify({ error: "Valid email required" })
            };
        }

        // Save to Supabase if configured
        if (supabase) {
            const { error } = await supabase
                .from('contact_messages')
                .insert({
                    name: contact.name.trim(),
                    email: contact.email.toLowerCase().trim(),
                    company: contact.company?.trim() || null,
                    subject: contact.subject || 'general',
                    message: contact.message.trim(),
                    created_at: new Date().toISOString(),
                    status: 'new'
                });

            if (error) {
                console.error("Supabase error:", error);
                // Continue anyway - we'll still send the email notification
            } else {
                console.log(`Contact message saved from: ${contact.email}`);
            }
        } else {
            console.log(`Contact message received (no DB): ${contact.email}`);
        }

        // Send notification email to team
        const emailSent = await sendNotificationEmail(contact);

        return {
            statusCode: 200,
            headers,
            body: JSON.stringify({
                success: true,
                message: "Message sent successfully! We'll get back to you soon.",
                emailSent,
            }),
        };
    } catch (error) {
        console.error("Contact form error:", error);
        return {
            statusCode: 500,
            headers,
            body: JSON.stringify({ error: "Internal server error" })
        };
    }
};

export { handler };
