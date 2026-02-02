import type { Handler, HandlerEvent, HandlerContext } from "@netlify/functions";
import Stripe from "stripe";

// Environment variables
const STRIPE_SECRET_KEY = process.env.STRIPE_SECRET_KEY || "";

// Initialize Stripe
const stripe = STRIPE_SECRET_KEY ? new Stripe(STRIPE_SECRET_KEY) : null;

interface ConnectRequest {
    action: "create" | "status" | "onboarding-link" | "dashboard-link" | "transactions";
    user_id?: string;
    email?: string;
    country?: string;
    account_id?: string;
    limit?: number;
}

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

    if (!stripe) {
        return {
            statusCode: 503,
            headers,
            body: JSON.stringify({ error: "Stripe not configured. Please set STRIPE_SECRET_KEY." })
        };
    }

    try {
        const body = JSON.parse(event.body || "{}") as ConnectRequest;
        const { action, user_id, email, country = "US", account_id, limit = 20 } = body;

        const baseUrl = process.env.URL || "https://agentauth.in";

        switch (action) {
            case "create": {
                if (!email || !user_id) {
                    return { statusCode: 400, headers, body: JSON.stringify({ error: "email and user_id are required" }) };
                }

                // Create Stripe Connect account
                const account = await stripe.accounts.create({
                    type: "express",
                    country,
                    email,
                    metadata: { user_id },
                    capabilities: {
                        card_payments: { requested: true },
                        transfers: { requested: true },
                    },
                });

                // Create onboarding link
                const accountLink = await stripe.accountLinks.create({
                    account: account.id,
                    refresh_url: `${baseUrl}/nucleus?connect=refresh`,
                    return_url: `${baseUrl}/nucleus?connect=success&account_id=${account.id}`,
                    type: "account_onboarding",
                });

                return {
                    statusCode: 200,
                    headers,
                    body: JSON.stringify({
                        success: true,
                        account_id: account.id,
                        onboarding_url: accountLink.url,
                    }),
                };
            }

            case "status": {
                if (!account_id) {
                    return { statusCode: 400, headers, body: JSON.stringify({ error: "account_id is required" }) };
                }

                const account = await stripe.accounts.retrieve(account_id);

                let status = "incomplete";
                if (account.charges_enabled && account.payouts_enabled) {
                    status = "active";
                } else if (account.details_submitted) {
                    status = "pending";
                }

                return {
                    statusCode: 200,
                    headers,
                    body: JSON.stringify({
                        success: true,
                        account_id: account.id,
                        details_submitted: account.details_submitted,
                        charges_enabled: account.charges_enabled,
                        payouts_enabled: account.payouts_enabled,
                        status,
                    }),
                };
            }

            case "onboarding-link": {
                if (!account_id) {
                    return { statusCode: 400, headers, body: JSON.stringify({ error: "account_id is required" }) };
                }

                const accountLink = await stripe.accountLinks.create({
                    account: account_id,
                    refresh_url: `${baseUrl}/nucleus?connect=refresh`,
                    return_url: `${baseUrl}/nucleus?connect=success&account_id=${account_id}`,
                    type: "account_onboarding",
                });

                return {
                    statusCode: 200,
                    headers,
                    body: JSON.stringify({
                        success: true,
                        onboarding_url: accountLink.url,
                    }),
                };
            }

            case "dashboard-link": {
                if (!account_id) {
                    return { statusCode: 400, headers, body: JSON.stringify({ error: "account_id is required" }) };
                }

                const loginLink = await stripe.accounts.createLoginLink(account_id);

                return {
                    statusCode: 200,
                    headers,
                    body: JSON.stringify({
                        success: true,
                        dashboard_url: loginLink.url,
                    }),
                };
            }

            case "transactions": {
                if (!account_id) {
                    return { statusCode: 400, headers, body: JSON.stringify({ error: "account_id is required" }) };
                }

                const charges = await stripe.charges.list(
                    { limit },
                    { stripeAccount: account_id }
                );

                const transactions = charges.data.map(charge => ({
                    id: charge.id,
                    amount: charge.amount / 100,
                    currency: charge.currency.toUpperCase(),
                    status: charge.status,
                    description: charge.description || "No description",
                    created_at: charge.created,
                    merchant: charge.metadata?.merchant || "Unknown",
                }));

                return {
                    statusCode: 200,
                    headers,
                    body: JSON.stringify({
                        success: true,
                        transactions,
                    }),
                };
            }

            default:
                return { statusCode: 400, headers, body: JSON.stringify({ error: `Invalid action: ${action}` }) };
        }
    } catch (error: any) {
        console.error("Stripe Connect error:", error);
        return {
            statusCode: 500,
            headers,
            body: JSON.stringify({ error: error.message || "Internal server error" })
        };
    }
};

export { handler };
