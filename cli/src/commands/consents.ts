import { Command } from 'commander';
import chalk from 'chalk';
import inquirer from 'inquirer';
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

async function listConsents(options: { status?: string; agent?: string; limit?: string }) {
  const client = getClient();
  const spinner = ui.spinner('Fetching consents...');
  spinner.start();

  try {
    const response = await client.listConsents(options.status);
    spinner.stop();

    if (!response.data || response.data.length === 0) {
      console.log(ui.warn('No consents found.'));
      return;
    }

    console.log(ui.header(`Consents (${response.data.length})`));

    const rows = response.data.map((c: any) => [
      chalk.gray(c.id?.substring(0, 8) || 'N/A'),
      chalk.cyan(c.agentName || c.agentId || 'unknown'),
      c.action || 'N/A',
      c.resource || c.merchant || 'N/A',
      c.amount ? ui.formatAmount(c.amount) : '-',
      c.status === 'approved' ? chalk.green('APPROVED') :
      c.status === 'denied' ? chalk.red('DENIED') :
      c.status === 'pending' ? chalk.yellow('PENDING') :
      c.status === 'revoked' ? chalk.gray('REVOKED') :
      chalk.gray(c.status?.toUpperCase() || 'UNKNOWN'),
      c.createdAt ? ui.formatDate(c.createdAt) : 'N/A',
    ]);

    console.log(ui.table(
      ['ID', 'Agent', 'Action', 'Resource', 'Amount', 'Status', 'Created'],
      rows
    ));
  } catch (err: any) {
    spinner.stop();
    console.log(ui.error(`Failed to fetch consents: ${err.message}`));
  }
}

async function approveConsent(consentId: string) {
  const client = getClient();

  const { confirm } = await inquirer.prompt([{
    type: 'confirm',
    name: 'confirm',
    message: `Approve consent ${chalk.cyan(consentId)}?`,
    default: true,
  }]);

  if (!confirm) {
    console.log(ui.warn('Cancelled.'));
    return;
  }

  const spinner = ui.spinner('Approving consent...');
  spinner.start();

  try {
    await client.approveConsent(consentId);
    spinner.stop();
    console.log(ui.success(`Consent ${consentId} approved.`));
  } catch (err: any) {
    spinner.stop();
    console.log(ui.error(`Failed to approve: ${err.message}`));
  }
}

async function denyConsent(consentId: string) {
  const client = getClient();

  const { reason } = await inquirer.prompt([{
    type: 'input',
    name: 'reason',
    message: 'Reason for denial (optional):',
  }]);

  const { confirm } = await inquirer.prompt([{
    type: 'confirm',
    name: 'confirm',
    message: `Deny consent ${chalk.cyan(consentId)}?`,
    default: false,
  }]);

  if (!confirm) {
    console.log(ui.warn('Cancelled.'));
    return;
  }

  const spinner = ui.spinner('Denying consent...');
  spinner.start();

  try {
    await client.denyConsent(consentId, reason);
    spinner.stop();
    console.log(ui.success(`Consent ${consentId} denied.`));
  } catch (err: any) {
    spinner.stop();
    console.log(ui.error(`Failed to deny: ${err.message}`));
  }
}

async function revokeConsent(consentId: string) {
  const client = getClient();

  const { confirm } = await inquirer.prompt([{
    type: 'confirm',
    name: 'confirm',
    message: chalk.red(`Revoke consent ${chalk.cyan(consentId)}? This cannot be undone.`),
    default: false,
  }]);

  if (!confirm) {
    console.log(ui.warn('Cancelled.'));
    return;
  }

  const spinner = ui.spinner('Revoking consent...');
  spinner.start();

  try {
    await client.revokeConsent(consentId);
    spinner.stop();
    console.log(ui.success(`Consent ${consentId} revoked.`));
  } catch (err: any) {
    spinner.stop();
    console.log(ui.error(`Failed to revoke: ${err.message}`));
  }
}

export function registerConsentsCommand(program: Command) {
  const cmd = program
    .command('consents')
    .description('Manage agent consents');

  cmd
    .command('list')
    .description('List all consents')
    .option('-s, --status <status>', 'Filter by status: pending, approved, denied, revoked')
    .option('-a, --agent <id>', 'Filter by agent ID')
    .option('-l, --limit <n>', 'Max results', '25')
    .action(listConsents);

  cmd
    .command('approve <id>')
    .description('Approve a pending consent')
    .action(approveConsent);

  cmd
    .command('deny <id>')
    .description('Deny a pending consent')
    .action(denyConsent);

  cmd
    .command('revoke <id>')
    .description('Revoke an active consent')
    .action(revokeConsent);
}
