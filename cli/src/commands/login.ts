import { Command } from 'commander';
import inquirer from 'inquirer';
import * as config from '../config';
import { AgentAuthClient } from '../api';
import * as ui from '../ui';

export function registerLoginCommand(program: Command) {
  program.addCommand(loginCommand);
}

export const loginCommand = new Command('login')
  .description('Authenticate with AgentAuth API')
  .option('--key <apiKey>', 'API key (or use interactive prompt)')
  .option('--url <apiUrl>', 'API base URL (default: https://agentauth.in)')
  .action(async (options) => {
    console.log(ui.header('AgentAuth Login'));

    let apiKey = options.key;
    let apiUrl = options.url;

    // If no API key provided, prompt interactively
    if (!apiKey) {
      const answers = await inquirer.prompt([
        {
          type: 'password',
          name: 'apiKey',
          message: 'Enter your AgentAuth API key:',
          mask: '*',
          validate: (input: string) => {
            if (!input || input.trim().length === 0) {
              return 'API key is required';
            }
            if (input.trim().length < 10) {
              return 'API key seems too short. Please check and try again.';
            }
            return true;
          },
        },
      ]);
      apiKey = answers.apiKey;
    }

    // Prompt for custom URL if not provided
    if (!apiUrl) {
      const currentUrl = config.getApiUrl();
      const urlAnswer = await inquirer.prompt([
        {
          type: 'input',
          name: 'apiUrl',
          message: 'API URL:',
          default: currentUrl,
        },
      ]);
      apiUrl = urlAnswer.apiUrl;
    }

    // Validate the API key by calling the account endpoint
    const spin = ui.spinner('Validating API key...');
    spin.start();

    try {
      const client = new AgentAuthClient(apiKey, apiUrl);
      const response = await client.getAccount();

      spin.stop();

      if (response.success && response.data) {
        // Save credentials
        config.setApiKey(apiKey);
        if (apiUrl) {
          config.setApiUrl(apiUrl);
        }

        const account = response.data;

        console.log(ui.success('Successfully authenticated!\n'));
        console.log(ui.infoBox('Account Details', [
          `${ui.chalk.bold('Name:')}         ${account.name}`,
          `${ui.chalk.bold('Email:')}        ${account.email}`,
          `${ui.chalk.bold('Organization:')} ${account.organization}`,
          `${ui.chalk.bold('Plan:')}         ${account.plan.toUpperCase()}`,
          `${ui.chalk.bold('Config saved:')} ${config.getConfigPath()}`,
        ].join('\n')));
      } else {
        console.log(ui.error('Authentication failed. Please check your API key.'));
        process.exit(1);
      }
    } catch (err: unknown) {
      spin.stop();

      const message = err instanceof Error ? err.message : 'Unknown error';
      console.log(ui.error(`Authentication failed: ${message}`));

      if (message.includes('401') || message.includes('Unauthorized')) {
        console.log(ui.info('Your API key appears to be invalid. Please check it and try again.'));
        console.log(ui.info('You can find your API key at https://agentauth.in/dashboard/settings'));
      } else if (message.includes('ECONNREFUSED') || message.includes('fetch')) {
        console.log(ui.info(`Could not connect to ${apiUrl || config.getApiUrl()}`));
        console.log(ui.info('Please check your internet connection and API URL.'));
      }

      process.exit(1);
    }
  });
