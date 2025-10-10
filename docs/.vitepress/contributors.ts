import { Octokit } from "@octokit/rest";
import * as dotenv from "dotenv";

// Load environment variables from .env file
dotenv.config();

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

interface Collaborator {
  login: string;
  avatar_url: string;
  html_url: string;
  permissions?: {
    admin: boolean;
    maintain?: boolean;
    push: boolean;
    triage?: boolean;
    pull: boolean;
  };
  role_name?: string;
}

interface UserProfile {
  name?: string;
  blog?: string;
  twitter_username?: string;
  email?: string;
  bio?: string;
  company?: string;
  location?: string;
  social_accounts?: Array<{
    provider: string;
    url: string;
  }>;
}

// This function will be executed only during build time
async function fetchContributors(
  collaboratorUsernames: string[],
): Promise<Contributor[]> {
  console.log(
    "Fetching GitHub contributors during build time (using a single API call)...",
  );
  // Initialize Octokit with GitHub token if available
  const octokit = new Octokit(
    GITHUB_TOKEN
      ? {
          auth: GITHUB_TOKEN,
        }
      : {},
  );

  if (GITHUB_TOKEN) {
    console.log("Using GitHub token for authentication");
  } else {
    console.log("No GitHub token found. API requests may be rate-limited.");
  }

  try {
    // Make a single API call to get contributor stats
    console.log("Retrieving contributor stats...");
    let stats: any[] = [];
    try {
      // Implement retry mechanism for 202 responses
      let retries = 0;
      const maxRetries = 100; // We can retry up to 100 times (500 seconds)
      let response: any;

      while (retries <= maxRetries) {
        response = await octokit.request(
          "GET /repos/{owner}/{repo}/stats/contributors",
          {
            owner: "twangodev",
            repo: "uw-coursemap",
          },
        );

        // If we get a 202 status code, GitHub is still computing the stats
        if (response.status === 202) {
          retries++;
          if (retries <= maxRetries) {
            console.log(
              `Received 202 status (stats being computed). Retry ${retries}/${maxRetries} after 5 seconds...`,
            );
            // Wait for 5 seconds before retrying
            await new Promise((resolve) => setTimeout(resolve, 5000));
          } else {
            console.error(
              `Reached maximum retries (${maxRetries}) for 202 status. Aborting operation.`,
            );
            throw new Error(
              `Failed to fetch contributor stats after ${maxRetries} retries. Aborting.`,
            );
          }
        } else {
          // If we get a successful response, break out of the loop
          break;
        }
      }

      if (response && response.status !== 202) {
        stats = response.data;
        console.log(
          `Successfully fetched stats for ${stats.length} contributors`,
        );
      } else {
        console.warn(
          "Could not fetch contributor stats after retries, proceeding with empty data",
        );
      }
    } catch (error) {
      console.warn("Could not fetch contributor stats:", error);
      return []; // Return empty array if we can't get stats
    }

    // Ensure stats is an array before processing
    if (!Array.isArray(stats)) {
      console.warn("Stats is not an array, returning empty array");
      return [];
    }

    // Process each contributor from the stats
    const contributors = stats.map((stat) => {
      if (!stat.author) {
        console.warn("Stat has no author, skipping");
        return null;
      }

      const contributor = stat.author;
      // Calculate lines from weeks data
      let lines = 0;
      if (stat.weeks) {
        // Sum up additions and subtract deletions across all weeks
        lines = stat.weeks.reduce(
          (sum: number, week: { a: number; d: number }) => sum + week.a - week.d,
          0,
        );
      }

      // Ensure lines is not negative
      lines = lines > 0 ? lines : 0;

      // Use login as the name - we're only making one API call total
      const userName = contributor.login;

      // Log the contributor details including lines and contributions
      console.log(
        `Discovered contributor: ${contributor.login} - Lines: ${lines}, Commits: ${stat.total}`,
      );

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

    // Filter out collaborators from the contributors list
    const filteredContributors = contributorsWithLines.filter(
      (contributor) => !collaboratorUsernames.includes(contributor.login),
    );

    // Sort by contributions (commits) first, then by lines if contributions are equal
    return filteredContributors.sort((a, b) => {
      const contributionsA = a.contributions || 0;
      const contributionsB = b.contributions || 0;

      // If contributions are equal, sort by lines
      if (contributionsA === contributionsB) {
        return (b.lines || 0) - (a.lines || 0);
      }

      // Otherwise, sort by contributions (commits)
      return contributionsB - contributionsA;
    });
  } catch (error) {
    console.error("Error fetching GitHub contributors:", error);
    return [];
  }
}

// Fetch user profile for social links
async function fetchUserProfile(username: string): Promise<UserProfile> {
  const octokit = new Octokit(
    GITHUB_TOKEN
      ? {
          auth: GITHUB_TOKEN,
        }
      : {},
  );

  try {
    // Fetch basic profile and social accounts in parallel
    const [profileResponse, socialAccountsResponse] = await Promise.all([
      octokit.request("GET /users/{username}", { username }),
      octokit.request("GET /users/{username}/social_accounts", { username }).catch((error) => {
        console.warn(`Failed to fetch social accounts for ${username}:`, error);
        return { data: [] };
      }),
    ]);

    return {
      name: profileResponse.data.name || undefined,
      blog: profileResponse.data.blog || undefined,
      twitter_username: profileResponse.data.twitter_username || undefined,
      email: profileResponse.data.email || undefined,
      bio: profileResponse.data.bio || undefined,
      company: profileResponse.data.company || undefined,
      location: profileResponse.data.location || undefined,
      social_accounts: socialAccountsResponse.data || [],
    };
  } catch (error) {
    console.warn(`Failed to fetch profile for ${username}:`, error);
    return {};
  }
}

// Fetch collaborators at build time
async function fetchCollaborators(): Promise<Collaborator[]> {
  console.log("Fetching GitHub collaborators during build time...");

  const octokit = new Octokit(
    GITHUB_TOKEN
      ? {
          auth: GITHUB_TOKEN,
        }
      : {},
  );

  try {
    const collaborators = await octokit.paginate(
      "GET /repos/{owner}/{repo}/collaborators",
      {
        owner: "twangodev",
        repo: "uw-coursemap",
        affiliation: "all",
        per_page: 100,
      },
    );

    console.log(`Successfully fetched ${collaborators.length} collaborators`);

    // Log each collaborator
    collaborators.forEach((collab) => {
      const role = formatRole(collab.role_name) || formatPermissions(collab.permissions);
      console.log(`Discovered collaborator: ${collab.login} - Role: ${role}`);
    });

    return collaborators as Collaborator[];
  } catch (error) {
    console.error("Error fetching GitHub collaborators:", error);
    return [];
  }
}

function formatRole(roleName?: string): string | undefined {
  if (!roleName) return undefined;
  // Capitalize first letter of role name
  return roleName.charAt(0).toUpperCase() + roleName.slice(1);
}

function formatPermissions(permissions?: Collaborator["permissions"]): string {
  if (!permissions) return "Collaborator";
  if (permissions.admin) return "Admin";
  if (permissions.maintain) return "Maintainer";
  if (permissions.push) return "Write";
  if (permissions.triage) return "Triage";
  if (permissions.pull) return "Read";
  return "Collaborator";
}

// Build social links from user profile
function buildSocialLinks(
  profile: UserProfile,
  githubUrl: string,
): { icon: string; link: string }[] {
  const links: { icon: string; link: string }[] = [
    { icon: "github", link: githubUrl },
  ];

  const addedUrls = new Set<string>([githubUrl]);

  // Add social accounts from GitHub's social_accounts endpoint
  if (profile.social_accounts && profile.social_accounts.length > 0) {
    profile.social_accounts.forEach((account) => {
      if (!addedUrls.has(account.url)) {
        addedUrls.add(account.url);
        links.push({ icon: account.provider, link: account.url });
      }
    });
  }

  // Skip blog/website since Simple Icons doesn't have a generic website icon
  // Only show social accounts that have proper icons from social_accounts endpoint

  // Add Twitter if available from legacy field (in case not in social_accounts)
  if (profile.twitter_username) {
    const twitterUrl = `https://twitter.com/${profile.twitter_username}`;
    if (!addedUrls.has(twitterUrl)) {
      addedUrls.add(twitterUrl);
      links.push({ icon: "twitter", link: twitterUrl });
    }
  }

  return links;
}

// Fetch contributors and collaborators data at build time
export default {
  async load() {
    // Fetch collaborators first
    const rawCollaborators = await fetchCollaborators();

    // Get collaborator usernames for filtering
    const collaboratorUsernames = rawCollaborators.map((collab) => collab.login);

    // Fetch contributors (excluding collaborators)
    const rawContributors = await fetchContributors(collaboratorUsernames);

    // Transform contributors to match VPTeamMembers format
    const contributors = rawContributors.map((contributor) => ({
      avatar: contributor.avatar_url,
      name: contributor.name,
      title: `${contributor.lines} lines, ${contributor.contributions} contributions`,
      links: [{ icon: "github", link: contributor.html_url }],
    }));

    // Fetch user profiles for all collaborators in parallel
    console.log("Fetching user profiles for collaborators...");
    const profilePromises = rawCollaborators.map((collab) =>
      fetchUserProfile(collab.login),
    );
    const profiles = await Promise.all(profilePromises);

    // Transform collaborators to match VPTeamMembers format with social links
    const collaborators = rawCollaborators.map((collaborator, index) => {
      const profile = profiles[index];
      const links = buildSocialLinks(profile, collaborator.html_url);

      // Log discovered social links
      const displayName = profile.name || collaborator.login;
      const socialLinks = links
        .filter((l) => l.icon !== "github")
        .map((l) => l.icon)
        .join(", ");
      if (socialLinks) {
        console.log(
          `  ${displayName} (${collaborator.login}): Found social links (${socialLinks})`,
        );
      }

      return {
        avatar: collaborator.avatar_url,
        name: profile.name || collaborator.login, // Use real name if available, fallback to username
        title:
          formatRole(collaborator.role_name) ||
          formatPermissions(collaborator.permissions),
        links,
      };
    });

    return {
      maintainers: collaborators,
      contributors,
    };
  },
};
