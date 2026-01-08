import { defineConfig, devices } from '@playwright/test';
import { defineBddConfig, cucumberReporter } from 'playwright-bdd';
import path from 'path';
import { fileURLToPath } from 'url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const projectRoot = path.resolve(__dirname, '..');

const testDir = defineBddConfig({
  featuresRoot: projectRoot,
  features: path.join(projectRoot, 'features/**/*.feature'),
  steps: ['e2e/steps/**/*.ts', 'e2e/fixtures/test-fixtures.ts'],
  tags: '@frontend and not @backend-only',
});

export default defineConfig({
  testDir,
  // Global setup runs before all tests - resets database to clean state
  globalSetup: './e2e/global-setup.ts',
  fullyParallel: false, // Run tests serially to avoid database conflicts
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: 1, // Single worker for reliable test execution with shared database
  reporter: [
    cucumberReporter('html', { outputFile: 'cucumber-report/report.html' }),
    ['html', { outputFolder: 'playwright-report' }],
    ['list'],
  ],
  use: {
    baseURL: process.env.PLAYWRIGHT_BASE_URL || 'http://localhost:5173',
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
    video: 'on-first-retry',
  },
  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
  ],
  webServer: [
    {
      // Backend Django server
      command: 'cd ../backend && python manage.py runserver 8000',
      url: 'http://localhost:8000/api/health/',
      reuseExistingServer: !process.env.CI,
      timeout: 120 * 1000,
    },
    {
      // Frontend Vite dev server
      command: 'npm run dev',
      url: 'http://localhost:5173',
      reuseExistingServer: !process.env.CI,
      timeout: 120 * 1000,
    },
  ],
});
