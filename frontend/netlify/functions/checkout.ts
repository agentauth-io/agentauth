import type { Handler, HandlerEvent, HandlerContext } from "@netlify/functions";
import Stripe from "stripe";

// Environment variables
const STRIPE_SECRET_KEY = process.env.STRIPE_SECRET_KEY || "";
const STRIPE_PRICE_STARTUP = process.env.STRIPE_PRICE_STARTUP || "";
const STRIPE_PRICE_PRO = process.env.STRIPE_PRICE_PRO || "";
const STRIPE_PRICE_ENTERPRISE = process.env.STRIPE_PRICE_ENTERPRISE || "";

// Initialize Stripe
const stripe = STRIPE_SECRET_KEY ? new Stripe(STRIPE_SECRET_KEY) : null;

interface CheckoutRequest {
    plan: string;
    email: string;
    userId: string;
    successUrl?: string;
    cancelUrl?: string;
}

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

    if (!stripe) {
        return {
            statusCode: 503,
            headers,
            body: JSON.stringify({ error: "Stripe not configured. Please set STRIPE_SECRET_KEY." })
        };
    }

    try {
        const body = JSON.parse(event.body || "{}") as CheckoutRequest;
        const { plan, email, userId, successUrl, cancelUrl } = body;

        if (!email || !plan) {
            return { statusCode: 400, headers, body: JSON.stringify({ error: "Email and plan are required" }) };
        }

        // Map plan to price ID
        let priceId: string;
        switch (plan.toLowerCase()) {
            case "startup":
                priceId = STRIPE_PRICE_STARTUP;
                break;
            case "pro":
                priceId = STRIPE_PRICE_PRO;
                break;
            case "enterprise":
                priceId = STRIPE_PRICE_ENTERPRISE;
                break;
            default:
                return { statusCode: 400, headers, body: JSON.stringify({ error: `Invalid plan: ${plan}` }) };
        }

        if (!priceId) {
            return {
                statusCode: 503,
                headers,
                body: JSON.stringify({ error: `Price not configured for plan: ${plan}. Set STRIPE_PRICE_${plan.toUpperCase()}.` })
            };
        }

        // Create or get customer
        let customerId: string;
        const existingCustomers = await stripe.customers.list({ email, limit: 1 });

        if (existingCustomers.data.length > 0) {
            customerId = existingCustomers.data[0].id;
        } else {
            const customer = await stripe.customers.create({
                email,
                metadata: { user_id: userId || "" },
            });
            customerId = customer.id;
        }

        // Create Checkout Session
        const session = await stripe.checkout.sessions.create({
            customer: customerId,
            payment_method_types: ["card"],
            line_items: [{ price: priceId, quantity: 1 }],
            mode: "subscription",
            success_url: successUrl || "https://agentauth.in/portal?checkout=success",
            cancel_url: cancelUrl || "https://agentauth.in/pricing?checkout=canceled",
            metadata: {
                user_id: userId || "",
                plan,
            },
            subscription_data: {
                metadata: {
                    user_id: userId || "",
                    plan,
                },
            },
        });

        return {
            statusCode: 200,
            headers,
            body: JSON.stringify({
                success: true,
                checkout_url: session.url,
                session_id: session.id,
            }),
        };
    } catch (error: any) {
        console.error("Checkout error:", error);
        return {
            statusCode: 500,
            headers,
            body: JSON.stringify({ error: error.message || "Internal server error" })
        };
    }
};

export { handler };
