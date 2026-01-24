import { Handler } from "@netlify/functions";
import Stripe from "stripe";

const stripe = new Stripe(process.env.STRIPE_SECRET_KEY || "", {
    apiVersion: "2025-12-15.clover",
});

interface TransactionData {
    id: string;
    amount: number;
    currency: string;
    status: "authorized" | "denied" | "pending";
    merchant: string;
    created_at: string;
    description: string;
}

interface DashboardStats {
    total_authorizations: number;
    transaction_volume: number;
    approval_rate: number;
    avg_response_time: number;
    transactions: TransactionData[];
}

const handler: Handler = async (event) => {
    // CORS headers
    const headers = {
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Headers": "Content-Type, Authorization",
        "Access-Control-Allow-Methods": "GET, OPTIONS",
        "Content-Type": "application/json",
    };

    if (event.httpMethod === "OPTIONS") {
        return { statusCode: 200, headers, body: "" };
    }

    if (event.httpMethod !== "GET") {
        return {
            statusCode: 405,
            headers,
            body: JSON.stringify({ error: "Method not allowed" }),
        };
    }

    try {
        // Check if Stripe is configured
        if (!process.env.STRIPE_SECRET_KEY) {
            return {
                statusCode: 200,
                headers,
                body: JSON.stringify({
                    total_authorizations: 0,
                    transaction_volume: 0,
                    approval_rate: 0,
                    avg_response_time: 8.3,
                    transactions: [],
                    message: "Stripe not configured - showing empty data",
                }),
            };
        }

        // Parse query parameters
        const limit = parseInt(event.queryStringParameters?.limit || "20");
        const period = event.queryStringParameters?.period || "7d";

        // Calculate date range based on period
        const now = Math.floor(Date.now() / 1000);
        let startTime: number;
        switch (period) {
            case "24h":
                startTime = now - 24 * 60 * 60;
                break;
            case "30d":
                startTime = now - 30 * 24 * 60 * 60;
                break;
            case "90d":
                startTime = now - 90 * 24 * 60 * 60;
                break;
            case "7d":
            default:
                startTime = now - 7 * 24 * 60 * 60;
        }

        // Fetch payment intents from Stripe
        const paymentIntents = await stripe.paymentIntents.list({
            limit: Math.min(limit, 100),
            created: { gte: startTime },
        });

        // Transform Stripe data to our format
        const transactions: TransactionData[] = paymentIntents.data.map((pi) => {
            let status: "authorized" | "denied" | "pending";
            switch (pi.status) {
                case "succeeded":
                case "requires_capture":
                    status = "authorized";
                    break;
                case "canceled":
                case "requires_payment_method":
                    status = "denied";
                    break;
                default:
                    status = "pending";
            }

            return {
                id: pi.id,
                amount: pi.amount / 100, // Convert cents to dollars
                currency: pi.currency.toUpperCase(),
                status,
                merchant: pi.metadata?.merchant || "AgentAuth",
                created_at: new Date(pi.created * 1000).toISOString(),
                description: pi.description || "Agent transaction",
            };
        });

        // Calculate statistics
        const totalAuthorizations = transactions.length;
        const successfulTx = transactions.filter((t) => t.status === "authorized");
        const transactionVolume = successfulTx.reduce((sum, t) => sum + t.amount, 0);
        const approvalRate =
            totalAuthorizations > 0
                ? (successfulTx.length / totalAuthorizations) * 100
                : 0;

        const stats: DashboardStats = {
            total_authorizations: totalAuthorizations,
            transaction_volume: transactionVolume,
            approval_rate: Math.round(approvalRate * 10) / 10,
            avg_response_time: 8.3, // Placeholder - could be calculated from actual response times
            transactions,
        };

        return {
            statusCode: 200,
            headers,
            body: JSON.stringify(stats),
        };
    } catch (error) {
        console.error("Error fetching Stripe data:", error);
        return {
            statusCode: 500,
            headers,
            body: JSON.stringify({
                error: "Failed to fetch transaction data",
                details: error instanceof Error ? error.message : "Unknown error",
            }),
        };
    }
};

export { handler };
