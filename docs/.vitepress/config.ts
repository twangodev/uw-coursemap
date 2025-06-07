import { type UserConfig} from 'vitepress'
import {groupIconMdPlugin, groupIconVitePlugin} from 'vitepress-plugin-group-icons';
import {withMermaid} from "vitepress-plugin-mermaid";
import teamData from './contributors';

const vitePressOptions: UserConfig = {
  lang: 'en-US',
  title: "uw-coursemap",
  description: "Explore the courses offered by the UW-Madison in a visual and interactive way.",
  async buildEnd() {
    console.log('Build completed. GitHub API calls were made only during build time.');
  },
  async transformPageData(pageData) {
    // Only load the data once during build time
    if (pageData.relativePath === 'team.md') {
      const data = await teamData.load();
      pageData.frontmatter.teamData = data;
    }
    return pageData;
  },
  themeConfig: {
    logo: 'https://uwcourses.com/uw-coursemap-logo.svg',
    siteTitle: 'UW Course Map',
    // https://vitepress.dev/reference/default-theme-config
    nav: [
      {
        text: 'Home',
        link: '/'
      },
      {
        text: 'About',
        link: '/about'
      },
      {
        text: 'Live',
        link: 'https://uwcourses.com'
      },
    ],
    sidebar: [
      {
        text: 'Getting Started',
        items: [
          {
            text: 'About',
            link: '/about'
          },
          {
            text: 'Quickstart',
            link: '/getting-started/quickstart'
          },
          {
            text: 'Architecture',
            link: '/getting-started/architecture'
          }
        ]
      },
      {
        text: 'Usage',
        items: [
          {
            text: 'Content API Specification',
            link: '/usage/static-api',
          },
          {

          }
        ]
      },
      {
        text: 'Codebase',
        items: [
          {
            text: 'Frontend',
            link: '/codebase/frontend'
          },
          {
            text: 'Search',
            link: '/codebase/search'
          },
          {
            text: 'Generation',
            link: '/codebase/generation'
          }
        ]
      },
      {
        text: 'Contributing',
        link: '/contributing'
      },
      {
        text: 'Code of Conduct',
        link: '/code-of-conduct'
      },
      {
        text: 'Team',
        link: '/team'
      },
      {
        text: 'Branding',
        link: '/branding'
      },
    ],
    search: {
      provider: 'local'
    },
    socialLinks: [
      {
        icon: 'github',
        link: 'https://github.com/twangodev/uw-coursemap'
      }
    ],
    outline: {
      level: [2, 3],
    },
    editLink: {
      pattern: 'https://github.com/twangodev/uw-coursemap/edit/main/docs/:path',
      text: 'Edit this page on GitHub'
    },
    footer: {
      message: "UW Course Map is not affiliated with the University of Wisconsin-Madison.",
      copyright: `&copy; ${new Date().getFullYear()} James Ding`
    }
  },
  lastUpdated: true,
  sitemap: {
    hostname: 'https://docs.uwcourses.com'
  },
  head: [
    ['script', {
      src: 'https://rybbit.twango.dev/api/script.js',
      defer: '',
      'data-site-id': '2'
    }],
    ['link', {
      href: "https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.7.2/css/all.min.css",
      rel: "stylesheet"
    }]
  ],
  markdown: {
    config(md) {
      md.use(groupIconMdPlugin)
    },
    lineNumbers: true,
    image: {
      lazyLoading: true
    },
    math: true,
  },
  vite: {
    plugins: [
        groupIconVitePlugin({
          customIcon: {
            'docker': 'vscode-icons:file-type-docker',
            'git': 'vscode-icons:file-type-git',
            'sh': 'vscode-icons:file-type-shell',
            'pip': 'vscode-icons:file-type-python',
            'pipenv': 'vscode-icons:file-type-python',
          }
        }) as any,
    ],
  }
}

export default withMermaid(vitePressOptions)
