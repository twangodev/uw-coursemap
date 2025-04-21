import type { Handle } from '@sveltejs/kit';
import { getContributors, type Contributor } from '$lib/github';
import { writeFileSync, existsSync, mkdirSync } from 'node:fs';
import { join, dirname } from 'node:path';

export interface ContributorsData {
    timestamp?: string;
    contributors: Contributor[];
}

let initialized = false;

export const handle: Handle = async ({ event, resolve }) => {
    // Only fetch contributors once during build/SSR
    if (!initialized && import.meta.env.SSR) {
        try {
            const contributors = await getContributors();
            const staticPath = join(process.cwd(), 'src', 'lib', 'contributors.json');
            
            // Ensure static directory exists
            const dir = dirname(staticPath);
            if (!existsSync(dir)) {
                mkdirSync(dir, { recursive: true });
            }
            
            const contributorsData: ContributorsData = {
                timestamp: new Date().toISOString(),
                contributors: contributors.slice(0, 3)
            };
            
            writeFileSync(staticPath, JSON.stringify(contributorsData, null, 2));
            initialized = true;
        } catch (error) {
            console.error('Error fetching contributors:', error);
        }
    }
    
    return await resolve(event);
};