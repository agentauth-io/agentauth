import { Command } from 'commander';
import inquirer from 'inquirer';
import * as fs from 'fs';
import * as path from 'path';
import YAML from 'yaml';
import * as config from '../config';
import { AgentAuthClient } from '../api';
import * as ui from '../ui';
import { PolicyCondition, PolicyCreateRequest, PolicyRule } from '../types';

function requireAuth(): AgentAuthClient {
  if (!config.isConfigured()) {
    console.log(ui.error('Not authenticated. Run `agentauth login` first.'));
    process.exit(1);
  }
  return new AgentAuthClient(config.getApiKey(), config.getApiUrl());
}

// ─── List Policies ──────────────────────────────────────────────────────────

const listPolicies = new Command('list')
  .description('List all policies')
  .option('--json', 'Output as JSON')
  .option('--status <status>', 'Filter by status (active, draft, archived)')
  .action(async (options) => {
    const client = requireAuth();
    const spin = ui.spinner('Fetching policies...');
    spin.start();

    try {
      const response = await client.listPolicies();
      spin.stop();

      let policies = response.data;

      if (options.status) {
        policies = policies.filter(p => p.status === options.status);
      }

      if (options.json) {
        console.log(JSON.stringify(policies, null, 2));
        return;
      }

      if (policies.length === 0) {
        console.log(ui.info('No policies found. Create one with `agentauth policies create`.'));
        return;
      }

      console.log(ui.header(`Policies (${policies.length})`));
      console.log(ui.table(
        ['ID', 'Name', 'Status', 'Version', 'Rules', 'Updated'],
        policies.map(policy => [
          ui.truncate(policy.id, 12),
          policy.name,
          ui.statusBadge(policy.status),
          policy.version,
          String(policy.rules.length),
          ui.formatDate(policy.updatedAt),
        ])
      ));
    } catch (err: unknown) {
      spin.stop();
      const message = err instanceof Error ? err.message : 'Unknown error';
      console.log(ui.error(`Failed to list policies: ${message}`));
      process.exit(1);
    }
  });

// ─── Create Policy ─────────────────────────────────────────────────────────

const createPolicy = new Command('create')
  .description('Create a new policy interactively')
  .option('--file <file>', 'Create from YAML file')
  .action(async (options) => {
    const client = requireAuth();

    if (options.file) {
      // Load from file
      const filePath = path.resolve(options.file);
      if (!fs.existsSync(filePath)) {
        console.log(ui.error(`File not found: ${filePath}`));
        process.exit(1);
      }

      const content = fs.readFileSync(filePath, 'utf-8');
      let policyData: PolicyCreateRequest;

      try {
        policyData = YAML.parse(content) as PolicyCreateRequest;
      } catch {
        console.log(ui.error('Invalid YAML file.'));
        process.exit(1);
      }

      const spin = ui.spinner('Creating policy...');
      spin.start();

      try {
        const response = await client.createPolicy(policyData);
        spin.stop();

        if (response.success && response.data) {
          console.log(ui.success(`Policy "${response.data.name}" created successfully!`));
          console.log(ui.detailTable([
            ['ID', response.data.id],
            ['Name', response.data.name],
            ['Status', ui.statusBadge(response.data.status)],
            ['Rules', String(response.data.rules.length)],
          ]));
        }
      } catch (err: unknown) {
        spin.stop();
        const message = err instanceof Error ? err.message : 'Unknown error';
        console.log(ui.error(`Failed to create policy: ${message}`));
        process.exit(1);
      }
      return;
    }

    // Interactive policy builder
    console.log(ui.header('Create New Policy'));

    const basicInfo = await inquirer.prompt([
      {
        type: 'input',
        name: 'name',
        message: 'Policy name:',
        validate: (input: string) => input.length > 0 || 'Name is required',
      },
      {
        type: 'input',
        name: 'description',
        message: 'Description (optional):',
        default: '',
      },
    ]);

    const rules: Omit<PolicyRule, 'id'>[] = [];
    let addMore = true;

    while (addMore) {
      console.log(ui.subheader(`Rule #${rules.length + 1}`));

      const ruleAnswers = await inquirer.prompt([
        {
          type: 'input',
          name: 'action',
          message: 'Action pattern (e.g., "purchase", "*", "api_call.*"):',
          validate: (input: string) => input.length > 0 || 'Action is required',
        },
        {
          type: 'list',
          name: 'effect',
          message: 'Effect:',
          choices: [
            { name: 'Allow - Permit the action', value: 'allow' },
            { name: 'Deny - Block the action', value: 'deny' },
            { name: 'Require Consent - Ask human for approval', value: 'require_consent' },
          ],
        },
        {
          type: 'number',
          name: 'priority',
          message: 'Priority (higher = evaluated first):',
          default: rules.length + 1,
        },
        {
          type: 'confirm',
          name: 'addConditions',
          message: 'Add conditions to this rule?',
          default: false,
        },
      ]);

      const conditions: PolicyCondition[] = [];

      if (ruleAnswers.addConditions) {
        let addMoreConditions = true;
        while (addMoreConditions) {
          const condAnswers = await inquirer.prompt([
            {
              type: 'input',
              name: 'field',
              message: 'Condition field (e.g., "amount", "merchant", "time"):',
              validate: (input: string) => input.length > 0 || 'Field is required',
            },
            {
              type: 'list',
              name: 'operator',
              message: 'Operator:',
              choices: [
                { name: 'Equals (==)', value: 'eq' },
                { name: 'Not Equals (!=)', value: 'neq' },
                { name: 'Greater Than (>)', value: 'gt' },
                { name: 'Greater or Equal (>=)', value: 'gte' },
                { name: 'Less Than (<)', value: 'lt' },
                { name: 'Less or Equal (<=)', value: 'lte' },
                { name: 'In List', value: 'in' },
                { name: 'Not In List', value: 'nin' },
                { name: 'Contains', value: 'contains' },
                { name: 'Regex Match', value: 'matches' },
              ],
            },
            {
              type: 'input',
              name: 'value',
              message: 'Value (use comma-separated for lists):',
              validate: (input: string) => input.length > 0 || 'Value is required',
            },
            {
              type: 'confirm',
              name: 'addMore',
              message: 'Add another condition?',
              default: false,
            },
          ]);

          let value: unknown = condAnswers.value;
          // Parse numeric values
          if (!isNaN(Number(value))) {
            value = Number(value);
          }
          // Parse comma-separated lists for in/nin
          if ((condAnswers.operator === 'in' || condAnswers.operator === 'nin') && typeof value === 'string') {
            value = value.split(',').map((v: string) => v.trim());
          }

          conditions.push({
            field: condAnswers.field,
            operator: condAnswers.operator,
            value,
          });

          addMoreConditions = condAnswers.addMore;
        }
      }

      rules.push({
        action: ruleAnswers.action,
        effect: ruleAnswers.effect,
        conditions,
        priority: ruleAnswers.priority,
      });

      const { more } = await inquirer.prompt([
        {
          type: 'confirm',
          name: 'more',
          message: 'Add another rule?',
          default: false,
        },
      ]);
      addMore = more;
    }

    // Show summary
    console.log(ui.subheader('Policy Summary'));
    console.log(ui.detailTable([
      ['Name', basicInfo.name],
      ['Description', basicInfo.description || ui.chalk.dim('none')],
      ['Rules', String(rules.length)],
    ]));

    rules.forEach((rule, i) => {
      console.log(`\n  Rule #${i + 1}: ${rule.action} -> ${ui.statusBadge(rule.effect)} (priority: ${rule.priority})`);
      if (rule.conditions.length > 0) {
        rule.conditions.forEach(cond => {
          console.log(`    ${ui.chalk.dim('if')} ${cond.field} ${cond.operator} ${JSON.stringify(cond.value)}`);
        });
      }
    });

    // Save options
    const { saveAction } = await inquirer.prompt([
      {
        type: 'list',
        name: 'saveAction',
        message: 'What would you like to do?',
        choices: [
          { name: 'Push to API (create policy)', value: 'push' },
          { name: 'Save as YAML file', value: 'save' },
          { name: 'Both (push and save)', value: 'both' },
          { name: 'Cancel', value: 'cancel' },
        ],
      },
    ]);

    if (saveAction === 'cancel') {
      console.log(ui.warn('Policy creation cancelled.'));
      return;
    }

    const policyData: PolicyCreateRequest = {
      name: basicInfo.name,
      description: basicInfo.description,
      rules,
    };

    if (saveAction === 'save' || saveAction === 'both') {
      const { filename } = await inquirer.prompt([
        {
          type: 'input',
          name: 'filename',
          message: 'File name:',
          default: `${basicInfo.name.toLowerCase().replace(/\s+/g, '-')}.yaml`,
        },
      ]);

      const yamlContent = YAML.stringify(policyData);
      fs.writeFileSync(filename, yamlContent, 'utf-8');
      console.log(ui.success(`Policy saved to ${filename}`));
    }

    if (saveAction === 'push' || saveAction === 'both') {
      const spin = ui.spinner('Creating policy...');
      spin.start();

      try {
        const response = await client.createPolicy(policyData);
        spin.stop();

        if (response.success && response.data) {
          console.log(ui.success(`Policy "${response.data.name}" created successfully!`));
          console.log(ui.detailTable([
            ['ID', response.data.id],
            ['Name', response.data.name],
            ['Version', response.data.version],
            ['Status', ui.statusBadge(response.data.status)],
          ]));
        }
      } catch (err: unknown) {
        spin.stop();
        const message = err instanceof Error ? err.message : 'Unknown error';
        console.log(ui.error(`Failed to create policy: ${message}`));
        process.exit(1);
      }
    }
  });

// ─── Test Policy ────────────────────────────────────────────────────────────

const testPolicy = new Command('test')
  .description('Test a policy with a simulated authorization request')
  .argument('<policyId>', 'Policy ID to test')
  .option('-a, --agent <agentId>', 'Agent ID', 'test-agent')
  .option('--action <action>', 'Action to test', 'purchase')
  .option('--amount <amount>', 'Amount', parseFloat)
  .option('-m, --merchant <merchant>', 'Merchant')
  .action(async (policyId: string, options) => {
    const client = requireAuth();

    console.log(ui.header('Policy Test'));

    const request = {
      agentId: options.agent,
      action: options.action,
      amount: options.amount,
      merchant: options.merchant,
    };

    console.log(ui.info(`Testing policy ${policyId} with:`));
    console.log(ui.detailTable(
      Object.entries(request)
        .filter(([, v]) => v !== undefined)
        .map(([k, v]) => [k, String(v)])
    ));

    const spin = ui.spinner('Running policy test...');
    spin.start();

    try {
      const response = await client.testPolicy(policyId, request);
      spin.stop();

      if (response.success && response.data) {
        const result = response.data;
        console.log(`\n  Result: ${ui.decisionBadge(result.decision)}`);
        console.log(`  Reason: ${result.reason}`);
        console.log(`  Latency: ${ui.formatLatency(result.latencyMs)}\n`);
      }
    } catch (err: unknown) {
      spin.stop();
      const message = err instanceof Error ? err.message : 'Unknown error';
      console.log(ui.error(`Policy test failed: ${message}`));
      process.exit(1);
    }
  });

// ─── Push Policy ────────────────────────────────────────────────────────────

const pushPolicy = new Command('push')
  .description('Upload a policy from a YAML file')
  .argument('<file>', 'YAML file path')
  .action(async (file: string) => {
    const client = requireAuth();

    const filePath = path.resolve(file);
    if (!fs.existsSync(filePath)) {
      console.log(ui.error(`File not found: ${filePath}`));
      process.exit(1);
    }

    const content = fs.readFileSync(filePath, 'utf-8');
    let policyData: PolicyCreateRequest;

    try {
      policyData = YAML.parse(content) as PolicyCreateRequest;
    } catch {
      console.log(ui.error('Invalid YAML file. Please check the syntax.'));
      process.exit(1);
    }

    console.log(ui.info(`Pushing policy from ${path.basename(filePath)}...`));
    console.log(ui.detailTable([
      ['Name', policyData.name],
      ['Rules', String(policyData.rules?.length || 0)],
    ]));

    const spin = ui.spinner('Uploading policy...');
    spin.start();

    try {
      const response = await client.createPolicy(policyData);
      spin.stop();

      if (response.success && response.data) {
        console.log(ui.success(`Policy "${response.data.name}" pushed successfully!`));
        console.log(ui.detailTable([
          ['ID', response.data.id],
          ['Version', response.data.version],
          ['Status', ui.statusBadge(response.data.status)],
        ]));
      }
    } catch (err: unknown) {
      spin.stop();
      const message = err instanceof Error ? err.message : 'Unknown error';
      console.log(ui.error(`Push failed: ${message}`));
      process.exit(1);
    }
  });

// ─── Pull Policy ────────────────────────────────────────────────────────────

const pullPolicy = new Command('pull')
  .description('Download a policy as a YAML file')
  .argument('<policyId>', 'Policy ID')
  .option('-o, --output <file>', 'Output file path')
  .action(async (policyId: string, options) => {
    const client = requireAuth();

    const spin = ui.spinner('Fetching policy...');
    spin.start();

    try {
      const response = await client.getPolicy(policyId);
      spin.stop();

      if (response.success && response.data) {
        const policy = response.data;
        const yamlContent = YAML.stringify({
          name: policy.name,
          description: policy.description,
          rules: policy.rules.map(r => ({
            action: r.action,
            effect: r.effect,
            priority: r.priority,
            conditions: r.conditions,
          })),
        });

        const outputFile = options.output || `${policy.name.toLowerCase().replace(/\s+/g, '-')}.yaml`;
        fs.writeFileSync(outputFile, yamlContent, 'utf-8');

        console.log(ui.success(`Policy "${policy.name}" saved to ${outputFile}`));
        console.log(ui.detailTable([
          ['ID', policy.id],
          ['Version', policy.version],
          ['Rules', String(policy.rules.length)],
          ['File', path.resolve(outputFile)],
        ]));
      } else {
        console.log(ui.error(`Policy "${policyId}" not found.`));
      }
    } catch (err: unknown) {
      spin.stop();
      const message = err instanceof Error ? err.message : 'Unknown error';
      console.log(ui.error(`Pull failed: ${message}`));
      process.exit(1);
    }
  });

// ─── Main Command ───────────────────────────────────────────────────────────

export function registerPoliciesCommand(program: Command) {
  program.addCommand(policiesCommand);
}

export const policiesCommand = new Command('policies')
  .description('Manage authorization policies')
  .addCommand(listPolicies)
  .addCommand(createPolicy)
  .addCommand(testPolicy)
  .addCommand(pushPolicy)
  .addCommand(pullPolicy);
