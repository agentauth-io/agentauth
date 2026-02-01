import Conf from 'conf';

const DEFAULT_API_URL = 'https://agentauth.in';

interface ConfigSchema {
  apiKey: string;
  apiUrl: string;
  outputFormat: 'table' | 'json' | 'yaml';
  colorEnabled: boolean;
}

const config = new Conf<ConfigSchema>({
  projectName: 'agentauth',
  defaults: {
    apiKey: '',
    apiUrl: DEFAULT_API_URL,
    outputFormat: 'table',
    colorEnabled: true,
  },
  schema: {
    apiKey: {
      type: 'string',
      default: '',
    },
    apiUrl: {
      type: 'string',
      default: DEFAULT_API_URL,
    },
    outputFormat: {
      type: 'string',
      enum: ['table', 'json', 'yaml'],
      default: 'table',
    },
    colorEnabled: {
      type: 'boolean',
      default: true,
    },
  },
});

/**
 * Get the stored API key
 */
export function getApiKey(): string {
  return config.get('apiKey');
}

/**
 * Set the API key
 */
export function setApiKey(key: string): void {
  config.set('apiKey', key);
}

/**
 * Get the API base URL
 */
export function getApiUrl(): string {
  return config.get('apiUrl');
}

/**
 * Set the API base URL
 */
export function setApiUrl(url: string): void {
  config.set('apiUrl', url);
}

/**
 * Get the preferred output format
 */
export function getOutputFormat(): 'table' | 'json' | 'yaml' {
  return config.get('outputFormat');
}

/**
 * Set the preferred output format
 */
export function setOutputFormat(format: 'table' | 'json' | 'yaml'): void {
  config.set('outputFormat', format);
}

/**
 * Check if colors are enabled
 */
export function isColorEnabled(): boolean {
  return config.get('colorEnabled');
}

/**
 * Set color preference
 */
export function setColorEnabled(enabled: boolean): void {
  config.set('colorEnabled', enabled);
}

/**
 * Clear all stored configuration
 */
export function clear(): void {
  config.clear();
}

/**
 * Check if an API key is configured
 */
export function isConfigured(): boolean {
  const key = getApiKey();
  return key !== undefined && key !== null && key.length > 0;
}

/**
 * Get the path to the config file
 */
export function getConfigPath(): string {
  return config.path;
}

/**
 * Get all config as an object (used by commands that need apiKey + apiUrl)
 */
export function getConfig(): { apiKey: string; apiUrl: string; outputFormat: string; colorEnabled: boolean } {
  return {
    apiKey: getApiKey(),
    apiUrl: getApiUrl(),
    outputFormat: getOutputFormat(),
    colorEnabled: isColorEnabled(),
  };
}

/**
 * Get all config values (with masked API key)
 */
export function getAll(): Record<string, unknown> {
  const apiKey = getApiKey();
  return {
    apiKey: apiKey ? `${apiKey.substring(0, 8)}...${apiKey.substring(apiKey.length - 4)}` : '(not set)',
    apiUrl: getApiUrl(),
    outputFormat: getOutputFormat(),
    colorEnabled: isColorEnabled(),
    configPath: getConfigPath(),
  };
}
