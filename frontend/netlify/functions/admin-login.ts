import { Handler } from "@netlify/functions";
import jwt from "jsonwebtoken";

const ADMIN_PASSWORD = process.env.ADMIN_PASSWORD;
const JWT_SECRET = process.env.ADMIN_JWT_SECRET;

if (!ADMIN_PASSWORD || !JWT_SECRET) {
    console.error("ADMIN_PASSWORD and ADMIN_JWT_SECRET must be set in environment");
}

const ALLOWED_ORIGINS = [
    "https://agentauth.in",
    "https://www.agentauth.in",
    "https://agentauth.netlify.app",
];

const handler: Handler = async (event) => {
    const origin = event.headers?.origin || "";
    const allowedOrigin = ALLOWED_ORIGINS.includes(origin) ? origin : ALLOWED_ORIGINS[0];
    
    const headers = {
        "Access-Control-Allow-Origin": allowedOrigin,
        "Access-Control-Allow-Headers": "Content-Type, Authorization",
        "Access-Control-Allow-Methods": "POST, OPTIONS",
        "Content-Type": "application/json",
    };

    if (event.httpMethod === "OPTIONS") {
        return { statusCode: 200, headers, body: "" };
    }

    if (event.httpMethod !== "POST") {
        return {
            statusCode: 405,
            headers,
            body: JSON.stringify({ error: "Method not allowed" }),
        };
    }

    try {
        const { password } = JSON.parse(event.body || "{}");

        if (password !== ADMIN_PASSWORD) {
            return {
                statusCode: 401,
                headers,
                body: JSON.stringify({ detail: "Invalid password" }),
            };
        }

        // Create token
        const expiresAt = new Date();
        expiresAt.setHours(expiresAt.getHours() + 1);

        const token = jwt.sign(
            { type: "admin", exp: Math.floor(expiresAt.getTime() / 1000) },
            JWT_SECRET
        );

        return {
            statusCode: 200,
            headers,
            body: JSON.stringify({
                token,
                expires_at: expiresAt.toISOString(),
                message: "Login successful",
            }),
        };
    } catch (error) {
        return {
            statusCode: 400,
            headers,
            body: JSON.stringify({ error: "Invalid request" }),
        };
    }
};

export { handler };
