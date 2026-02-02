// Test command
import { Command } from "commander";
import ora from "ora";
import chalk from "chalk";
import { apiRequest, checkConnection } from "../utils/api.js";
import { success, error, heading } from "../utils/output.js";
import { getConfig, getApiKey } from "../utils/config.js";
import type { TestResult } from "../types.js";

interface TestScenario {
    name: string;
    run: () => Promise<{ passed: boolean; message: string }>;
}

export const testCommand = new Command("test")
    .description("Run integration tests and diagnostics")
    .option("--verbose", "Show detailed test output")
    .option("--scenario <name>", "Run specific test scenario")
    .action(async (options) => {
        const config = getConfig();
        const results: TestResult[] = [];
        
        heading("AgentAuth Integration Tests");
        console.log(chalk.gray(`API: ${config.apiUrl}\n`));

        const scenarios: TestScenario[] = [
            {
                name: "API Connection",
                run: async () => {
                    const connected = await checkConnection();
                    return {
                        passed: connected,
                        message: connected ? "API is reachable" : "Cannot connect to API",
                    };
                },
            },
            {
                name: "Authentication",
                run: async () => {
                    const apiKey = getApiKey();
                    if (!apiKey) {
                        return { passed: false, message: "No API key configured" };
                    }
                    const result = await apiRequest<{ valid: boolean }>("/v1/auth/validate");
                    return {
                        passed: result.success,
                        message: result.success ? "API key is valid" : (result.error || "Invalid API key"),
                    };
                },
            },
            {
                name: "Dashboard Stats",
                run: async () => {
                    const result = await apiRequest<unknown>("/v1/dashboard/stats");
                    return {
                        passed: result.success,
                        message: result.success ? "Dashboard stats accessible" : (result.error || "Failed to fetch stats"),
                    };
                },
            },
            {
                name: "Agents List",
                run: async () => {
                    const result = await apiRequest<unknown[]>("/v1/agents");
                    return {
                        passed: result.success,
                        message: result.success 
                            ? `Found ${Array.isArray(result.data) ? result.data.length : 0} agents` 
                            : (result.error || "Failed to fetch agents"),
                    };
                },
            },
            {
                name: "Consents List",
                run: async () => {
                    const result = await apiRequest<unknown[]>("/v1/consents");
                    return {
                        passed: result.success,
                        message: result.success 
                            ? `Found ${Array.isArray(result.data) ? result.data.length : 0} consents` 
                            : (result.error || "Failed to fetch consents"),
                    };
                },
            },
            {
                name: "Authorization Flow",
                run: async () => {
                    // Create a test authorization
                    const result = await apiRequest<{ id: string }>("/v1/authorize", {
                        method: "POST",
                        body: {
                            agent_id: "cli-test-agent",
                            intent: "CLI integration test",
                            max_amount: 1.00,
                            currency: "USD",
                        },
                    });
                    
                    if (!result.success) {
                        return { passed: false, message: result.error || "Failed to create test authorization" };
                    }
                    
                    // Verify the authorization
                    const verifyResult = await apiRequest<{ status: string }>(`/v1/verify/${result.data?.id}`);
                    
                    return {
                        passed: verifyResult.success,
                        message: verifyResult.success 
                            ? "Authorization flow working" 
                            : (verifyResult.error || "Verification failed"),
                    };
                },
            },
        ];

        const scenariosToRun = options.scenario 
            ? scenarios.filter(s => s.name.toLowerCase().includes(options.scenario.toLowerCase()))
            : scenarios;

        if (scenariosToRun.length === 0) {
            error(`No scenarios matching "${options.scenario}"`);
            return;
        }

        for (const scenario of scenariosToRun) {
            const spinner = ora(`Testing: ${scenario.name}`).start();
            const startTime = Date.now();
            
            try {
                const result = await scenario.run();
                const duration = Date.now() - startTime;
                
                results.push({
                    name: scenario.name,
                    passed: result.passed,
                    duration,
                    error: result.passed ? undefined : result.message,
                });

                if (result.passed) {
                    spinner.succeed(`${scenario.name} ${chalk.gray(`(${duration}ms)`)}`);
                    if (options.verbose) {
                        console.log(chalk.gray(`   ${result.message}`));
                    }
                } else {
                    spinner.fail(`${scenario.name} ${chalk.gray(`(${duration}ms)`)}`);
                    console.log(chalk.red(`   ${result.message}`));
                }
            } catch (err) {
                const duration = Date.now() - startTime;
                results.push({
                    name: scenario.name,
                    passed: false,
                    duration,
                    error: err instanceof Error ? err.message : "Unknown error",
                });
                spinner.fail(`${scenario.name} ${chalk.gray(`(${duration}ms)`)}`);
                console.log(chalk.red(`   ${err instanceof Error ? err.message : "Unknown error"}`));
            }
        }

        // Summary
        console.log();
        const passed = results.filter(r => r.passed).length;
        const failed = results.filter(r => !r.passed).length;
        const totalTime = results.reduce((acc, r) => acc + r.duration, 0);

        if (failed === 0) {
            success(`All ${passed} tests passed in ${totalTime}ms`);
        } else {
            error(`${failed} of ${passed + failed} tests failed in ${totalTime}ms`);
            process.exitCode = 1;
        }
    });
