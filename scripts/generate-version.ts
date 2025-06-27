import gitRevSync from 'git-rev-sync';
import { writeFileSync, mkdirSync } from 'fs';
import { dirname, join } from 'path';
import { fileURLToPath } from 'url';

const __dirname = dirname(fileURLToPath(import.meta.url));
const projectRoot = join(__dirname, '..');

interface VersionInfo {
  version: string;
  buildTime: string;
}

const makeDirty = true;

try {
  // Try to get git tag with commit info
  const tag = gitRevSync.tag(makeDirty);
  const version: string = tag ? 
    `${tag}-${gitRevSync.count()}-g${gitRevSync.short(projectRoot)}` : 
    gitRevSync.short(projectRoot);
  
  const versionInfo: VersionInfo = {
    version,
    buildTime: new Date().toISOString()
  };

  const content = `// This file is auto-generated during build
export const VERSION_INFO = ${JSON.stringify(versionInfo, null, 2)} as const;
`;

  // Ensure directory exists
  mkdirSync(join(__dirname, '../src/lib/generated'), { recursive: true });
  
  writeFileSync(
    join(__dirname, '../src/lib/generated/version.ts'),
    content
  );

  console.log(`Generated version info: ${version}`);
} catch (error) {
  console.error('Failed to generate version info:', error);
  
  // Fallback
  const fallbackInfo: VersionInfo = {
    version: 'unknown',
    buildTime: new Date().toISOString()
  };

  const content = `// This file is auto-generated during build (fallback)
export const VERSION_INFO = ${JSON.stringify(fallbackInfo, null, 2)} as const;
`;

  writeFileSync(
    join(__dirname, '../src/lib/generated/version.ts'),
    content
  );
}