import * as gitRevSync from 'git-rev-sync';
import { writeFileSync, mkdirSync } from 'fs';
import { dirname, join } from 'path';
import { fileURLToPath } from 'url';

const __dirname = dirname(fileURLToPath(import.meta.url));
const projectRoot = join(__dirname, '..');

interface VersionInfo {
  tag: string,
  short: string,
  buildTime: string;
}

const outputDir = join(projectRoot, 'src/lib/generated');
const outputFile = join(outputDir, 'version.ts');

let tag: string;
let short: string;

try {
  tag = gitRevSync.tag();
  short = gitRevSync.short(projectRoot);
  
} catch (error) {
  console.warn('Git command failed:', error instanceof Error ? error.message : String(error));
  console.warn('Using fallback version');
  tag = 'unknown';
  short = 'unknown';
}

const versionInfo: VersionInfo = {
  tag,
  short,
  buildTime: new Date().toISOString()
};

const content = `// This file is auto-generated during build
export const VERSION_INFO = ${JSON.stringify(versionInfo, null, 2)} as const;
`;

// Ensure directory exists
mkdirSync(outputDir, { recursive: true });

writeFileSync(outputFile, content);

console.log(`Generated version info: ${tag} (${short}) at ${outputFile}`);