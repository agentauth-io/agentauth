import { Command } from 'commander';
import * as config from '../config';
import { AgentAuthClient } from '../api';
import * as ui from '../ui';

export function registerStatusCommand(program: Command) {
  program.addCommand(statusCommand);
}

export const statusCommand = new Command('status')
  .description('Show connection status and account information')
  .option('--json', 'Output as JSON')
  .action(async (options) => {
    console.log(ui.header('AgentAuth Status'));

    // Check if configured
    if (!config.isConfigured()) {
      console.log(ui.error('Not authenticated. Run `agentauth login` first.'));
      process.exit(1);
    }

    const configInfo = config.getAll();

    // Show config info
    console.log(ui.subheader('Configuration'));
    console.log(ui.detailTable([
      ['API Key', String(configInfo.apiKey)],
      ['API URL', String(configInfo.apiUrl)],
      ['Output Format', String(configInfo.outputFormat)],
      ['Colors', configInfo.colorEnabled ? 'Enabled' : 'Disabled'],
      ['Config Path', String(configInfo.configPath)],
    ]));

    // Test connection
    const spin = ui.spinner('Checking connection...');
    spin.start();

    try {
      const client = new AgentAuthClient(config.getApiKey(), config.getApiUrl());
      const response = await client.getAccount();

      spin.stop();

      if (response.success && response.data) {
        const account = response.data;
        const usage = account.usage;

        console.log(ui.success('Connected to AgentAuth API\n'));

        if (options.json) {
          console.log(JSON.stringify({ config: configInfo, account: response.data }, null, 2));
          return;
        }

        // Account info
        console.log(ui.subheader('Account'));
        console.log(ui.detailTable([
          ['Name', account.name],
          ['Email', account.email],
          ['Organization', account.organization],
          ['Plan', ui.statusBadge(account.plan)],
          ['Member Since', ui.formatDate(account.createdAt)],
        ]));

        // Usage stats
        console.log(ui.subheader('Usage'));
        console.log(ui.detailTable([
          ['Authorizations', `${ui.formatNumber(usage.authorizationsUsed)} / ${ui.formatNumber(usage.authorizationsLimit)}`],
          ['Agents', `${ui.formatNumber(usage.agentsUsed)} / ${ui.formatNumber(usage.agentsLimit)}`],
          ['Policies', `${ui.formatNumber(usage.policiesUsed)} / ${ui.formatNumber(usage.policiesLimit)}`],
        ]));

        // Usage bars
        const authPct = (usage.authorizationsUsed / usage.authorizationsLimit) * 100;
        const agentPct = (usage.agentsUsed / usage.agentsLimit) * 100;
        const policyPct = (usage.policiesUsed / usage.policiesLimit) * 100;

        console.log(`\n  Authorizations ${usageBar(authPct)} ${ui.formatPercent(authPct)}`);
        console.log(`  Agents         ${usageBar(agentPct)} ${ui.formatPercent(agentPct)}`);
        console.log(`  Policies       ${usageBar(policyPct)} ${ui.formatPercent(policyPct)}`);
        console.log();

        if (authPct > 80) {
          console.log(ui.warn('You are approaching your authorization limit. Consider upgrading your plan.'));
        }
      } else {
        console.log(ui.error('Could not retrieve account information.'));
      }
    } catch (err: unknown) {
      spin.stop();
      const message = err instanceof Error ? err.message : 'Unknown error';
      console.log(ui.error(`Connection failed: ${message}`));

      if (message.includes('401') || message.includes('Unauthorized')) {
        console.log(ui.info('Your API key may have expired. Run `agentauth login` to re-authenticate.'));
      } else {
        console.log(ui.info(`Could not reach ${config.getApiUrl()}`));
      }

      process.exit(1);
    }
  });

/**
 * Render a usage bar
 */
function usageBar(percent: number, width: number = 30): string {
  const filled = Math.round((percent / 100) * width);
  const empty = width - filled;

  const filledStr = '█'.repeat(filled);
  const emptyStr = '░'.repeat(empty);

  if (percent >= 90) {
    return `${ui.chalk.red(filledStr)}${ui.chalk.gray(emptyStr)}`;
  } else if (percent >= 70) {
    return `${ui.chalk.yellow(filledStr)}${ui.chalk.gray(emptyStr)}`;
  } else {
    return `${ui.chalk.green(filledStr)}${ui.chalk.gray(emptyStr)}`;
  }
}
