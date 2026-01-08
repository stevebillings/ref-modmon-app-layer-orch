/**
 * Playwright global setup - runs once before all tests.
 *
 * This resets the database to a clean state with only test users seeded.
 */
import { execSync } from 'child_process';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

async function globalSetup() {
  console.log('\n📦 Resetting test database...');

  const backendDir = path.resolve(__dirname, '../../backend');

  try {
    // Reset the database - clears all data and seeds test users
    execSync('python manage.py reset_test_db', {
      cwd: backendDir,
      stdio: 'inherit',
    });

    console.log('✅ Database reset complete\n');
  } catch (error) {
    console.error('❌ Failed to reset database:', error);
    throw error;
  }
}

export default globalSetup;
