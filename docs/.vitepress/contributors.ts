import { Octokit } from '@octokit/rest';

// Access environment variables
const GITHUB_TOKEN = process.env.GITHUB_TOKEN;

interface Contributor {
  login: string;
  avatar_url: string;
  html_url: string;
  contributions: number;
  name?: string;
  lines?: number;
}

interface TeamMember {
  avatar: string;
  name: string;
  title: string;
  links: { icon: string; link: string }[];
}

// This function will be executed only during build time
async function fetchContributors(maintainers: TeamMember[]): Promise<Contributor[]> {
  console.log('Fetching GitHub contributors during build time...');
  // Initialize Octokit with GitHub token if available
  const octokit = new Octokit(GITHUB_TOKEN ? {
    auth: GITHUB_TOKEN
  } : {});

  if (GITHUB_TOKEN) {
    console.log('Using GitHub token for authentication');
  } else {
    console.log('No GitHub token found. API requests may be rate-limited.');
  }

  try {
    // Get contributors from GitHub API
    const { data: contributors } = await octokit.repos.listContributors({
      owner: 'twangodev',
      repo: 'uw-coursemap',
      per_page: 100,
    });

    // Get additional data for each contributor to calculate lines
    const contributorsWithLines = await Promise.all(
      contributors.map(async (contributor) => {
        // Get user details to get the name
        const { data: user } = await octokit.users.getByUsername({
          username: contributor.login,
        });

        // Get commit stats to calculate lines
        // Note: This endpoint might return 202 if stats are not cached
        // In a production environment, you might want to handle this case
        let stats = [];
        try {
          const response = await octokit.request('GET /repos/{owner}/{repo}/stats/contributors', {
            owner: 'twangodev',
            repo: 'uw-coursemap',
          });
          stats = response.data;
        } catch (error) {
          console.warn('Could not fetch contributor stats:', error);
        }

        // Ensure stats is an array before using find
        const contributorStats = Array.isArray(stats) 
          ? stats.find(stat => stat.author && stat.author.login === contributor.login)
          : undefined;
        let lines = 0;

        if (contributorStats && contributorStats.weeks) {
          // Sum up additions and subtract deletions across all weeks
          lines = contributorStats.weeks.reduce((sum, week) => sum + week.a - week.d, 0);
        }

        return {
          login: contributor.login,
          avatar_url: contributor.avatar_url,
          html_url: contributor.html_url,
          contributions: contributor.contributions,
          name: user.name || contributor.login,
          lines: lines > 0 ? lines : 0, // Ensure lines is not negative
        };
      })
    );

    // Filter out maintainers from the contributors list
    const maintainerGithubUsernames = maintainers.map(maintainer => {
      // Extract GitHub username from the link
      const githubLink = maintainer.links.find(link => link.icon === 'github')?.link;
      return githubLink ? githubLink.split('/').pop() : '';
    });

    const filteredContributors = contributorsWithLines.filter(
      contributor => !maintainerGithubUsernames.includes(contributor.login)
    );

    // Sort by lines contributed (descending)
    return filteredContributors.sort((a, b) => (b.lines || 0) - (a.lines || 0));
  } catch (error) {
    console.error('Error fetching GitHub contributors:', error);
    return [];
  }
}

// Define the maintainers list
const maintainers = [
  {
    avatar: 'https://www.github.com/twangodev.png',
    name: 'James Ding',
    title: 'Creator',
    links: [
      { icon: 'github', link: 'https://github.com/twangodev' },
      { icon: 'linkedin', link: 'https://www.linkedin.com/in/jamesding365/' },
    ]
  },
  {
    avatar: 'https://www.github.com/ProfessorAtomicManiac.png',
    name: 'Charles Ding',
    title: 'Maintainer',
    links: [
      { icon: 'github', link: 'https://github.com/ProfessorAtomicManiac' },
    ]
  },
  {
    avatar: 'https://www.github.com/theradest1.png',
    name: 'Landon Bakken',
    title: 'Maintainer',
    links: [
      { icon: 'github', link: 'https://github.com/theradest1' },
    ]
  },
];

// Fetch contributors data at build time
export default {
  async load() {
    const rawContributors = await fetchContributors(maintainers);

    // Transform contributors to match VPTeamMembers format
    const contributors = rawContributors.map(contributor => ({
      avatar: contributor.avatar_url,
      name: contributor.name,
      title: `${contributor.lines} lines, ${contributor.contributions} contributions`,
      links: [
        { icon: 'github', link: contributor.html_url }
      ]
    }));

    return {
      maintainers,
      contributors
    };
  }
};
