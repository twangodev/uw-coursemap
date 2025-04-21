import type { Handle } from '@sveltejs/kit';
import { getContributors } from '$lib/github';
import { writeFileSync, existsSync, mkdirSync } from 'node:fs';
import { join, dirname } from 'node:path';

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
            
            writeFileSync(staticPath, JSON.stringify(contributors.slice(0, 5), null, 2));
            initialized = true;
        } catch (error) {
            console.error('Error fetching contributors:', error);
        }
    }
    
    return await resolve(event);
};