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

async function listKeys() {
  const client = getClient();
  const spinner = ui.spinner('Fetching API keys...');
  spinner.start();

  try {
    const response = await client.listKeys();
    spinner.stop();

    if (!response.data || response.data.length === 0) {
      console.log(ui.warn('No API keys found.'));
      console.log(chalk.gray('  Create one with: agentauth keys create <name>'));
      return;
    }

    console.log(ui.header(`API Keys (${response.data.length})`));

    const rows = response.data.map((k: any) => [
      chalk.gray(k.id?.substring(0, 8) || 'N/A'),
      chalk.white(k.name || 'Unnamed'),
      chalk.cyan(k.prefix ? `${k.prefix}...` : k.key?.substring(0, 12) + '...' || 'N/A'),
      k.status === 'active' ? chalk.green('ACTIVE') : chalk.red('REVOKED'),
      k.lastUsedAt ? ui.formatDate(k.lastUsedAt) : chalk.gray('Never'),
      k.createdAt ? ui.formatDate(k.createdAt) : 'N/A',
    ]);

    console.log(ui.table(
      ['ID', 'Name', 'Key', 'Status', 'Last Used', 'Created'],
      rows
    ));
  } catch (err: any) {
    spinner.stop();
    console.log(ui.error(`Failed to fetch keys: ${err.message}`));
  }
}

async function createKey(name: string, options: { permissions?: string; expires?: string }) {
  const client = getClient();
  const spinner = ui.spinner(`Creating API key "${name}"...`);
  spinner.start();

  try {
    const response = await client.createKey({
      name,
      permissions: options.permissions ? options.permissions.split(',') : undefined,
      expiresAt: options.expires,
    });
    spinner.stop();

    console.log(ui.success('API key created successfully!'));
    console.log('');
    console.log(chalk.yellow('  ⚠ Save this key now — it will not be shown again:'));
    console.log('');
    console.log(chalk.white.bold(`  ${response.data?.key || response.data?.id || 'N/A'}`));
    console.log('');
    console.log(chalk.gray('  Name:    ') + chalk.white(name));
    if (response.data?.permissions) {
      console.log(chalk.gray('  Perms:   ') + chalk.white(response.data.permissions.join(', ')));
    }
    if (response.data?.expiresAt) {
      console.log(chalk.gray('  Expires: ') + chalk.white(response.data.expiresAt));
    }
    console.log('');
  } catch (err: any) {
    spinner.stop();
    console.log(ui.error(`Failed to create key: ${err.message}`));
  }
}

async function revokeKey(keyId: string) {
  const client = getClient();

  const { confirm } = await inquirer.prompt([{
    type: 'confirm',
    name: 'confirm',
    message: chalk.red(`Revoke API key ${chalk.cyan(keyId)}? This cannot be undone.`),
    default: false,
  }]);

  if (!confirm) {
    console.log(ui.warn('Cancelled.'));
    return;
  }

  const spinner = ui.spinner('Revoking key...');
  spinner.start();

  try {
    await client.revokeKey(keyId);
    spinner.stop();
    console.log(ui.success(`API key ${keyId} revoked.`));
  } catch (err: any) {
    spinner.stop();
    console.log(ui.error(`Failed to revoke key: ${err.message}`));
  }
}

async function rotateKey(keyId: string) {
  const client = getClient();

  const { confirm } = await inquirer.prompt([{
    type: 'confirm',
    name: 'confirm',
    message: `Rotate API key ${chalk.cyan(keyId)}? The old key will be revoked.`,
    default: false,
  }]);

  if (!confirm) {
    console.log(ui.warn('Cancelled.'));
    return;
  }

  const spinner = ui.spinner('Rotating key...');
  spinner.start();

  try {
    // Revoke old key
    await client.revokeKey(keyId);

    // Create new key with same name
    const newKey = await client.createKey({ name: `rotated-${keyId.substring(0, 8)}` });
    spinner.stop();

    console.log(ui.success('API key rotated successfully!'));
    console.log('');
    console.log(chalk.yellow('  ⚠ Save this new key now — it will not be shown again:'));
    console.log('');
    console.log(chalk.white.bold(`  ${newKey.data?.key || newKey.data?.id || 'N/A'}`));
    console.log('');
    console.log(chalk.gray(`  Old key ${keyId} has been revoked.`));
    console.log('');
  } catch (err: any) {
    spinner.stop();
    console.log(ui.error(`Failed to rotate key: ${err.message}`));
  }
}

export function registerKeysCommand(program: Command) {
  const cmd = program
    .command('keys')
    .description('Manage API keys');

  cmd
    .command('list')
    .description('List all API keys')
    .action(listKeys);

  cmd
    .command('create <name>')
    .description('Create a new API key')
    .option('-p, --permissions <perms>', 'Comma-separated permissions')
    .option('-e, --expires <date>', 'Expiration date (ISO format)')
    .action(createKey);

  cmd
    .command('revoke <id>')
    .description('Revoke an API key')
    .action(revokeKey);

  cmd
    .command('rotate <id>')
    .description('Rotate an API key (revoke old, create new)')
    .action(rotateKey);
}
