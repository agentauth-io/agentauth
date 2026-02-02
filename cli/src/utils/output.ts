// Output formatting utilities
import chalk from "chalk";
import { table } from "table";

export type OutputFormat = "table" | "json" | "yaml";

export function formatTable(data: Record<string, unknown>[], columns: string[]): string {
    if (data.length === 0) {
        return chalk.gray("No data found");
    }

    const headers = columns.map((col) => chalk.bold.cyan(col.toUpperCase()));
    const rows = data.map((row) =>
        columns.map((col) => {
            const value = row[col];
            if (value === undefined || value === null) return chalk.gray("—");
            if (typeof value === "boolean") return value ? chalk.green("✓") : chalk.red("✗");
            return String(value);
        })
    );

    return table([headers, ...rows], {
        border: {
            topBody: chalk.gray("─"),
            topJoin: chalk.gray("┬"),
            topLeft: chalk.gray("┌"),
            topRight: chalk.gray("┐"),
            bottomBody: chalk.gray("─"),
            bottomJoin: chalk.gray("┴"),
            bottomLeft: chalk.gray("└"),
            bottomRight: chalk.gray("┘"),
            bodyLeft: chalk.gray("│"),
            bodyRight: chalk.gray("│"),
            bodyJoin: chalk.gray("│"),
            joinBody: chalk.gray("─"),
            joinLeft: chalk.gray("├"),
            joinRight: chalk.gray("┤"),
            joinJoin: chalk.gray("┼"),
        },
    });
}

export function formatJson(data: unknown): string {
    return JSON.stringify(data, null, 2);
}

export function formatYaml(data: unknown): string {
    function toYaml(obj: unknown, indent = 0): string {
        const spaces = "  ".repeat(indent);
        
        if (obj === null || obj === undefined) {
            return "null";
        }
        
        if (typeof obj === "string") {
            return obj.includes("\n") ? `|\n${obj.split("\n").map(l => spaces + "  " + l).join("\n")}` : obj;
        }
        
        if (typeof obj !== "object") {
            return String(obj);
        }
        
        if (Array.isArray(obj)) {
            if (obj.length === 0) return "[]";
            return obj.map(item => `${spaces}- ${toYaml(item, indent + 1)}`).join("\n");
        }
        
        const entries = Object.entries(obj as Record<string, unknown>);
        if (entries.length === 0) return "{}";
        
        return entries
            .map(([key, value]) => {
                if (typeof value === "object" && value !== null) {
                    return `${spaces}${key}:\n${toYaml(value, indent + 1)}`;
                }
                return `${spaces}${key}: ${toYaml(value, indent)}`;
            })
            .join("\n");
    }
    
    return toYaml(data);
}

export function formatOutput(data: unknown, format: OutputFormat): string {
    switch (format) {
        case "json":
            return formatJson(data);
        case "yaml":
            return formatYaml(data);
        case "table":
        default:
            if (Array.isArray(data) && data.length > 0) {
                const columns = Object.keys(data[0] as Record<string, unknown>);
                return formatTable(data as Record<string, unknown>[], columns);
            }
            return formatJson(data);
    }
}

export function success(message: string): void {
    console.log(chalk.green("✓"), message);
}

export function error(message: string): void {
    console.error(chalk.red("✗"), message);
}

export function warning(message: string): void {
    console.warn(chalk.yellow("⚠"), message);
}

export function info(message: string): void {
    console.log(chalk.blue("ℹ"), message);
}

export function heading(text: string): void {
    console.log(chalk.bold.white(`\n${text}`));
    console.log(chalk.gray("─".repeat(text.length)));
}

export function keyValue(key: string, value: string | number | boolean): void {
    const formattedValue = typeof value === "boolean" 
        ? (value ? chalk.green("Yes") : chalk.red("No"))
        : chalk.white(String(value));
    console.log(`  ${chalk.gray(key + ":")} ${formattedValue}`);
}
