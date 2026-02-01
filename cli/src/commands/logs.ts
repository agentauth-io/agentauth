import { Command } from 'commander';
import chalk from 'chalk';
import fs from 'fs';
import { getConfig } from '../config';
import { AgentAuthClient } from '../api';
import * as ui from '../ui';
import { LogEntry } from '../types';

function getClient(): AgentAuthClient {
  const config = getConfig();
  if (!config.apiKey) {
    console.log(ui.error('Not logged in. Run: agentauth login'));
    process.exit(1);
  }
  return new AgentAuthClient(config.apiKey, config.apiUrl);
}

function formatLogLine(log: LogEntry): string {
  const time = chalk.gray(ui.formatDate(log.timestamp));
  const agent = chalk.cyan(log.agentName || log.agentId || 'unknown');
  const action = chalk.white(log.action || 'unknown');

  let decision = '';
  switch (log.decision) {
    case 'ALLOWED': decision = chalk.green('✓ ALLOWED'); break;
    case 'DENIED': decision = chalk.red('✗ DENIED'); break;
    case 'PENDING': decision = chalk.yellow('⏳ PENDING'); break;
    default: decision = chalk.gray(log.decision || 'N/A');
  }

  const amount = log.amount ? chalk.white(ui.formatAmount(log.amount)) : '';
  const merchant = log.merchant ? chalk.gray(`@ ${log.merchant}`) : '';
  const latency = chalk.gray(`${log.latencyMs || 0}ms`);

  return `${time}  ${decision}  ${agent}  ${action}  ${amount}  ${merchant}  ${latency}`;
}

async function streamLogs(options: { agent?: string; decision?: string }) {
  const client = getClient();

  console.log(ui.header('Live Log Stream'));
  console.log(chalk.gray('  Streaming authorization logs in real-time...'));
  console.log(chalk.gray('  Press Ctrl+C to stop.\n'));

  let lastTimestamp = new Date().toISOString();

  const poll = async () => {
    try {
      const response = await client.listLogs({
        agentId: options.agent,
        decision: options.decision,
        startDate: lastTimestamp,
        limit: 20,
      });

      if (response.data && response.data.length > 0) {
        for (const log of response.data) {
          console.log(formatLogLine(log));
          if (log.timestamp > lastTimestamp) {
            lastTimestamp = log.timestamp;
          }
        }
      }
    } catch (err: any) {
      console.log(ui.error(`Stream error: ${err.message}`));
    }
  };

  // Initial fetch
  try {
    const response = await client.listLogs({
      agentId: options.agent,
      decision: options.decision,
      limit: 20,
    });

    if (response.data && response.data.length > 0) {
      for (const log of response.data) {
        console.log(formatLogLine(log));
        if (log.timestamp > lastTimestamp) {
          lastTimestamp = log.timestamp;
        }
      }
    } else {
      console.log(chalk.gray('  Waiting for activity...\n'));
    }
  } catch (err: any) {
    console.log(ui.error(`Failed to fetch initial logs: ${err.message}`));
  }

  // Poll every 3 seconds
  const interval = setInterval(poll, 3000);
  process.on('SIGINT', () => {
    clearInterval(interval);
    console.log(chalk.gray('\n  Stream stopped.'));
    process.exit(0);
  });
}

async function searchLogs(query: string, options: { agent?: string; decision?: string; limit?: string; from?: string; to?: string }) {
  const client = getClient();
  const spinner = ui.spinner(`Searching logs for "${query}"...`);
  spinner.start();

  try {
    const response = await client.listLogs({
      search: query,
      agentId: options.agent,
      decision: options.decision,
      startDate: options.from,
      endDate: options.to,
      limit: options.limit ? parseInt(options.limit) : 50,
    });
    spinner.stop();

    if (!response.data || response.data.length === 0) {
      console.log(ui.warn('No logs found matching your query.'));
      return;
    }

    console.log(ui.header(`Search Results: "${query}" (${response.data.length} entries)`));

    for (const log of response.data) {
      console.log(formatLogLine(log));
    }
  } catch (err: any) {
    spinner.stop();
    console.log(ui.error(`Search failed: ${err.message}`));
  }
}

async function exportLogs(options: { output?: string; format?: string; limit?: string; from?: string; to?: string }) {
  const client = getClient();
  const format = options.format || 'json';
  const output = options.output || `agentauth-logs-${Date.now()}.${format}`;
  const spinner = ui.spinner('Exporting logs...');
  spinner.start();

  try {
    const response = await client.listLogs({
      startDate: options.from,
      endDate: options.to,
      limit: options.limit ? parseInt(options.limit) : 1000,
    });
    spinner.stop();

    if (!response.data || response.data.length === 0) {
      console.log(ui.warn('No logs to export.'));
      return;
    }

    let content: string;
    if (format === 'csv') {
      const headers = 'timestamp,agent,action,decision,amount,merchant,latency_ms\n';
      const rows = response.data.map((l: LogEntry) =>
        `${l.timestamp},${l.agentName || l.agentId},${l.action},${l.decision},${l.amount || ''},${l.merchant || ''},${l.latencyMs}`
      ).join('\n');
      content = headers + rows;
    } else {
      content = JSON.stringify(response.data, null, 2);
    }

    fs.writeFileSync(output, content);
    console.log(ui.success(`Exported ${response.data.length} logs to ${chalk.cyan(output)}`));
  } catch (err: any) {
    spinner.stop();
    console.log(ui.error(`Export failed: ${err.message}`));
  }
}

export function registerLogsCommand(program: Command) {
  const cmd = program
    .command('logs')
    .description('View and search authorization logs');

  cmd
    .command('stream')
    .description('Stream logs in real-time')
    .option('-a, --agent <id>', 'Filter by agent')
    .option('-d, --decision <type>', 'Filter: ALLOWED, DENIED, PENDING')
    .action(streamLogs);

  cmd
    .command('search <query>')
    .description('Search logs')
    .option('-a, --agent <id>', 'Filter by agent')
    .option('-d, --decision <type>', 'Filter by decision')
    .option('-l, --limit <n>', 'Max results', '50')
    .option('--from <date>', 'Start date (ISO format)')
    .option('--to <date>', 'End date (ISO format)')
    .action(searchLogs);

  cmd
    .command('export')
    .description('Export logs to file')
    .option('-o, --output <file>', 'Output file path')
    .option('-f, --format <type>', 'Format: json, csv', 'json')
    .option('-l, --limit <n>', 'Max entries', '1000')
    .option('--from <date>', 'Start date (ISO format)')
    .option('--to <date>', 'End date (ISO format)')
    .action(exportLogs);
}
