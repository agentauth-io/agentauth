import { Command } from 'commander';
import chalk from 'chalk';
import fs from 'fs';
import YAML from 'yaml';
import inquirer from 'inquirer';
import { getConfig } from '../config';
import { AgentAuthClient } from '../api';
import * as ui from '../ui';
import { TestScenario, TestCase, TestResult, AuthorizationRequest } from '../types';

function getClient(): AgentAuthClient {
  const config = getConfig();
  if (!config.apiKey) {
    console.log(ui.error('Not logged in. Run: agentauth login'));
    process.exit(1);
  }
  return new AgentAuthClient(config.apiKey, config.apiUrl);
}

async function runScenario(scenarioFile: string, options: { verbose?: boolean }) {
  const client = getClient();

  // Load scenario file
  if (!fs.existsSync(scenarioFile)) {
    console.log(ui.error(`File not found: ${scenarioFile}`));
    process.exit(1);
  }

  const content = fs.readFileSync(scenarioFile, 'utf-8');
  let scenario: TestScenario;

  try {
    if (scenarioFile.endsWith('.yaml') || scenarioFile.endsWith('.yml')) {
      scenario = YAML.parse(content) as TestScenario;
    } else {
      scenario = JSON.parse(content) as TestScenario;
    }
  } catch (err: any) {
    console.log(ui.error(`Failed to parse scenario file: ${err.message}`));
    process.exit(1);
  }

  if (!scenario.scenarios || scenario.scenarios.length === 0) {
    console.log(ui.warn('No test cases found in scenario file.'));
    return;
  }

  console.log(ui.header(`Running Tests: ${scenario.name || scenarioFile}`));
  if (scenario.description) {
    console.log(chalk.gray(`  ${scenario.description}\n`));
  }

  const results: TestResult[] = [];
  let passed = 0;
  let failed = 0;

  for (const testCase of scenario.scenarios) {
    const start = Date.now();

    try {
      const response = await client.authorize(testCase.request);
      const latency = Date.now() - start;
      const actualDecision = response.data?.decision || 'UNKNOWN';
      const isPass = actualDecision === testCase.expectedDecision;

      if (isPass) passed++;
      else failed++;

      const result: TestResult = {
        name: testCase.name,
        passed: isPass,
        expected: testCase.expectedDecision,
        actual: actualDecision,
        latencyMs: latency,
        reason: response.data?.reason || '',
      };
      results.push(result);

      const icon = isPass ? chalk.green('✓ PASS') : chalk.red('✗ FAIL');
      const details = isPass ? '' : chalk.gray(` (expected ${testCase.expectedDecision}, got ${actualDecision})`);
      console.log(`  ${icon}  ${chalk.white(testCase.name)}${details}  ${chalk.gray(`${latency}ms`)}`);

      if (options.verbose && !isPass) {
        console.log(chalk.gray(`         Reason: ${response.data?.reason || 'N/A'}`));
        console.log(chalk.gray(`         Request: ${JSON.stringify(testCase.request)}`));
      }
    } catch (err: any) {
      const latency = Date.now() - start;
      failed++;

      const result: TestResult = {
        name: testCase.name,
        passed: false,
        expected: testCase.expectedDecision,
        actual: 'ERROR',
        latencyMs: latency,
        reason: '',
        error: err.message,
      };
      results.push(result);

      console.log(`  ${chalk.red('✗ ERROR')}  ${chalk.white(testCase.name)}  ${chalk.red(err.message)}`);
    }
  }

  // Summary
  console.log('');
  console.log(chalk.gray('  ─────────────────────────────────────────'));
  const totalStr = `${results.length} tests`;
  const passStr = chalk.green(`${passed} passed`);
  const failStr = failed > 0 ? chalk.red(`${failed} failed`) : chalk.gray('0 failed');
  const avgLatency = Math.round(results.reduce((s, r) => s + r.latencyMs, 0) / results.length);
  console.log(`  ${totalStr}  |  ${passStr}  |  ${failStr}  |  avg ${chalk.cyan(`${avgLatency}ms`)}`);

  if (failed > 0) {
    console.log('');
    console.log(chalk.red(`  ${failed} test(s) failed.`));
    process.exitCode = 1;
  } else {
    console.log('');
    console.log(chalk.green('  All tests passed!'));
  }
}

async function runInteractive() {
  const client = getClient();

  console.log(ui.header('Interactive Authorization Test'));
  console.log(chalk.gray('  Test authorization requests interactively.\n'));

  let running = true;
  while (running) {
    const answers = await inquirer.prompt([
      { type: 'input', name: 'agentId', message: 'Agent ID:', default: 'test-agent' },
      { type: 'input', name: 'action', message: 'Action:', default: 'purchase' },
      { type: 'input', name: 'amount', message: 'Amount ($):', default: '100' },
      { type: 'input', name: 'merchant', message: 'Merchant:', default: 'example.com' },
      { type: 'input', name: 'description', message: 'Description (optional):' },
    ]);

    const request: AuthorizationRequest = {
      agentId: answers.agentId,
      action: answers.action,
      amount: parseFloat(answers.amount) || undefined,
      merchant: answers.merchant || undefined,
      description: answers.description || undefined,
    };

    const spinner = ui.spinner('Authorizing...');
    spinner.start();
    const start = Date.now();

    try {
      const response = await client.authorize(request);
      const latency = Date.now() - start;
      spinner.stop();

      const decision = response.data?.decision || 'UNKNOWN';
      const icon = decision === 'ALLOWED' ? chalk.green('✓ ALLOWED') :
                   decision === 'DENIED' ? chalk.red('✗ DENIED') :
                   chalk.yellow('⏳ PENDING');

      console.log('');
      console.log(`  ${icon}  ${chalk.gray(`${latency}ms`)}`);
      if (response.data?.reason) {
        console.log(chalk.gray(`  Reason: ${response.data.reason}`));
      }
      if (response.data?.policyName) {
        console.log(chalk.gray(`  Policy: ${response.data.policyName}`));
      }
      console.log('');
    } catch (err: any) {
      spinner.stop();
      console.log(ui.error(`Authorization failed: ${err.message}`));
    }

    const { again } = await inquirer.prompt([{
      type: 'confirm',
      name: 'again',
      message: 'Run another test?',
      default: true,
    }]);
    running = again;
  }
}

export function registerTestCommand(program: Command) {
  program
    .command('test')
    .description('Test authorization policies')
    .option('-s, --scenario <file>', 'Test scenario file (YAML/JSON)')
    .option('-i, --interactive', 'Interactive testing mode')
    .option('-v, --verbose', 'Show detailed output on failures')
    .action(async (options) => {
      if (options.interactive) {
        await runInteractive();
      } else if (options.scenario) {
        await runScenario(options.scenario, options);
      } else {
        console.log(ui.warn('Specify --scenario <file> or --interactive'));
        console.log(chalk.gray('  Example: agentauth test --scenario tests/basic.yaml'));
        console.log(chalk.gray('  Example: agentauth test --interactive'));
      }
    });
}
