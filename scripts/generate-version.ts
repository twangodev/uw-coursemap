import * as gitRevSync from 'git-rev-sync';
import { writeFileSync, mkdirSync } from 'fs';
import { dirname, join } from 'path';
import { fileURLToPath } from 'url';

const __dirname = dirname(fileURLToPath(import.meta.url));
const projectRoot = join(__dirname, '..');

interface VersionInfo {
  version: string;
  buildTime: string;
}

const makeDirty = true
const outputDir = join(projectRoot, 'src/lib/generated');
const outputFile = join(outputDir, 'version.ts');

let version: string;

try {
  // Use git-rev-sync with project root path
  const tag = gitRevSync.tag(makeDirty);
  const short = gitRevSync.short(projectRoot);
  
  version = tag ? `${tag}-${short}` : short;
} catch (error) {
  console.warn('Git command failed:', error instanceof Error ? error.message : String(error));
  console.warn('Using fallback version');
  version = 'unknown';
}

const versionInfo: VersionInfo = {
  version,
  buildTime: new Date().toISOString()
};

const content = `// This file is auto-generated during build
export const VERSION_INFO = ${JSON.stringify(versionInfo, null, 2)} as const;
`;

// Ensure directory exists
mkdirSync(outputDir, { recursive: true });

writeFileSync(outputFile, content);

console.log(`Generated version info: ${version}`);