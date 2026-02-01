import { Command } from 'commander';
import chalk from 'chalk';
import { getConfig } from '../config';
import { AgentAuthClient } from '../api';
import * as ui from '../ui';

function getClient(): AgentAuthClient {
  const config = getConfig();
  if (!config.apiKey) {
    console.log(ui.error('Not logged in. Run: agentauth login'));
    process.exit(1);
  }
  return new AgentAuthClient(config.apiKey, config.apiUrl);
}

function clearScreen() {
  process.stdout.write('\x1B[2J\x1B[0f');
}

function drawBox(title: string, content: string[], width: number): string {
  const purple = chalk.hex('#a78bfa');
  const lines: string[] = [];
  const innerWidth = width - 4;

  lines.push(purple(`  ┌─ ${title} ${'─'.repeat(Math.max(0, innerWidth - title.length - 2))}┐`));
  for (const line of content) {
    const stripped = line.replace(/\x1B\[[0-9;]*m/g, '');
    const padding = Math.max(0, innerWidth - stripped.length);
    lines.push(purple('  │ ') + line + ' '.repeat(padding) + purple(' │'));
  }
  lines.push(purple(`  └${'─'.repeat(innerWidth + 2)}┘`));
  return lines.join('\n');
}

function drawStatCard(label: string, value: string, color: string): string[] {
  return [
    chalk.gray(label),
    (chalk as any)[color]?.bold?.(value) || chalk.white.bold(value),
  ];
}

async function renderDashboard(client: AgentAuthClient): Promise<string> {
  const lines: string[] = [];
  const width = Math.min(process.stdout.columns || 80, 80);

  // Header
  const purple = chalk.hex('#a78bfa');
  lines.push('');
  lines.push(purple.bold('  ╔═══════════════════════════════════════════════════════════════╗'));
  lines.push(purple.bold('  ║              ') + chalk.white.bold('AGENTAUTH DASHBOARD') + purple.bold('                          ║'));
  lines.push(purple.bold('  ╚═══════════════════════════════════════════════════════════════╝'));
  lines.push('');

  // Connection status
  const config = getConfig();
  lines.push(chalk.green('  ● Connected') + chalk.gray(` to ${config.apiUrl}`));
  lines.push('');

  try {
    const stats = await client.getStats();
    const data = stats.data || {} as any;

    // Stats cards
    const statsContent = [
      `${chalk.white.bold(String(data.actionsToday || 0).padEnd(12))} ${chalk.gray('Actions Today')}     ${chalk.white.bold(ui.formatAmount(data.totalVolume || 0).padEnd(12))} ${chalk.gray('Volume')}`,
      `${chalk.green.bold(String((data.approvalRate || 0).toFixed(1) + '%').padEnd(12))} ${chalk.gray('Approval Rate')}     ${chalk.cyan.bold(String((data.averageLatencyMs || 0).toFixed(0) + 'ms').padEnd(12))} ${chalk.gray('Avg Latency')}`,
      `${chalk.white.bold(String(data.activeAgents || data.totalAgents || 0).padEnd(12))} ${chalk.gray('Active Agents')}     ${chalk.yellow.bold(String(data.pendingConsents || 0).padEnd(12))} ${chalk.gray('Pending Consents')}`,
    ];
    lines.push(drawBox('Stats', statsContent, width));
    lines.push('');

    // Recent activity
    const recentActivity: any[] = data.recentActivity || [];
    if (recentActivity.length > 0) {
      const activityLines: string[] = [];
      const displayCount = Math.min(recentActivity.length, 10);

      for (let i = 0; i < displayCount; i++) {
        const entry = recentActivity[i];
        const decision = entry.decision || 'unknown';

        let icon: string;
        switch (decision.toLowerCase()) {
          case 'authorized':
          case 'allowed':
            icon = chalk.green('✓');
            break;
          case 'denied':
            icon = chalk.red('✗');
            break;
          case 'pending':
            icon = chalk.yellow('⏳');
            break;
          default:
            icon = chalk.gray('·');
        }

        const agent = chalk.cyan((entry.agentName || entry.agentId || 'unknown').substring(0, 20).padEnd(20));
        const amount = entry.amount ? chalk.white(ui.formatAmount(entry.amount).padEnd(12)) : chalk.gray('-'.padEnd(12));
        const merchant = chalk.gray((entry.merchant || '').substring(0, 20).padEnd(20));
        const time = chalk.gray(ui.formatDate(entry.timestamp || new Date().toISOString()));

        activityLines.push(`${icon} ${agent} ${amount} ${merchant} ${time}`);
      }
      lines.push(drawBox('Recent Activity', activityLines, width));
    } else {
      lines.push(drawBox('Recent Activity', [chalk.gray('No recent activity')], width));
    }
  } catch (err: any) {
    lines.push(drawBox('Error', [chalk.red(`Failed to fetch data: ${err.message}`)], width));
  }

  lines.push('');
  lines.push(chalk.gray('  Keyboard: ') +
    chalk.white('[r]') + chalk.gray('efresh  ') +
    chalk.white('[a]') + chalk.gray('gents  ') +
    chalk.white('[p]') + chalk.gray('olicies  ') +
    chalk.white('[l]') + chalk.gray('ogs  ') +
    chalk.white('[k]') + chalk.gray('eys  ') +
    chalk.white('[q]') + chalk.gray('uit'));
  lines.push(chalk.gray(`  Auto-refresh every 5s  |  Last updated: ${new Date().toLocaleTimeString()}`));

  return lines.join('\n');
}

async function runDashboard() {
  const client = getClient();

  clearScreen();

  // Initial render
  const output = await renderDashboard(client);
  console.log(output);

  // Auto-refresh every 5 seconds
  const refreshInterval = setInterval(async () => {
    try {
      clearScreen();
      const output = await renderDashboard(client);
      console.log(output);
    } catch {
      // Silently handle refresh errors
    }
  }, 5000);

  // Handle keyboard input
  if (process.stdin.isTTY) {
    process.stdin.setRawMode(true);
    process.stdin.resume();
    process.stdin.setEncoding('utf8');

    process.stdin.on('data', async (key: string) => {
      switch (key) {
        case 'q':
        case '\u0003': // Ctrl+C
          clearInterval(refreshInterval);
          process.stdin.setRawMode(false);
          clearScreen();
          console.log(chalk.gray('  Dashboard closed.'));
          process.exit(0);
          break;
        case 'r':
          clearScreen();
          console.log(chalk.gray('  Refreshing...'));
          try {
            const freshOutput = await renderDashboard(client);
            clearScreen();
            console.log(freshOutput);
          } catch {
            // Handle error
          }
          break;
        case 'a':
          clearInterval(refreshInterval);
          process.stdin.setRawMode(false);
          clearScreen();
          console.log(chalk.gray('  Tip: Run `agentauth agents list`'));
          process.exit(0);
          break;
        case 'p':
          clearInterval(refreshInterval);
          process.stdin.setRawMode(false);
          clearScreen();
          console.log(chalk.gray('  Tip: Run `agentauth policies list`'));
          process.exit(0);
          break;
        case 'l':
          clearInterval(refreshInterval);
          process.stdin.setRawMode(false);
          clearScreen();
          console.log(chalk.gray('  Tip: Run `agentauth logs stream`'));
          process.exit(0);
          break;
        case 'k':
          clearInterval(refreshInterval);
          process.stdin.setRawMode(false);
          clearScreen();
          console.log(chalk.gray('  Tip: Run `agentauth keys list`'));
          process.exit(0);
          break;
      }
    });
  }
}

export function registerDashboardCommand(program: Command) {
  program
    .command('dashboard')
    .description('Open interactive TUI dashboard')
    .action(runDashboard);
}
