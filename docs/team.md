<script setup>
import { VPTeamMembers } from 'vitepress/theme';
import { useData } from 'vitepress';

// Get the data that was computed at build time
const { frontmatter } = useData();
const { maintainers, contributors } = frontmatter.value.teamData || { maintainers: [], contributors: [] };
</script>

# Meet the Team

## Maintainers

<!--suppress CheckEmptyScriptTag, HtmlUnknownTag -->
<VPTeamMembers size="small" :members="maintainers" />

> [!TIP]
> Interested in helping shape the future of this project? Check out our [contributing guide](./contributing.md) to learn how to become a maintainer.

## Contributions

![Alt](https://repobeats.axiom.co/api/embed/6cef9c41661d58138630347f2b67a57c7872fe3a.svg "Repobeats analytics image")

<!--suppress CheckEmptyScriptTag, HtmlUnknownTag -->
<VPTeamMembers size="small" :members="contributors" />

Special shoutout to [Shyam Patel](https://github.com/yamshpatel), [Ali Al Mezel](https://github.com/AliMezel), and [Muakong Yang](https://github.com/Muakongyang) for their contributions for the prototype at Cheesehacks 2024!
