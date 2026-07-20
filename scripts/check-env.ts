import "dotenv/config";

import { getServerEnv } from "../lib/env";

try {
  const env = getServerEnv();
  console.log("Environment OK");
  console.log(`  NODE_ENV: ${env.NODE_ENV}`);
  console.log(`  APP_URL: ${env.APP_URL}`);
  console.log(`  DATABASE_URL: configured`);
} catch (error) {
  console.error(error instanceof Error ? error.message : error);
  process.exit(1);
}
