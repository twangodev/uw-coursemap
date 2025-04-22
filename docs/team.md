<script setup>
import { VPTeamMembers } from 'vitepress/theme';
import { useData } from 'vitepress';

// Get the data that was computed at build time
const { frontmatter } = useData();
const { maintainers, contributors } = frontmatter.value.teamData || { maintainers: [], contributors: [] };
</script>

# Meet the Team

## Maintainers

Our maintainers steer the project by triaging issues, reviewing and merging pull requests, and keeping documentation up to date.

<!--suppress CheckEmptyScriptTag, HtmlUnknownTag -->
<VPTeamMembers size="small" :members="maintainers" />

> [!TIP]
> Interested in helping shape the future of this project? Check out our [contributing guide](./contributing.md) to learn how to become a maintainer.

## Contributors


Our contributors power improvements through bug reports, pull requests, documentation updates, and community support—this could be you!

<!--suppress CheckEmptyScriptTag, HtmlUnknownTag -->
<VPTeamMembers size="small" :members="contributors" />

Special shoutout to [Shyam Patel](https://github.com/yamshpatel), [Ali Al Mezel](https://github.com/AliMezel), and [Muakong Yang](https://github.com/Muakongyang) for their contributions for the prototype at Cheesehacks 2024!