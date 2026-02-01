import { Command } from 'commander';
import inquirer from 'inquirer';
import * as config from '../config';
import { AgentAuthClient } from '../api';
import * as ui from '../ui';

function requireAuth(): AgentAuthClient {
  if (!config.isConfigured()) {
    console.log(ui.error('Not authenticated. Run `agentauth login` first.'));
    process.exit(1);
  }
  return new AgentAuthClient(config.getApiKey(), config.getApiUrl());
}

// ─── List Agents ────────────────────────────────────────────────────────────

const listAgents = new Command('list')
  .description('List all registered agents')
  .option('--json', 'Output as JSON')
  .option('--status <status>', 'Filter by status (active, inactive, suspended)')
  .action(async (options) => {
    const client = requireAuth();
    const spin = ui.spinner('Fetching agents...');
    spin.start();

    try {
      const response = await client.listAgents();
      spin.stop();

      let agents = response.data;

      if (options.status) {
        agents = agents.filter(a => a.status === options.status);
      }

      if (options.json) {
        console.log(JSON.stringify(agents, null, 2));
        return;
      }

      if (agents.length === 0) {
        console.log(ui.info('No agents found. Register one with `agentauth agents register`.'));
        return;
      }

      console.log(ui.header(`Agents (${agents.length})`));
      console.log(ui.table(
        ['ID', 'Name', 'Status', 'Capabilities', 'Policies', 'Last Active'],
        agents.map(agent => [
          ui.truncate(agent.id, 12),
          agent.name,
          ui.statusBadge(agent.status),
          agent.capabilities.length > 0 ? agent.capabilities.slice(0, 3).join(', ') : ui.chalk.dim('none'),
          String(agent.policies.length),
          agent.lastActiveAt ? ui.formatDate(agent.lastActiveAt) : ui.chalk.dim('never'),
        ])
      ));

      console.log(ui.chalk.dim(`  Total: ${agents.length} agents`));
    } catch (err: unknown) {
      spin.stop();
      const message = err instanceof Error ? err.message : 'Unknown error';
      console.log(ui.error(`Failed to list agents: ${message}`));
      process.exit(1);
    }
  });

// ─── Register Agent ─────────────────────────────────────────────────────────

const registerAgent = new Command('register')
  .description('Register a new agent')
  .option('--name <name>', 'Agent name')
  .option('--description <description>', 'Agent description')
  .option('--capabilities <caps>', 'Comma-separated capabilities')
  .action(async (options) => {
    const client = requireAuth();

    console.log(ui.header('Register New Agent'));

    let name = options.name;
    let description = options.description;
    let capabilities: string[] = options.capabilities ? options.capabilities.split(',').map((c: string) => c.trim()) : [];

    if (!name) {
      const answers = await inquirer.prompt([
        {
          type: 'input',
          name: 'name',
          message: 'Agent name:',
          validate: (input: string) => input.length > 0 || 'Name is required',
        },
        {
          type: 'input',
          name: 'description',
          message: 'Description (optional):',
          default: '',
        },
        {
          type: 'checkbox',
          name: 'capabilities',
          message: 'Select capabilities:',
          choices: [
            { name: 'Purchase / Financial Transactions', value: 'purchase' },
            { name: 'Data Access / Read', value: 'data_access' },
            { name: 'Data Write / Modify', value: 'data_write' },
            { name: 'API Calls (External)', value: 'api_call' },
            { name: 'Email / Notifications', value: 'email_send' },
            { name: 'File System Access', value: 'file_access' },
            { name: 'Subscription Management', value: 'subscription' },
            { name: 'User Impersonation', value: 'impersonation' },
          ],
        },
        {
          type: 'input',
          name: 'extraCapabilities',
          message: 'Additional capabilities (comma-separated, optional):',
          default: '',
        },
      ]);

      name = answers.name;
      description = answers.description;
      capabilities = [
        ...answers.capabilities,
        ...answers.extraCapabilities.split(',').map((c: string) => c.trim()).filter((c: string) => c.length > 0),
      ];
    }

    const spin = ui.spinner('Registering agent...');
    spin.start();

    try {
      const response = await client.registerAgent({
        name,
        description,
        capabilities,
      });

      spin.stop();

      if (response.success && response.data) {
        const agent = response.data;
        console.log(ui.success(`Agent "${agent.name}" registered successfully!\n`));
        console.log(ui.detailTable([
          ['ID', agent.id],
          ['Name', agent.name],
          ['Description', agent.description || ui.chalk.dim('none')],
          ['Status', ui.statusBadge(agent.status)],
          ['Capabilities', agent.capabilities.join(', ') || ui.chalk.dim('none')],
          ['Created', ui.formatTimestamp(agent.createdAt)],
        ]));
      } else {
        console.log(ui.error('Failed to register agent.'));
        if (response.error) console.log(ui.error(response.error));
      }
    } catch (err: unknown) {
      spin.stop();
      const message = err instanceof Error ? err.message : 'Unknown error';
      console.log(ui.error(`Registration failed: ${message}`));
      process.exit(1);
    }
  });

// ─── Inspect Agent ──────────────────────────────────────────────────────────

const inspectAgent = new Command('inspect')
  .description('Show detailed information about an agent')
  .argument('<id>', 'Agent ID')
  .option('--json', 'Output as JSON')
  .action(async (id: string, options) => {
    const client = requireAuth();
    const spin = ui.spinner('Fetching agent details...');
    spin.start();

    try {
      const response = await client.getAgent(id);
      spin.stop();

      if (response.success && response.data) {
        const agent = response.data;

        if (options.json) {
          console.log(JSON.stringify(agent, null, 2));
          return;
        }

        console.log(ui.header(`Agent: ${agent.name}`));
        console.log(ui.detailTable([
          ['ID', agent.id],
          ['Name', agent.name],
          ['Description', agent.description || ui.chalk.dim('none')],
          ['Status', ui.statusBadge(agent.status)],
          ['Created', ui.formatTimestamp(agent.createdAt)],
          ['Updated', ui.formatTimestamp(agent.updatedAt)],
          ['Last Active', agent.lastActiveAt ? ui.formatTimestamp(agent.lastActiveAt) : ui.chalk.dim('never')],
        ]));

        if (agent.capabilities.length > 0) {
          console.log(ui.subheader('Capabilities'));
          agent.capabilities.forEach(cap => {
            console.log(`  ${ui.chalk.green('+')} ${cap}`);
          });
        }

        if (agent.policies.length > 0) {
          console.log(ui.subheader('Assigned Policies'));
          agent.policies.forEach(policyId => {
            console.log(`  ${ui.chalk.blue('>')} ${policyId}`);
          });
        }

        if (Object.keys(agent.metadata).length > 0) {
          console.log(ui.subheader('Metadata'));
          console.log(`  ${JSON.stringify(agent.metadata, null, 2)}`);
        }
      } else {
        console.log(ui.error(`Agent "${id}" not found.`));
      }
    } catch (err: unknown) {
      spin.stop();
      const message = err instanceof Error ? err.message : 'Unknown error';
      console.log(ui.error(`Failed to inspect agent: ${message}`));
      process.exit(1);
    }
  });

// ─── Remove Agent ───────────────────────────────────────────────────────────

const removeAgent = new Command('remove')
  .description('Remove a registered agent')
  .argument('<id>', 'Agent ID')
  .option('-f, --force', 'Skip confirmation prompt')
  .action(async (id: string, options) => {
    const client = requireAuth();

    if (!options.force) {
      const { confirm } = await inquirer.prompt([
        {
          type: 'confirm',
          name: 'confirm',
          message: `Are you sure you want to remove agent "${id}"? This cannot be undone.`,
          default: false,
        },
      ]);

      if (!confirm) {
        console.log(ui.warn('Operation cancelled.'));
        return;
      }
    }

    const spin = ui.spinner('Removing agent...');
    spin.start();

    try {
      const response = await client.removeAgent(id);
      spin.stop();

      if (response.success) {
        console.log(ui.success(`Agent "${id}" has been removed.`));
      } else {
        console.log(ui.error(`Failed to remove agent "${id}".`));
        if (response.error) console.log(ui.error(response.error));
      }
    } catch (err: unknown) {
      spin.stop();
      const message = err instanceof Error ? err.message : 'Unknown error';
      console.log(ui.error(`Failed to remove agent: ${message}`));
      process.exit(1);
    }
  });

// ─── Main Command ───────────────────────────────────────────────────────────

export function registerAgentsCommand(program: Command) {
  program.addCommand(agentsCommand);
}

export const agentsCommand = new Command('agents')
  .description('Manage AI agents')
  .addCommand(listAgents)
  .addCommand(registerAgent)
  .addCommand(inspectAgent)
  .addCommand(removeAgent);
