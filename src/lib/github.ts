// This file contains the logic to fetch contributors from GitHub API
// interfaces for GitHub API responses
interface GitHubUser {
    name: string | null;
    blog: string | null;
    html_url: string;
}

interface GitHubContributor {
    login: string;
    type: string;
    url: string;
}

// what we want to return
export interface Contributor {
    name: string;
    url: string;
}

export async function getContributors(): Promise<Contributor[]> {
    try {
        // Fetch contributors list
        const response = await fetch('https://api.github.com/repos/twangodev/uw-coursemap/contributors');
        const contributors: GitHubContributor[] = await response.json();

        // Filter out bots and fetch detailed info for each contributor
        const contributorDetails = await Promise.all(
            contributors
                .filter(c => c.type !== 'Bot')
                .map(async (contributor): Promise<Contributor> => {
                    const userResponse = await fetch(contributor.url);
                    const userData: GitHubUser = await userResponse.json();
                    
                    return {
                        name: userData.name || contributor.login,
                        url: userData.blog || userData.html_url
                    };
                })
        );
        return contributorDetails;
    } catch (error) {
        console.error('Error fetching contributors:', error);
        // Fallback data if API fails
        return [
            { name: "James Ding", url: "https://twango.dev" },
            // TODO: I need to make a personal website lmao
            { name: "Charles Ding", url: "https://github.com/ProfessorAtomicManiac" },
            { name: "Landon Bakken", url: "https://theradest1.github.io/Personal-Website-Github-Pages/" }
        ];
    }
}