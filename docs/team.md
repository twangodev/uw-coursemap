<script setup>
import { VPTeamMembers } from 'vitepress/theme';

const members = [
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
    title: 'Developer',
    links: [
      { icon: 'github', link: 'https://github.com/ProfessorAtomicManiac' },
    ]
  },
{
    avatar: 'https://www.github.com/theradest1.png',
    name: 'Landon Bakken',
    title: 'Developer',
    links: [
      { icon: 'github', link: 'https://github.com/theradest1' },
    ]
  },
];
</script>

# Meet the Team

## Development Team

We're a group of students maintaining this project. Say hello to us!

<!--suppress CheckEmptyScriptTag, HtmlUnknownTag -->
<VPTeamMembers size="small" :members />

::: tip
If you are interested in joining the team and becoming a maintainer, please check out our [contributing guide](./contributing.md) for more information on how to get involved.
:::

## Hackathon Contributors

Special shoutout to [Shyam Patel](https://github.com/yamshpatel), [Ali Al Mezel](https://github.com/AliMezel), and [Muakong Yang](https://github.com/Muakongyang) for their contributions for the prototype at Cheesehacks 2024!