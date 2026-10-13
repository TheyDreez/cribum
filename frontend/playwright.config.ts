import { defineConfig, devices } from '@playwright/test';

// Flag opt-in caso um ambiente conteinerizado (ex: CI Docker root) exija explicitamente no-sandbox
const useInsecureSandbox = process.env.PLAYWRIGHT_INSECURE_SANDBOX === 'true';

export default defineConfig({
  testDir: './tests',
  fullyParallel: false,
  workers: 1,
  forbidOnly: !!process.env.CI,
  retries: 0,
  timeout: 30000,
  use: {
    baseURL: 'http://127.0.0.1:5173',
    trace: 'retain-on-failure',
    screenshot: 'only-on-failure',
    video: 'retain-on-failure',
    headless: true,
    launchOptions: useInsecureSandbox
      ? {
          args: ['--no-sandbox', '--disable-setuid-sandbox'],
        }
      : {},
  },
  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
  ],
});
