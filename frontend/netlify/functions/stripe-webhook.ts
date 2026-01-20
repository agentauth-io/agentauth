import { Handler, HandlerEvent, HandlerContext } from "@netlify/functions";
import Stripe from "stripe";
import { createClient } from "@supabase/supabase-js";
import { Resend } from "resend";

// Initialize clients
const stripe = new Stripe(process.env.STRIPE_SECRET_KEY || "", {
    apiVersion: "2024-12-18.acacia",
});

const supabase = createClient(
    process.env.SUPABASE_URL || "",
    process.env.SUPABASE_SERVICE_KEY || "" // Service key for admin operations
);

const resend = new Resend(process.env.RESEND_API_KEY);

// Plan mapping from Stripe price IDs
const PRICE_TO_PLAN: Record<string, string> = {
    [process.env.STRIPE_PRICE_STARTUP || ""]: "startup",
    [process.env.STRIPE_PRICE_PRO || ""]: "pro",
    [process.env.STRIPE_PRICE_ENTERPRISE || ""]: "enterprise",
};

const handler: Handler = async (event: HandlerEvent, context: HandlerContext) => {
    // Only allow POST
    if (event.httpMethod !== "POST") {
        return { statusCode: 405, body: "Method Not Allowed" };
    }

    const sig = event.headers["stripe-signature"];
    const webhookSecret = process.env.STRIPE_WEBHOOK_SECRET;

    if (!sig || !webhookSecret) {
        console.error("Missing signature or webhook secret");
        return { statusCode: 400, body: "Missing signature or webhook secret" };
    }

    let stripeEvent: Stripe.Event;

    try {
        stripeEvent = stripe.webhooks.constructEvent(
            event.body || "",
            sig,
            webhookSecret
        );
    } catch (err) {
        console.error("Webhook signature verification failed:", err);
        return { statusCode: 400, body: "Invalid signature" };
    }

    // Handle checkout.session.completed
    if (stripeEvent.type === "checkout.session.completed") {
        const session = stripeEvent.data.object as Stripe.Checkout.Session;

        console.log("Checkout session completed:", session.id);

        try {
            await handleCheckoutComplete(session);
        } catch (err) {
            console.error("Error handling checkout:", err);
            // Still return 200 to acknowledge receipt
        }
    }

    // Handle subscription updates
    if (stripeEvent.type === "customer.subscription.updated") {
        const subscription = stripeEvent.data.object as Stripe.Subscription;
        console.log("Subscription updated:", subscription.id);
        // Update subscription status in database
    }

    // Handle subscription cancellation
    if (stripeEvent.type === "customer.subscription.deleted") {
        const subscription = stripeEvent.data.object as Stripe.Subscription;
        console.log("Subscription canceled:", subscription.id);
        // Mark subscription as canceled in database
    }

    return { statusCode: 200, body: JSON.stringify({ received: true }) };
};

async function handleCheckoutComplete(session: Stripe.Checkout.Session) {
    const customerEmail = session.customer_email || session.customer_details?.email;
    const customerName = session.customer_details?.name || "New User";
    const customerId = session.customer as string;
    const subscriptionId = session.subscription as string;

    if (!customerEmail) {
        console.error("No customer email in session");
        return;
    }

    console.log(`Processing checkout for ${customerEmail}`);

    // Get subscription details to determine plan
    let planName = "startup"; // default
    if (subscriptionId) {
        try {
            const subscription = await stripe.subscriptions.retrieve(subscriptionId);
            const priceId = subscription.items.data[0]?.price.id;
            planName = PRICE_TO_PLAN[priceId] || "startup";
        } catch (err) {
            console.error("Error fetching subscription:", err);
        }
    }

    // Check if user already exists in Supabase
    const { data: existingUser } = await supabase.auth.admin.listUsers();
    const userExists = existingUser?.users?.some(u => u.email === customerEmail);

    let userId: string;

    if (!userExists) {
        // Create new user account with random password
        const tempPassword = generateSecurePassword();

        const { data: newUser, error: createError } = await supabase.auth.admin.createUser({
            email: customerEmail,
            password: tempPassword,
            email_confirm: true, // Auto-confirm email
            user_metadata: {
                full_name: customerName,
                stripe_customer_id: customerId,
                subscription_plan: planName,
            },
        });

        if (createError) {
            console.error("Error creating user:", createError);
            throw createError;
        }

        userId = newUser.user.id;
        console.log(`Created new user: ${userId}`);

        // Generate magic link for login
        const { data: magicLinkData, error: magicError } = await supabase.auth.admin.generateLink({
            type: "magiclink",
            email: customerEmail,
            options: {
                redirectTo: "https://agentauth.in/portal",
            },
        });

        const magicLink = magicLinkData?.properties?.action_link || "https://agentauth.in/portal";

        // Send welcome email
        await sendWelcomeEmail(customerEmail, customerName, planName, magicLink);

    } else {
        // User exists - just update their subscription
        const existingUserData = existingUser?.users?.find(u => u.email === customerEmail);
        userId = existingUserData?.id || "";

        // Update user metadata with subscription info
        await supabase.auth.admin.updateUserById(userId, {
            user_metadata: {
                stripe_customer_id: customerId,
                subscription_plan: planName,
            },
        });

        // Send upgrade confirmation email
        await sendUpgradeEmail(customerEmail, customerName, planName);
    }

    // Store subscription in database (if you have a subscriptions table)
    // This would connect to your backend database
    console.log(`Subscription created for user ${userId}: ${planName} plan`);
}

function generateSecurePassword(): string {
    const chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789!@#$%^&*";
    let password = "";
    for (let i = 0; i < 16; i++) {
        password += chars.charAt(Math.floor(Math.random() * chars.length));
    }
    return password;
}

async function sendWelcomeEmail(
    email: string,
    name: string,
    plan: string,
    magicLink: string
) {
    const planDisplay = plan.charAt(0).toUpperCase() + plan.slice(1);

    try {
        await resend.emails.send({
            from: "AgentAuth <noreply@agentauth.in>",
            to: email,
            subject: `🎉 Welcome to AgentAuth ${planDisplay}!`,
            html: `
<!DOCTYPE html>
<html>
<head>
    <style>
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #0a0a0f; color: #ffffff; padding: 40px; }
        .container { max-width: 600px; margin: 0 auto; background: linear-gradient(180deg, rgba(255,255,255,0.08) 0%, rgba(255,255,255,0.02) 100%); border-radius: 16px; padding: 40px; border: 1px solid rgba(255,255,255,0.1); }
        h1 { margin: 0 0 20px 0; font-size: 28px; }
        p { color: #a0a0a0; line-height: 1.6; margin: 16px 0; }
        .button { display: inline-block; background: #ffffff; color: #000000; padding: 14px 28px; border-radius: 8px; text-decoration: none; font-weight: 600; margin: 24px 0; }
        .plan-badge { display: inline-block; background: linear-gradient(135deg, #4F46E5 0%, #7C3AED 100%); padding: 6px 16px; border-radius: 20px; font-size: 14px; font-weight: 600; }
        .footer { margin-top: 40px; padding-top: 20px; border-top: 1px solid rgba(255,255,255,0.1); font-size: 14px; color: #666; }
    </style>
</head>
<body>
    <div class="container">
        <h1>Welcome to AgentAuth, ${name}! 🚀</h1>
        
        <p>Thank you for subscribing to the <span class="plan-badge">${planDisplay} Plan</span></p>
        
        <p>Your account has been created and your subscription is now active. You can now access all the features included in your plan.</p>
        
        <a href="${magicLink}" class="button">Access Your Dashboard →</a>
        
        <p>Click the button above to log into your Developer Portal and start securing your AI agents.</p>
        
        <div style="background: rgba(255,255,255,0.05); padding: 20px; border-radius: 8px; margin: 24px 0;">
            <p style="margin: 0; color: #fff; font-weight: 600;">What's included:</p>
            <ul style="color: #a0a0a0; margin: 12px 0; padding-left: 20px;">
                <li>API Keys & Authentication</li>
                <li>Authorization Policies</li>
                <li>Audit Logs & Analytics</li>
                <li>Enterprise-grade Security</li>
            </ul>
        </div>
        
        <p>Your receipt has been sent separately by Stripe.</p>
        
        <div class="footer">
            <p>Questions? Reply to this email or contact us at hello@agentauth.in</p>
            <p>© 2026 AgentAuth. All rights reserved.</p>
        </div>
    </div>
</body>
</html>
            `,
        });
        console.log(`Welcome email sent to ${email}`);
    } catch (err) {
        console.error("Error sending welcome email:", err);
    }
}

async function sendUpgradeEmail(email: string, name: string, plan: string) {
    const planDisplay = plan.charAt(0).toUpperCase() + plan.slice(1);

    try {
        await resend.emails.send({
            from: "AgentAuth <noreply@agentauth.in>",
            to: email,
            subject: `🎉 You've upgraded to AgentAuth ${planDisplay}!`,
            html: `
<!DOCTYPE html>
<html>
<head>
    <style>
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #0a0a0f; color: #ffffff; padding: 40px; }
        .container { max-width: 600px; margin: 0 auto; background: linear-gradient(180deg, rgba(255,255,255,0.08) 0%, rgba(255,255,255,0.02) 100%); border-radius: 16px; padding: 40px; border: 1px solid rgba(255,255,255,0.1); }
        h1 { margin: 0 0 20px 0; font-size: 28px; }
        p { color: #a0a0a0; line-height: 1.6; margin: 16px 0; }
        .button { display: inline-block; background: #ffffff; color: #000000; padding: 14px 28px; border-radius: 8px; text-decoration: none; font-weight: 600; margin: 24px 0; }
        .plan-badge { display: inline-block; background: linear-gradient(135deg, #4F46E5 0%, #7C3AED 100%); padding: 6px 16px; border-radius: 20px; font-size: 14px; font-weight: 600; }
        .footer { margin-top: 40px; padding-top: 20px; border-top: 1px solid rgba(255,255,255,0.1); font-size: 14px; color: #666; }
    </style>
</head>
<body>
    <div class="container">
        <h1>Upgrade Complete! 🎉</h1>
        
        <p>Hey ${name}, your account has been upgraded to the <span class="plan-badge">${planDisplay} Plan</span></p>
        
        <p>All your new features are now active and available in your dashboard.</p>
        
        <a href="https://agentauth.in/portal" class="button">Go to Dashboard →</a>
        
        <p>Your receipt has been sent separately.</p>
        
        <div class="footer">
            <p>Questions? Reply to this email or contact us at hello@agentauth.in</p>
            <p>© 2026 AgentAuth. All rights reserved.</p>
        </div>
    </div>
</body>
</html>
            `,
        });
        console.log(`Upgrade email sent to ${email}`);
    } catch (err) {
        console.error("Error sending upgrade email:", err);
    }
}

export { handler };
