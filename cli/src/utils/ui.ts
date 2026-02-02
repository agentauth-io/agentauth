/**
 * AgentAuth CLI - Clean Terminal UI
 * Minimal, fast, professional terminal interface
 */
import chalk from "chalk";
import ora, { Ora } from "ora";

// ═══════════════════════════════════════════════════════════════════════════
// COLOR PALETTE - Monochrome with accent
// ═══════════════════════════════════════════════════════════════════════════

export const colors = {
    // Brand
    primary: chalk.cyan,
    secondary: chalk.magenta,
    accent: chalk.cyan,
    
    // Status
    success: chalk.green,
    warning: chalk.yellow,
    error: chalk.red,
    info: chalk.blue,
    
    // Neutral
    muted: chalk.gray,
    dim: chalk.dim,
    subtle: chalk.dim.gray,
    white: chalk.white,
    bold: chalk.bold,
    
    // Gradient simulation (simplified)
    gradient: (text: string) => chalk.cyan(text),
};

// ═══════════════════════════════════════════════════════════════════════════
// ICONS - ASCII only, no unicode symbols
// ═══════════════════════════════════════════════════════════════════════════

export const icons = {
    success: colors.success("+"),
    error: colors.error("x"),
    warning: colors.warning("!"),
    info: colors.info("i"),
    pending: colors.warning("~"),
    active: colors.success("*"),
    inactive: colors.muted("-"),
    arrow: colors.primary(">"),
    arrowRight: colors.dim(">"),
    bullet: colors.dim("-"),
    check: colors.success("+"),
    cross: colors.error("x"),
    dot: colors.muted("."),
    star: colors.warning("*"),
    lock: colors.muted("[locked]"),
    key: colors.warning("[key]"),
    agent: colors.accent("[agent]"),
    money: colors.success("$"),
    clock: colors.muted("[time]"),
    shield: colors.primary("[auth]"),
    lightning: colors.primary(">"),
};

// ═══════════════════════════════════════════════════════════════════════════
// BANNER - Compact, clean
// ═══════════════════════════════════════════════════════════════════════════

export const banner = () => {
    const line1 = colors.bold.white("AgentAuth CLI");
    const tagline = colors.dim("Authorization Infrastructure for AI Agents");
    const ver = colors.muted("v1.0.0");
    
    return `\n  ${line1} ${colors.dim("-")} ${tagline}\n  ${ver}\n`;
};

export const miniBanner = () => {
    return colors.bold("AgentAuth") + colors.dim(" | ");
};

// ═══════════════════════════════════════════════════════════════════════════
// BOX DRAWING - Simple borders
// ═══════════════════════════════════════════════════════════════════════════

export interface BoxOptions {
    title?: string;
    padding?: number;
    borderColor?: typeof chalk;
    width?: number;
}

export const box = (content: string | string[], options: BoxOptions = {}) => {
    const {
        title,
        padding = 1,
        width = 60,
    } = options;
    
    const lines = Array.isArray(content) ? content : content.split("\n");
    const innerWidth = width - 4;
    const border = colors.dim;
    
    let result = "";
    
    // Top border
    if (title) {
        result += border("+") + border("-".repeat(2)) + ` ${colors.bold(title)} ` + 
                  border("-".repeat(width - title.length - 6)) + border("+") + "\n";
    } else {
        result += border("+" + "-".repeat(width - 2) + "+") + "\n";
    }
    
    // Padding
    for (let i = 0; i < padding; i++) {
        result += border("|") + " ".repeat(width - 2) + border("|") + "\n";
    }
    
    // Content
    for (const line of lines) {
        const stripped = stripAnsi(line);
        const pad = Math.max(0, innerWidth - stripped.length);
        result += border("|") + " " + line + " ".repeat(pad) + " " + border("|") + "\n";
    }
    
    // Padding
    for (let i = 0; i < padding; i++) {
        result += border("|") + " ".repeat(width - 2) + border("|") + "\n";
    }
    
    // Bottom border
    result += border("+" + "-".repeat(width - 2) + "+");
    
    return result;
};

// ═══════════════════════════════════════════════════════════════════════════
// STATUS BADGES - Clean text labels
// ═══════════════════════════════════════════════════════════════════════════

export const statusBadge = (status: string) => {
    const badges: Record<string, string> = {
        active: colors.success.bold("[ACTIVE]"),
        inactive: colors.muted("[INACTIVE]"),
        pending: colors.warning("[PENDING]"),
        approved: colors.success.bold("[APPROVED]"),
        denied: colors.error.bold("[DENIED]"),
        expired: colors.muted("[EXPIRED]"),
        revoked: colors.error("[REVOKED]"),
        connected: colors.success("[CONNECTED]"),
        disconnected: colors.error("[DISCONNECTED]"),
        live: colors.success.bold("[LIVE]"),
        test: colors.warning("[TEST]"),
    };
    
    return badges[status.toLowerCase()] || colors.muted(`[${status.toUpperCase()}]`);
};

// ═══════════════════════════════════════════════════════════════════════════
// SPINNERS - Minimal
// ═══════════════════════════════════════════════════════════════════════════

export const spinner = (text: string): Ora => {
    return ora({
        text: colors.dim(text),
        spinner: "dots",
        color: "cyan",
    });
};

export const taskList = async (tasks: Array<{ name: string; task: () => Promise<boolean> }>) => {
    const results: Array<{ name: string; success: boolean }> = [];
    
    for (const { name, task } of tasks) {
        const spin = spinner(name).start();
        try {
            const ok = await task();
            if (ok) {
                spin.succeed(colors.dim(name));
            } else {
                spin.fail(colors.dim(name));
            }
            results.push({ name, success: ok });
        } catch {
            spin.fail(colors.dim(name));
            results.push({ name, success: false });
        }
    }
    
    return results;
};

// ═══════════════════════════════════════════════════════════════════════════
// TABLES - Clean, aligned
// ═══════════════════════════════════════════════════════════════════════════

export interface TableColumn {
    key: string;
    header: string;
    width?: number;
    align?: "left" | "right" | "center";
}

export const table = (data: Record<string, unknown>[], columns: TableColumn[]) => {
    if (data.length === 0) {
        return colors.dim("  No data");
    }
    
    // Calculate widths
    const colWidths = columns.map(col => {
        const headerLen = col.header.length;
        const maxDataLen = Math.max(...data.map(row => {
            const val = String(row[col.key] ?? "");
            return stripAnsi(val).length;
        }));
        return col.width || Math.max(headerLen, maxDataLen, 4);
    });
    
    let result = "";
    
    // Header
    result += "  " + columns.map((col, i) => {
        return colors.bold(padString(col.header, colWidths[i], col.align));
    }).join("  ") + "\n";
    
    // Separator
    result += "  " + colWidths.map(w => colors.dim("-".repeat(w))).join("  ") + "\n";
    
    // Data rows
    data.forEach(row => {
        result += "  " + columns.map((col, i) => {
            const val = String(row[col.key] ?? "");
            return padString(val, colWidths[i], col.align);
        }).join("  ") + "\n";
    });
    
    return result;
};

// ═══════════════════════════════════════════════════════════════════════════
// KEY-VALUE DISPLAY
// ═══════════════════════════════════════════════════════════════════════════

export const keyValue = (pairs: Array<[string, string | number | boolean]>, options: { indent?: number } = {}) => {
    const indent = " ".repeat(options.indent || 2);
    const maxKeyLen = Math.max(...pairs.map(([k]) => k.length));
    
    return pairs.map(([key, value]) => {
        const paddedKey = key.padEnd(maxKeyLen);
        let formattedValue: string;
        
        if (typeof value === "boolean") {
            formattedValue = value ? colors.success("Yes") : colors.error("No");
        } else {
            formattedValue = colors.white(String(value));
        }
        
        return `${indent}${colors.dim(paddedKey)}  ${formattedValue}`;
    }).join("\n");
};

// ═══════════════════════════════════════════════════════════════════════════
// HEADERS & DIVIDERS
// ═══════════════════════════════════════════════════════════════════════════

export const header = (text: string, _icon?: string) => {
    return `\n${colors.bold.white(text)}\n${colors.dim("-".repeat(Math.max(text.length, 20)))}\n`;
};

export const subheader = (text: string) => {
    return `\n${colors.dim(">")} ${colors.bold(text)}\n`;
};

export const divider = (width = 40) => {
    return colors.dim("-".repeat(width));
};

// ═══════════════════════════════════════════════════════════════════════════
// MESSAGES
// ═══════════════════════════════════════════════════════════════════════════

export const success = (message: string) => {
    console.log(`${icons.success} ${colors.success(message)}`);
};

export const error = (message: string, details?: string) => {
    console.log(`${icons.error} ${colors.error(message)}`);
    if (details) {
        console.log(`  ${colors.dim(details)}`);
    }
};

export const warning = (message: string) => {
    console.log(`${icons.warning} ${colors.warning(message)}`);
};

export const info = (message: string) => {
    console.log(`${icons.info} ${colors.info(message)}`);
};

export const hint = (message: string) => {
    console.log(`  ${colors.dim("Tip: " + message)}`);
};

// Log a line with prefix
export const log = (prefix: string, message: string) => {
    console.log(`${colors.dim(prefix)} ${message}`);
};

// ═══════════════════════════════════════════════════════════════════════════
// COMMAND HELP
// ═══════════════════════════════════════════════════════════════════════════

export const commandHelp = (commands: Array<{ name: string; description: string; alias?: string }>) => {
    const maxNameLen = Math.max(...commands.map(c => c.name.length));
    
    return commands.map(cmd => {
        const padding = " ".repeat(maxNameLen - cmd.name.length + 4);
        return `  ${colors.primary(cmd.name)}${padding}${colors.dim(cmd.description)}`;
    }).join("\n");
};

export const optionHelp = (options: Array<{ flag: string; description: string }>) => {
    const maxFlagLen = Math.max(...options.map(o => o.flag.length));
    
    return options.map(opt => {
        const padding = " ".repeat(maxFlagLen - opt.flag.length + 4);
        return `  ${colors.accent(opt.flag)}${padding}${colors.dim(opt.description)}`;
    }).join("\n");
};

// ═══════════════════════════════════════════════════════════════════════════
// UTILITIES
// ═══════════════════════════════════════════════════════════════════════════

export const stripAnsi = (str: string): string => {
    // eslint-disable-next-line no-control-regex
    return str.replace(/\x1B[[(?);]{0,2}(;?\d)*./g, "");
};

const padString = (str: string, width: number, align: "left" | "right" | "center" = "left"): string => {
    const stripped = stripAnsi(str);
    const padding = Math.max(0, width - stripped.length);
    
    switch (align) {
        case "right":
            return " ".repeat(padding) + str;
        case "center":
            const left = Math.floor(padding / 2);
            const right = padding - left;
            return " ".repeat(left) + str + " ".repeat(right);
        default:
            return str + " ".repeat(padding);
    }
};

// ═══════════════════════════════════════════════════════════════════════════
// FORMATTING HELPERS
// ═══════════════════════════════════════════════════════════════════════════

export const formatCurrency = (amount: number, currency = "USD") => {
    return new Intl.NumberFormat("en-US", {
        style: "currency",
        currency,
    }).format(amount);
};

export const formatNumber = (num: number) => {
    return new Intl.NumberFormat("en-US").format(num);
};

export const formatDate = (date: Date | string) => {
    const d = typeof date === "string" ? new Date(date) : date;
    return d.toLocaleDateString("en-US", {
        year: "numeric",
        month: "short",
        day: "numeric",
    });
};

export const formatRelativeTime = (date: Date | string) => {
    const d = typeof date === "string" ? new Date(date) : date;
    const now = new Date();
    const diff = now.getTime() - d.getTime();
    
    const seconds = Math.floor(diff / 1000);
    const minutes = Math.floor(seconds / 60);
    const hours = Math.floor(minutes / 60);
    const days = Math.floor(hours / 24);
    
    if (days > 0) return `${days}d ago`;
    if (hours > 0) return `${hours}h ago`;
    if (minutes > 0) return `${minutes}m ago`;
    return "just now";
};

// ═══════════════════════════════════════════════════════════════════════════
// TERMINAL OUTPUT HELPERS
// ═══════════════════════════════════════════════════════════════════════════

// Print a command-style line
export const cmd = (command: string) => {
    console.log(`${colors.dim("$")} ${colors.white(command)}`);
};

// Print output line
export const out = (line: string) => {
    console.log(`  ${line}`);
};

// Print a step in a process
export const step = (num: number, text: string, status?: "done" | "pending" | "error") => {
    const prefix = status === "done" ? colors.success("+") :
                   status === "error" ? colors.error("x") :
                   colors.dim(`${num}.`);
    console.log(`${prefix} ${text}`);
};

// Print a tree structure
export const tree = (items: Array<{ name: string; children?: string[] }>) => {
    let result = "";
    items.forEach((item, i) => {
        const isLast = i === items.length - 1;
        const prefix = isLast ? "`-" : "|-";
        result += `${colors.dim(prefix)} ${item.name}\n`;
        
        if (item.children) {
            item.children.forEach((child, j) => {
                const childIsLast = j === item.children!.length - 1;
                const childPrefix = isLast ? "   " : "|  ";
                const childBranch = childIsLast ? "`-" : "|-";
                result += `${colors.dim(childPrefix + childBranch)} ${colors.dim(child)}\n`;
            });
        }
    });
    return result;
};

// Progress bar
export const progressBar = (current: number, total: number, width = 20) => {
    const percent = Math.min(current / total, 1);
    const filled = Math.round(width * percent);
    const empty = width - filled;
    
    const bar = colors.primary("=".repeat(filled)) + colors.dim("-".repeat(empty));
    const pct = `${Math.round(percent * 100)}%`;
    
    return `[${bar}] ${pct}`;
};

// Truncate text
export const truncate = (str: string, maxLen: number) => {
    if (str.length <= maxLen) return str;
    return str.slice(0, maxLen - 3) + "...";
};
