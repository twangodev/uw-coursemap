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
  console.log('Fetching GitHub contributors during build time (using a single API call)...');
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
    // Make a single API call to get contributor stats
    console.log('Retrieving contributor stats...');
    let stats = [];
    try {
      // Implement retry mechanism for 202 responses
      let retries = 0;
      const maxRetries = 100; // We can retry up to 100 times (500 seconds)
      let response;

      while (retries <= maxRetries) {
        response = await octokit.request('GET /repos/{owner}/{repo}/stats/contributors', {
          owner: 'twangodev',
          repo: 'uw-coursemap',
        });

        // If we get a 202 status code, GitHub is still computing the stats
        if (response.status === 202) {
          retries++;
          if (retries <= maxRetries) {
            console.log(`Received 202 status (stats being computed). Retry ${retries}/${maxRetries} after 5 seconds...`);
            // Wait for 5 seconds before retrying
            await new Promise(resolve => setTimeout(resolve, 5000));
          } else {
            console.error(`Reached maximum retries (${maxRetries}) for 202 status. Aborting operation.`);
            throw new Error(`Failed to fetch contributor stats after ${maxRetries} retries. Aborting.`);
          }
        } else {
          // If we get a successful response, break out of the loop
          break;
        }
      }

      if (response && response.status !== 202) {
        stats = response.data;
        console.log(`Successfully fetched stats for ${stats.length} contributors`);
      } else {
        console.warn('Could not fetch contributor stats after retries, proceeding with empty data');
      }
    } catch (error) {
      console.warn('Could not fetch contributor stats:', error);
      return []; // Return empty array if we can't get stats
    }

    // Ensure stats is an array before processing
    if (!Array.isArray(stats)) {
      console.warn('Stats is not an array, returning empty array');
      return [];
    }

    // Process each contributor from the stats
    const contributors = stats.map((stat) => {
      if (!stat.author) {
        console.warn('Stat has no author, skipping');
        return null;
      }

      const contributor = stat.author;
      // Calculate lines from weeks data
      let lines = 0;
      if (stat.weeks) {
        // Sum up additions and subtract deletions across all weeks
        lines = stat.weeks.reduce((sum, week) => sum + week.a - week.d, 0);
      }

      // Ensure lines is not negative
      lines = lines > 0 ? lines : 0;

      // Use login as the name - we're only making one API call total
      const userName = contributor.login;

      // Log the contributor details including lines and contributions
      console.log(`Discovered contributor: ${contributor.login} - Lines: ${lines}, Commits: ${stat.total}`);

      return {
        login: contributor.login,
        avatar_url: contributor.avatar_url,
        html_url: contributor.html_url,
        contributions: stat.total,
        name: userName,
        lines: lines, // Don't allow negative lines
      };
    });

    const contributorsWithLines = contributors.filter(Boolean) as Contributor[];

    // Filter out maintainers from the contributors list
    const maintainerGithubUsernames = maintainers.map(maintainer => {
      // Extract GitHub username from the link
      const githubLink = maintainer.links.find(link => link.icon === 'github')?.link;
      return githubLink ? githubLink.replace(/\/+$/, '').split('/').pop() : '';
    });

    const filteredContributors = contributorsWithLines.filter(
      contributor => !maintainerGithubUsernames.includes(contributor.login)
    );

    // Sort by lines contributed (descending), then by contributions if lines are equal
    return filteredContributors.sort((a, b) => {
      const linesA = a.lines || 0;
      const linesB = b.lines || 0;

      // If lines are equal, sort by contributions
      if (linesA === linesB) {
        return (b.contributions || 0) - (a.contributions || 0);
      }

      // Otherwise, sort by lines
      return linesB - linesA;
    });
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
    avatar: 'https://www.github.com/landonbakken.png',
    name: 'Landon Bakken',
    title: 'Maintainer',
    links: [
      { icon: 'github', link: 'https://github.com/landonbakken' },
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
