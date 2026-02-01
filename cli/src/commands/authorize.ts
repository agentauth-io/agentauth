import { Command } from 'commander';
import inquirer from 'inquirer';
import * as config from '../config';
import { AgentAuthClient } from '../api';
import * as ui from '../ui';
import { AuthorizationRequest } from '../types';

export function registerAuthorizeCommand(program: Command) {
  program.addCommand(authorizeCommand);
}

export const authorizeCommand = new Command('authorize')
  .description('Submit an authorization request')
  .option('-a, --agent <agentId>', 'Agent ID')
  .option('--action <action>', 'Action to authorize (e.g., purchase, transfer, api_call)')
  .option('--amount <amount>', 'Transaction amount in dollars', parseFloat)
  .option('-m, --merchant <merchant>', 'Merchant or target name')
  .option('-d, --description <description>', 'Description of the action')
  .option('-r, --resource <resource>', 'Resource being accessed')
  .option('-i, --interactive', 'Interactive mode - prompt for all fields')
  .option('--json', 'Output result as JSON')
  .option('--dry-run', 'Simulate without actually authorizing')
  .action(async (options) => {
    if (!config.isConfigured()) {
      console.log(ui.error('Not authenticated. Run `agentauth login` first.'));
      process.exit(1);
    }

    let request: AuthorizationRequest;

    if (options.interactive) {
      // Interactive mode
      console.log(ui.header('Authorization Request'));

      const answers = await inquirer.prompt([
        {
          type: 'input',
          name: 'agentId',
          message: 'Agent ID:',
          default: options.agent,
          validate: (input: string) => input.length > 0 || 'Agent ID is required',
        },
        {
          type: 'list',
          name: 'action',
          message: 'Action type:',
          choices: [
            'purchase',
            'transfer',
            'api_call',
            'data_access',
            'file_write',
            'email_send',
            'subscription',
            { name: 'Other (custom)', value: '_custom' },
          ],
          default: options.action,
        },
        {
          type: 'input',
          name: 'customAction',
          message: 'Custom action name:',
          when: (answers: Record<string, string>) => answers.action === '_custom',
          validate: (input: string) => input.length > 0 || 'Action name is required',
        },
        {
          type: 'input',
          name: 'resource',
          message: 'Resource (optional):',
          default: options.resource || '',
        },
        {
          type: 'number',
          name: 'amount',
          message: 'Amount in USD (optional):',
          default: options.amount,
        },
        {
          type: 'input',
          name: 'merchant',
          message: 'Merchant / target (optional):',
          default: options.merchant || '',
        },
        {
          type: 'input',
          name: 'description',
          message: 'Description (optional):',
          default: options.description || '',
        },
        {
          type: 'confirm',
          name: 'confirm',
          message: 'Submit authorization request?',
          default: true,
        },
      ]);

      if (!answers.confirm) {
        console.log(ui.warn('Authorization request cancelled.'));
        return;
      }

      request = {
        agentId: answers.agentId,
        action: answers.action === '_custom' ? answers.customAction : answers.action,
        resource: answers.resource || undefined,
        amount: answers.amount ? Number(answers.amount) : undefined,
        merchant: answers.merchant || undefined,
        description: answers.description || undefined,
      };
    } else {
      // Non-interactive mode - require agent and action
      if (!options.agent) {
        console.log(ui.error('--agent is required. Use --interactive for guided input.'));
        process.exit(1);
      }
      if (!options.action) {
        console.log(ui.error('--action is required. Use --interactive for guided input.'));
        process.exit(1);
      }

      request = {
        agentId: options.agent,
        action: options.action,
        resource: options.resource,
        amount: options.amount,
        merchant: options.merchant,
        description: options.description,
      };
    }

    // Show request summary
    console.log(ui.subheader('Request Summary'));
    const summaryPairs: [string, string][] = [
      ['Agent', request.agentId],
      ['Action', request.action],
    ];
    if (request.resource) summaryPairs.push(['Resource', request.resource]);
    if (request.amount) summaryPairs.push(['Amount', ui.formatAmount(request.amount)]);
    if (request.merchant) summaryPairs.push(['Merchant', request.merchant]);
    if (request.description) summaryPairs.push(['Description', request.description]);
    console.log(ui.detailTable(summaryPairs));

    if (options.dryRun) {
      console.log(ui.info('Dry run mode - request not submitted.'));
      return;
    }

    // Submit the request
    const spin = ui.spinner('Evaluating authorization...');
    spin.start();

    try {
      const client = new AgentAuthClient(config.getApiKey(), config.getApiUrl());
      const response = await client.authorize(request);

      spin.stop();

      if (response.success && response.data) {
        const result = response.data;

        if (options.json) {
          console.log(JSON.stringify(result, null, 2));
          return;
        }

        // Show result
        console.log(ui.subheader('Authorization Result'));
        console.log();
        console.log(`  Decision: ${ui.decisionBadge(result.decision)}`);
        console.log();

        console.log(ui.detailTable([
          ['Request ID', result.requestId],
          ['Decision', result.decision],
          ['Reason', result.reason],
          ['Policy', result.policyName || result.policyId || 'N/A'],
          ['Latency', ui.formatLatency(result.latencyMs)],
          ['Evaluated At', ui.formatTimestamp(result.evaluatedAt)],
        ]));

        if (result.consentId) {
          console.log(ui.info(`Consent request created: ${result.consentId}`));
          console.log(ui.info('A human reviewer needs to approve this action.'));
          console.log(ui.info('Check status with: agentauth consents list'));
        }

        if (result.conditions && result.conditions.length > 0) {
          console.log(ui.subheader('Conditions'));
          result.conditions.forEach(condition => {
            console.log(`  ${ui.chalk.dim('•')} ${condition}`);
          });
        }

        // Set exit code based on decision
        if (result.decision === 'DENIED') {
          process.exit(2);
        } else if (result.decision === 'PENDING') {
          process.exit(3);
        }
      } else {
        console.log(ui.error('Authorization request failed.'));
        if (response.error) {
          console.log(ui.error(response.error));
        }
        process.exit(1);
      }
    } catch (err: unknown) {
      spin.stop();
      const message = err instanceof Error ? err.message : 'Unknown error';
      console.log(ui.error(`Authorization failed: ${message}`));
      process.exit(1);
    }
  });
